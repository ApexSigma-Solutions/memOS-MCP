# Database Configuration

The MemOS FastMCP server supports multiple database backends. This document provides a comparison of the supported backends and instructions for migrating between them.

## Supported Backends

| Backend    | Use Case              | Pros                               | Cons                                       |
|------------|-----------------------|------------------------------------|--------------------------------------------|
| SQLite     | Local Development     | Lightweight, easy to set up        | Not suitable for production, single-user   |
| PostgreSQL | Production            | Scalable, reliable, full-featured  | Requires a separate server, more complex   |
| Neo4j      | Graph-based Memory    | Advanced graph query capabilities  | Requires a separate server, niche use case |

## Migration Guides

### SQLite to PostgreSQL

1.  **Dump the SQLite database:**
    ```bash
    sqlite3 /data/sqlite/memory.db .dump > dump.sql
    ```

2.  **Convert the SQL dump to PostgreSQL format.** This may require a script or manual editing.

3.  **Import the converted SQL dump into PostgreSQL:**
    ```bash
    psql -h postgres -U memos_user -d memos < dump.sql
    ```

## Performance Tuning

### PostgreSQL

- **Connection Pooling:** The server uses SQLAlchemy's connection pooling to manage database connections. You can configure the pool size in the `PostgresDatabase` class.
- **Indexing:** The database schema includes indexes on the primary keys. You may want to add additional indexes to improve query performance.

## Backup and Restore

### PostgreSQL

- **Backup:**
  ```bash
  pg_dump -h postgres -U memos_user -d memos > backup.sql
  ```

- **Restore:**
  ```bash
  psql -h postgres -U memos_user -d memos < backup.sql
  ```
