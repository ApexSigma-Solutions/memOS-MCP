# memos.MCP

The **Conceptual Bridge** between the OmegaKG Brain and the IDE Hands.

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for full system model.

```
       All Sources → InGest-LLM (single digestor)
                           ↓
              PostgreSQL + Neo4j (persistent brain)
                     ↙         ↘
            memOS.MCP            OmegaVault
               ↓                    ↓
              IDE               Linear/GitHub
```

## Features

### 🧠 Context Retrieval (Brain → Hands)
- **`retrieve_context`**: Semantic search from PGVector
- **`get_concepts`**: Traversal of Neo4j knowledge graph
- **`get_constraints`**: Rule enforcement from Mimir

### 🤲 Working Memory (Hands)
- **Redis Integration**: Fast, ephemeral storage
- **Scratchpad**: Trace reasoning steps (`scratch_write`/`read`)
- **Session Context**: Manage working state (`set`/`get_working_memory`)

### 🎓 Learning (Hands → Brain)
- **`mark_significant`**: Flag experiences for promotion
- **`promote_memory`**: Send to InGest-LLM for permanent storage
- **Auto-promotion**: Significance threshold triggers automatic ingestion

## Quick Start

```powershell
# Install dependencies
cd memos.MCP
poetry install

# Set environment variables
# Copy .env.example to .env and configure:
# - POSTGRES_* (Storage)
# - NEO4J_* (Graph)
# - REDIS_* (Working Memory)
# - INGEST_LLM_URL (Learning)

# Start MCP server
fastmcp run src/memos_mcp/server.py
```

## Tools

| Tool | Category | Usage |
|------|----------|-------|
| `retrieve_context` | Query | `retrieve_context(query="auth flow", limit=5)` |
| `get_concepts` | Query | `get_concepts(concept_id="UserAuth", depth=2)` |
| `scratch_write` | Memory | `scratch_write(content="Planning schema...")` |
| `promote_memory` | Learn | `promote_memory(memory_id="123")` |

## Components

- **FastMCP**: Server framework
- **PGVectorStore**: Async vector retrieval
- **RedisMemoryClient**: Ephemeral storage manager
- **Logic Layer**: Integrates databases and enforces constraints

## Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md) - System Design
- [BUILD.md](BUILD.md) - Build Guide
