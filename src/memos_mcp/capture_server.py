"""
Ephemeral Capture Server for AI Conversation Persistence.

This server provides a localhost webhook endpoint for browser extensions
to capture AI conversations from Claude.ai, ChatGPT, and other LLM interfaces.

Features:
- /capture endpoint accepting POST requests with conversation data
- CORS support for browser extension origins
- Write conversations to Obsidian vault as markdown
- Health check and statistics endpoints

Run with: poetry run python -m memos_mcp.capture_server
"""

import asyncio
import json
import logging
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

from .config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# =============================================================================
# MODELS
# =============================================================================

class Message(BaseModel):
    """A single message in a conversation."""
    role: str  # "user", "assistant", "system"
    content: str
    timestamp: Optional[str] = None


class ConversationCapture(BaseModel):
    """Incoming conversation capture request."""
    source: str = Field(..., description="Source platform (claude.ai, chatgpt, etc)")
    conversation_id: Optional[str] = Field(None, description="Platform's conversation ID")
    title: Optional[str] = Field(None, description="Conversation title")
    messages: List[Message] = Field(..., description="List of messages")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    captured_at: Optional[str] = None


class CaptureResponse(BaseModel):
    """Response from capture endpoint."""
    status: str
    conversation_id: str
    file_path: Optional[str] = None
    message: str


# =============================================================================
# APPLICATION
# =============================================================================

app = FastAPI(
    title="memos.MCP Capture Server",
    description="Ephemeral capture server for AI conversation persistence",
    version="1.0.0",
)

# CORS configuration - allow browser extensions from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for browser extension compatibility
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Statistics tracking
stats = {
    "total_captures": 0,
    "captures_by_source": {},
    "last_capture_at": None,
    "errors": 0,
    "started_at": datetime.now(timezone.utc).isoformat(),
}


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def sanitize_filename(name: str) -> str:
    """Sanitize a string for use as a filename."""
    # Remove or replace invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '', name)
    sanitized = sanitized.strip()
    # Limit length
    if len(sanitized) > 100:
        sanitized = sanitized[:97] + "..."
    return sanitized or "untitled"


def format_conversation_markdown(capture: ConversationCapture) -> str:
    """
    Format a conversation as Obsidian-compatible markdown.
    
    Creates a document with YAML frontmatter and formatted messages.
    """
    now = datetime.now(timezone.utc)
    captured_at = capture.captured_at or now.isoformat()
    
    # Build frontmatter
    frontmatter = {
        "created": now.strftime("%Y-%m-%d %H:%M:%S%z"),
        "source": capture.source,
        "conversation_id": capture.conversation_id or str(uuid4()),
        "title": capture.title or "Untitled Conversation",
        "message_count": len(capture.messages),
        "tags": ["ai-conversation", f"source/{capture.source}"],
    }
    
    if capture.metadata:
        frontmatter["metadata"] = capture.metadata
    
    # Build markdown content
    lines = ["---"]
    for key, value in frontmatter.items():
        if isinstance(value, list):
            lines.append(f"{key}:")
            for item in value:
                lines.append(f"  - {item}")
        elif isinstance(value, dict):
            lines.append(f"{key}:")
            for k, v in value.items():
                lines.append(f"  {k}: {v}")
        else:
            lines.append(f"{key}: {value}")
    lines.append("---")
    lines.append("")
    
    # Title
    title = capture.title or "AI Conversation"
    lines.append(f"# {title}")
    lines.append("")
    lines.append(f"*Captured from {capture.source} at {captured_at}*")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # Messages
    for i, msg in enumerate(capture.messages, 1):
        role_emoji = {
            "user": "👤",
            "assistant": "🤖",
            "system": "⚙️",
        }.get(msg.role, "💬")
        
        role_name = msg.role.capitalize()
        
        lines.append(f"## {role_emoji} {role_name}")
        lines.append("")
        lines.append(msg.content)
        lines.append("")
        
        if msg.timestamp:
            lines.append(f"*{msg.timestamp}*")
            lines.append("")
    
    return "\n".join(lines)


def detect_query_type(messages: List[Message]) -> str:
    """
    Detect the type of conversation based on content analysis.
    
    Returns one of: code, research, creative, general
    """
    all_content = " ".join(m.content.lower() for m in messages)
    
    # Code indicators
    code_patterns = ["```", "function", "class ", "def ", "import ", "const ", "let ", "var "]
    code_score = sum(1 for p in code_patterns if p in all_content)
    
    # Research indicators  
    research_patterns = ["research", "explain", "what is", "how does", "why", "documentation"]
    research_score = sum(1 for p in research_patterns if p in all_content)
    
    # Creative indicators
    creative_patterns = ["write", "story", "poem", "creative", "imagine", "design"]
    creative_score = sum(1 for p in creative_patterns if p in all_content)
    
    scores = {
        "code": code_score,
        "research": research_score,
        "creative": creative_score,
    }
    
    max_type = max(scores, key=scores.get)
    if scores[max_type] >= 2:
        return max_type
    return "general"


def get_obsidian_vault_path() -> Path:
    """Get the Obsidian vault path from settings or environment."""
    vault_path = os.environ.get("OBSIDIAN_VAULT_PATH", "./vault")
    return Path(vault_path)


async def write_to_obsidian(capture: ConversationCapture) -> str:
    """
    Write a conversation to the Obsidian vault.
    
    Returns the relative path to the created file.
    """
    vault_path = get_obsidian_vault_path()
    
    # Create conversations directory if needed
    conversations_dir = vault_path / "Conversations"
    conversations_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate filename
    now = datetime.now()
    title = sanitize_filename(capture.title or "Untitled")
    filename = f"{now.strftime('%Y-%m-%d_%H%M')}_{title}.md"
    
    file_path = conversations_dir / filename
    
    # Format and write
    markdown = format_conversation_markdown(capture)
    
    # Use sync write wrapped in thread for I/O
    file_path.write_text(markdown, encoding="utf-8")
    
    logger.info(f"Wrote conversation to {file_path}")
    
    return str(file_path.relative_to(vault_path))


# =============================================================================
# ENDPOINTS
# =============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "memos.MCP Capture Server",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/stats")
async def get_stats():
    """Get capture statistics."""
    return stats


@app.post("/capture", response_model=CaptureResponse)
async def capture_conversation(capture: ConversationCapture, request: Request):
    """
    Capture an AI conversation.
    
    This endpoint receives conversation data from browser extensions and:
    1. Validates the payload
    2. Writes to Obsidian vault as markdown
    3. Updates statistics
    
    Future: Queue for percolation to Neo4j graph.
    """
    try:
        # Generate conversation ID if not provided
        conv_id = capture.conversation_id or str(uuid4())
        
        # Detect query type
        query_type = detect_query_type(capture.messages)
        capture.metadata = capture.metadata or {}
        capture.metadata["query_type"] = query_type
        
        # Write to Obsidian
        file_path = await write_to_obsidian(capture)
        
        # Update statistics
        stats["total_captures"] += 1
        stats["captures_by_source"][capture.source] = (
            stats["captures_by_source"].get(capture.source, 0) + 1
        )
        stats["last_capture_at"] = datetime.now(timezone.utc).isoformat()
        
        logger.info(
            f"Captured conversation {conv_id} from {capture.source} "
            f"({len(capture.messages)} messages, type: {query_type})"
        )
        
        return CaptureResponse(
            status="success",
            conversation_id=conv_id,
            file_path=file_path,
            message=f"Captured {len(capture.messages)} messages to {file_path}",
        )
        
    except Exception as e:
        stats["errors"] += 1
        logger.error(f"Capture failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/capture/batch")
async def capture_batch(captures: List[ConversationCapture]):
    """Capture multiple conversations in a batch."""
    results = []
    for capture in captures:
        try:
            response = await capture_conversation(capture, None)
            results.append({"status": "success", "id": response.conversation_id})
        except Exception as e:
            results.append({"status": "error", "error": str(e)})
    
    return {
        "processed": len(captures),
        "successful": sum(1 for r in results if r["status"] == "success"),
        "results": results,
    }


# =============================================================================
# MAIN
# =============================================================================

def run_server(host: str = "127.0.0.1", port: int = 8765):
    """Run the capture server."""
    logger.info(f"Starting memos.MCP Capture Server on {host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    run_server()
