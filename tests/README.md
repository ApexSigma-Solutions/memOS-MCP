# Running Tests for memos-mcp

This directory contains comprehensive unit tests for the memos-mcp project.

## Quick Start

```bash
# Run all tests
python -m pytest

# Run with verbose output
python -m pytest -v

# Run specific test file
python -m pytest tests/test_config.py
```

## Test Organization

- `conftest.py` - Shared fixtures and configuration
- `test_*.py` - Module-specific tests
- `database/` - Database implementation tests

## Test Fixtures

Common fixtures available in conftest.py:
- `temp_db_path` - Temporary database file path
- `sqlite_db` - Initialized SQLite database
- `mock_settings` - Mocked configuration
- `sample_memory_data` - Sample memory data
- `sample_tool_data` - Sample tool data

## Coverage

Tests cover all new and modified files:
- Configuration (src/memos_mcp/config.py)
- Models (src/memos_mcp/models.py)
- Schemas (src/memos_mcp/schemas.py)
- Database abstraction (src/memos_mcp/database/base.py)
- SQLite implementation (src/memos_mcp/database/sqlite.py)
- PostgreSQL implementation (src/memos_mcp/database/postgres.py)
- Neo4j stub (src/memos_mcp/database/neo4j.py)
- Database factory (src/memos_mcp/database/__init__.py)
- Business logic (src/memos_mcp/logic.py)
- Server setup (src/memos_mcp/server.py)

For detailed coverage information, see TEST_COVERAGE.md