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
    """
    Create and provide a temporary file path for a SQLite database.
    
    Yields:
        The filesystem path to a temporary `.db` file. The file is removed after the generator completes.
    """
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name
    yield db_path
    # Cleanup
    if os.path.exists(db_path):
        os.remove(db_path)


@pytest.fixture(scope="function")
def sqlite_db(temp_db_path):
    """
    Provide a SQLiteDatabase instance backed by a temporary file for tests.
    
    On teardown, removes the temporary database file if it exists.
    
    Parameters:
        temp_db_path (str): Path to the temporary SQLite database file to use for the instance.
    
    Returns:
        db (SQLiteDatabase): A SQLiteDatabase instance connected to the provided temporary path.
    """
    from memos_mcp.database.sqlite import SQLiteDatabase
    db = SQLiteDatabase(db_path=temp_db_path)
    yield db
    # Cleanup
    if os.path.exists(temp_db_path):
        os.remove(temp_db_path)


@pytest.fixture(scope="function")
def mock_postgres_engine():
    """
    Provide a MagicMock that simulates a PostgreSQL engine for tests.
    
    Returns:
        mock_engine (MagicMock): A mock engine whose `connect()` method returns a mock session object.
    """
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
    """
    Create a mock Redis client configured for tests.
    
    Returns:
        MagicMock: A mock Redis client where `ping()` returns `True` and `get()` returns `None`.
    """
    mock_client = MagicMock()
    mock_client.ping.return_value = True
    mock_client.get.return_value = None
    return mock_client


@pytest.fixture
def sample_memory_data():
    """
    Provide a sample memory data dictionary used in tests.
    
    Returns:
        sample (dict): A dictionary with keys:
            - `content` (str): The memory text content.
            - `agent_id` (str): Identifier of the agent associated with the memory.
            - `metadata` (dict): Additional metadata with `source` (str) and `type` (str).
    """
    return {
        "content": "Test memory content",
        "agent_id": "test_agent",
        "metadata": {"source": "test", "type": "episodic"},
    }


@pytest.fixture
def sample_tool_data():
    """
    Provide a sample tool data dictionary for tests.
    
    Returns:
        dict: A dictionary with the following keys:
            - name (str): Tool name.
            - description (str): Short description of the tool.
            - usage (str): Usage instructions or notes.
            - tags (list[str]): List of tag strings categorizing the tool.
    """
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
    """
    Create and apply a test Settings instance and patch memos_mcp.config.settings to use it.
    
    This fixture creates a temporary SQLite database file, constructs a Settings object configured for tests (SQLite backend, temporary db path, and example Postgres connection values), and uses the provided monkeypatch to replace memos_mcp.config.settings with that Settings instance.
    
    Returns:
        Settings: The constructed Settings instance used for testing.
    """
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