"""Pytest configuration and fixtures for memos-mcp tests."""
import os
import tempfile
import uuid
from typing import Generator
import pytest
from unittest.mock import Mock, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Set testing environment variable
os.environ["TESTING"] = "1"

@pytest.fixture(scope="function")
def temp_db_path() -> Generator[str, None, None]:
    """Create a temporary database file path."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name
    yield db_path
    # Cleanup
    if os.path.exists(db_path):
        os.remove(db_path)


@pytest.fixture(scope="function")
def sqlite_db(temp_db_path):
    """Create a SQLite database instance for testing."""
    from memos_mcp.database.sqlite import SQLiteDatabase
    db = SQLiteDatabase(db_path=temp_db_path)
    yield db
    # Cleanup
    if os.path.exists(temp_db_path):
        os.remove(temp_db_path)


@pytest.fixture(scope="function")
def mock_postgres_engine():
    """Mock PostgreSQL engine for testing."""
    mock_engine = MagicMock()
    mock_session = MagicMock()
    mock_engine.connect.return_value = mock_session
    return mock_engine


@pytest.fixture(scope="function")
def mock_qdrant_client():
    """Mock Qdrant client for testing."""
    mock_client = MagicMock()
    mock_client.get_collections.return_value = MagicMock(collections=[])
    return mock_client


@pytest.fixture(scope="function")
def mock_redis_client():
    """Mock Redis client for testing."""
    mock_client = MagicMock()
    mock_client.ping.return_value = True
    mock_client.get.return_value = None
    return mock_client


@pytest.fixture
def sample_memory_data():
    """Sample memory data for testing."""
    return {
        "content": "Test memory content",
        "agent_id": "test_agent",
        "metadata": {"source": "test", "type": "episodic"},
    }


@pytest.fixture
def sample_tool_data():
    """Sample tool data for testing."""
    return {
        "name": "test_tool",
        "description": "A test tool for unit testing",
        "usage": "Use this tool for testing purposes",
        "tags": ["test", "development"],
    }


@pytest.fixture(autouse=True)
def reset_database_singleton():
    """Reset database singleton between tests."""
    import memos_mcp.database
    memos_mcp.database._db_instance = None
    yield
    memos_mcp.database._db_instance = None


@pytest.fixture
def mock_settings(monkeypatch):
    """Mock settings for testing."""
    from memos_mcp.config import Settings

    tmp_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    db_path = tmp_file.name
    tmp_file.close()
    password = uuid.uuid4().hex

    mock_settings = Settings(
        memos_db_type="sqlite",
        memos_db_path=db_path,
        postgres_host="localhost",
        postgres_port=5432,
        postgres_db="test_db",
        postgres_user="test_user",
        postgres_password=password,
    )

    monkeypatch.setattr("memos_mcp.config.settings", mock_settings)
    return mock_settings