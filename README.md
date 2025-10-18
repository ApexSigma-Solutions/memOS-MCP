# MemOS FastMCP Server

This repository contains the MemOS cognitive core service, refactored into a lightweight, portable FastMCP server. It provides persistent memory and tool awareness to AI agents, is containerized with Docker, and supports multiple database backends.

## Project Overview

The MemOS FastMCP server is designed to be a flexible and scalable solution for providing cognitive capabilities to AI agents. It exposes memory operations as MCP resources and tools, allowing agents to store memories, retrieve context, and register their own tools.

### Architecture Diagram

```
[Agent] -> [FastMCP Server] -> [Database Abstraction Layer] -> [SQLite | PostgreSQL | Neo4j]
                                       |
                                       -> [Qdrant] for vector search
```

## Quick Start (Local Development)

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/memos.as.git
    cd memos.as
    ```

2.  **Install dependencies:**
    ```bash
    pip install -e .
    ```

3.  **Run the server:**
    ```bash
    python src/memos_mcp/server.py
    ```

## Docker Deployment

The server can be easily deployed using Docker and Docker Compose.

1.  **Build the Docker image:**
    ```bash
    docker-compose -f docker/docker-compose.yml build
    ```

2.  **Run the server:**
    ```bash
    docker-compose -f docker/docker-compose.yml up
    ```

## Database Configuration

The server supports SQLite, PostgreSQL, and Neo4j as database backends. The database can be configured using environment variables.

### SQLite (default)

```bash
MEMOS_DB_TYPE=sqlite
MEMOS_DB_PATH=/data/sqlite/memory.db
```

### PostgreSQL

```bash
MEMOS_DB_TYPE=postgres
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=memos
POSTGRES_USER=memos_user
POSTGRES_PASSWORD=secure_password
```

### Neo4j

```bash
MEMOS_DB_TYPE=neo4j
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=neo4j_password
```

## Environment Variable Reference

See the `.env.example` file for a full list of environment variables.
