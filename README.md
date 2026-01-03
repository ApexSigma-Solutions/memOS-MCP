# memos.MCP

A FastMCP server providing memory management and context bridge capabilities for the OmegaKG ecosystem.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Browser Extension                         │
│                 (Claude.ai, ChatGPT, etc.)                   │
└─────────────────────┬───────────────────────────────────────┘
                      │ POST /capture
                      ▼
┌─────────────────────────────────────────────────────────────┐
│              Capture Server (port 8765)                      │
│  ├─ /capture     - Receive conversations                    │
│  ├─ /health      - Health check                              │
│  └─ /stats       - Capture statistics                        │
└─────────────────────┬───────────────────────────────────────┘
                      │
         ┌────────────┴────────────┐
         ▼                         ▼
┌─────────────────┐     ┌─────────────────────────┐
│  Obsidian Vault │     │   Percolation Scheduler │
│  (Markdown)     │◄────┤   (5-min batch)         │
└─────────────────┘     └───────────┬─────────────┘
                                    ▼
     ┌────────────────────────────────────────────┐
     │              PostgreSQL (port 5800)         │
     │  ├─ memos.memories     (vector(1024))      │
     │  └─ memos.memory_audit (audit log)         │
     └────────────────────────────────────────────┘
```

## Quick Start

```powershell
# Install dependencies
cd memos.MCP
poetry install

# Set environment variables (copy .env.example to .env)
$env:POSTGRES_PASSWORD = "omega_dev_password"
$env:OBSIDIAN_VAULT_PATH = "D:\path\to\vault"

# Start capture server
.\scripts\start-capture-server.ps1
```

## Features

- **Memory Storage**: Store and retrieve memory fragments with tags
- **Vector Search**: Semantic search across memories using PostgreSQL pgvector
- **Capture Server**: Localhost webhook for browser extension integration
- **Obsidian Integration**: Write conversations as markdown with frontmatter
- **Percolation Scheduler**: Batch processing to Neo4j knowledge graph

## Components

### PGVectorStore
PostgreSQL-based vector storage using pgvector extension:
- Async connection pooling via asyncpg
- 1024-dimension vector embeddings
- Cosine similarity search
- Full audit logging

### Capture Server
FastAPI server for conversation capture:
- CORS support for browser extensions
- Markdown output with YAML frontmatter
- Query type detection (code, research, creative)
- Statistics tracking

### Percolation Scheduler
Background scheduler for Neo4j integration:
- 5-minute batch processing intervals
- Automatic frontmatter parsing
- Duplicate file detection

## Documentation

- [Capture Server Setup](docs/capture-server-setup.md)
- [BUILD.md](BUILD.md) - Build & Run Guide
- [FastMCP Configuration](fastmcp.json) - MCP server settings

## Database Schema

```sql
-- memos.memories table
CREATE TABLE memos.memories (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    agent_id VARCHAR(255),
    memory_metadata JSONB,
    embedding VECTOR(1024),
    embedding_model VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    tags TEXT[]
);

-- IVFFLAT index for fast similarity search
CREATE INDEX idx_memories_embedding ON memos.memories 
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

## Version

v0.1.0-pgvector - PG Vector Migration Complete
