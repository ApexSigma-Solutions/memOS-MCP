# memos.MCP Capture Server Setup

This guide explains how to set up and run the ephemeral capture server for AI conversation persistence.

## Overview

The capture server provides a localhost webhook endpoint for browser extensions to capture AI conversations from Claude.ai, ChatGPT, and other LLM interfaces. Captured conversations are saved to your Obsidian vault and can be percolated to Neo4j for knowledge graph integration.

## Prerequisites

- Python 3.12+
- Poetry installed
- PostgreSQL with pgvector extension (for memory storage)
- Obsidian vault configured

## Installation

```powershell
cd d:\projects\OmegaKG\memos.MCP

# Install dependencies
poetry install

# Set required environment variables
# Copy .env.example to .env and configure:
cp .env.example .env
```

## Configuration

### Required Environment Variables

```env
# PostgreSQL (shared with Omega_KG_stable)
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5800
POSTGRES_DB=omega_kg_stable
POSTGRES_USER=omega_user
POSTGRES_PASSWORD=omega_dev_password
POSTGRES_SCHEMA=memos

# Obsidian vault path
OBSIDIAN_VAULT_PATH=D:\path\to\your\vault
```

## Starting the Server

### Option 1: PowerShell Script

```powershell
.\scripts\start-capture-server.ps1
```

### Option 2: Background Mode

```powershell
.\scripts\start-capture-server.ps1 -Background
```

### Option 3: Direct Python

```powershell
poetry run python -c "from memos_mcp.capture_server import run_server; run_server()"
```

The server runs on `http://localhost:8765` by default.

## API Endpoints

### Health Check

```http
GET /health
```

Returns server status and version.

### Capture Statistics

```http
GET /stats
```

Returns capture statistics (total captures, by source, errors).

### Capture Conversation

```http
POST /capture
Content-Type: application/json

{
  "source": "claude.ai",
  "title": "Optional conversation title",
  "conversation_id": "optional-external-id",
  "messages": [
    {"role": "user", "content": "Hello, how are you?"},
    {"role": "assistant", "content": "I'm doing well, thank you!"}
  ],
  "metadata": {}
}
```

Returns:
```json
{
  "status": "success",
  "conversation_id": "uuid",
  "file_path": "Conversations/2026-01-03_1745_conversation.md",
  "message": "Captured 2 messages to Conversations/..."
}
```

## Browser Extension Integration

The capture server supports CORS from any origin, making it compatible with browser extensions. Configure your extension to POST to:

```
http://localhost:8765/capture
```

### Example Chrome Extension Manifest Permissions

```json
{
  "permissions": [
    "activeTab",
    "storage"
  ],
  "host_permissions": [
    "http://localhost:8765/*"
  ]
}
```

## Output Format

Conversations are saved as Obsidian-compatible markdown with YAML frontmatter:

```markdown
---
created: 2026-01-03 17:45:00+0000
source: claude.ai
conversation_id: abc123
title: My Conversation
message_count: 5
tags:
  - ai-conversation
  - source/claude.ai
---

# My Conversation

*Captured from claude.ai at 2026-01-03T17:45:00Z*

---

## 👤 User

Your message here...

## 🤖 Assistant

AI response here...
```

## Percolation to Neo4j

Captured conversations can be percolated to Neo4j for knowledge graph integration. The percolation scheduler runs every 5 minutes and processes new conversation files.

To start with percolation:

```python
from memos_mcp.percolation import start_scheduler
import asyncio

asyncio.run(start_scheduler())
```

## Troubleshooting

### Server won't start

1. Check that port 8765 is not in use
2. Verify OBSIDIAN_VAULT_PATH is accessible
3. Check logs for specific errors

### Capture fails

1. Verify the JSON payload format
2. Check that messages array is not empty
3. Ensure CORS is not blocked by other middleware

### Files not appearing in Obsidian

1. Verify OBSIDIAN_VAULT_PATH is correct
2. Check that the Conversations directory exists
3. Wait for Obsidian to sync/detect new files
