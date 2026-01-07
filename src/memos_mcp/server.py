"""
memOS MCP Server Entrypoint
Integrates local tools and the Omega Intelligence Layer.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastmcp import FastMCP

# Import Configuration
from memos_mcp.config import Settings

# Import Core Logic
from memos_mcp.logic import MemosLogic

# Import Tools (The Mirmir Bridge)
# Import Tools
from memos_mcp.tools.intelligence import consult_mirmir, verify_implementation
from memos_mcp.tools.context import retrieve_context, get_concepts, get_constraints
from memos_mcp.tools.memory import (
    scratch_write,
    scratch_read,
    scratch_clear,
    set_working_memory,
    get_working_memory,
    mark_significant,
    promote_memory,
)

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("memos_mcp")

# Global Logic Instance
logic_instance: MemosLogic = None


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[None]:
    """
    Manages the lifecycle of the memOS server.
    Initializes database connections on startup.
    """
    global logic_instance
    logger.info("🚀 Starting memOS MCP Server (Port 8768)...")

    settings = Settings()

    try:
        # Initialize Core Logic (Database, Vector Store, etc.)
        logic_instance = MemosLogic(settings)
        await logic_instance.initialize()
        logger.info("✅ memOS Logic Layer Initialized.")

        yield

    except Exception as e:
        logger.error(f"❌ Critical Startup Failure: {e}")
        raise
    finally:
        logger.info("🛑 Shutting down memOS MCP Server...")
        if logic_instance:
            await logic_instance.shutdown()


# Initialize FastMCP
mcp_server = FastMCP(
    "memOS", lifespan=lifespan, dependencies=["neo4j", "pydantic", "redis"]
)

# Export app for uvicorn compatibility
# Export app for uvicorn compatibility
app = mcp_server

# --- CORS Middleware ---
from fastapi.middleware.cors import CORSMiddleware

try:
    # Attempt to add middleware (FastMCP should expose Starlette/FastAPI interface)
    mcp_server.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
except AttributeError:
    logger.warning(
        "Could not add CORS middleware to FastMCP instance - check FastMCP version"
    )

# --- REGISTER TOOLS ---

# 1. Intelligence Layer (The Brain)
mcp_server.add_tool(consult_mirmir)
mcp_server.add_tool(verify_implementation)

# 2. Context Retrieval (Queries)
mcp_server.add_tool(retrieve_context)
mcp_server.add_tool(get_concepts)
mcp_server.add_tool(get_constraints)

# 3. Working Memory (Hands)
mcp_server.add_tool(scratch_write)
mcp_server.add_tool(scratch_read)
mcp_server.add_tool(scratch_clear)
mcp_server.add_tool(set_working_memory)
mcp_server.add_tool(get_working_memory)

# 4. Learning (Hands -> Brain)
mcp_server.add_tool(mark_significant)
mcp_server.add_tool(promote_memory)


@mcp_server.resource("config://status")
def get_system_status() -> str:
    """Returns the health status of the memOS ecosystem."""
    status = "ONLINE" if logic_instance else "INITIALIZING"
    return f"memOS Status: {status}\nIntelligence Layer: ACTIVE (Mirmir Connected)"


# HTTP Endpoints removed as FastMCP does not support arbitrary HTTP routes directly.
# Use MCP tools instead.

if __name__ == "__main__":
    import sys
    import subprocess
    from pathlib import Path
    import uvicorn
    from fastapi import FastAPI

    # Run Documentation Enforcement (The Immune System)
    try:
        # Locate script relative to this file
        current_dir = Path(__file__).resolve().parent
        script_path = (
            current_dir.parent.parent / "scripts" / "maintenance" / "enforce_docs.py"
        )

        if script_path.exists():
            logger.info("🛡️ Running Mimir Documentation Enforcement...")
            # Use same python executable
            subprocess.run(
                [sys.executable, str(script_path)], check=True, capture_output=True
            )
            logger.info("✅ Mimir Documentation Verified.")
        else:
            logger.warning(f"⚠️ Docs script not found at {script_path}")

    except Exception as e:
        logger.error(f"⚠️ Documentation enforcement failed (Soft Fail): {e}")

    # Check for SSE mode flag
    if "--sse" in sys.argv:
        logger.info("Starting in SSE mode with Health Check...")

        # 1. Get the Starlette app from FastMCP
        request_app = mcp_server.sse_app()

        # 2. Create a wrapper FastAPI app
        wrapper_app = FastAPI()

        # 3. Add CORS Middleware (Required for Dashboard)
        from fastapi.middleware.cors import CORSMiddleware

        wrapper_app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Allow all origins for dev environment
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # 4. Add Health Check (Required for Dashboard)
        @wrapper_app.get("/health")
        async def health_check():
            return {"status": "healthy", "service": "memOS.MCP"}

        # 5. Mount the SSE app
        # We mount at root so /sse and /messages work as expected
        wrapper_app.mount("/", request_app)

        # 6. Run with Uvicorn
        uvicorn.run(wrapper_app, host="0.0.0.0", port=8768)

    else:
        # Start stdio server (default for Claude Desktop and local MCP clients)
        mcp_server.run()
