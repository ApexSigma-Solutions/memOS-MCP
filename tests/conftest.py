"""Pytest configuration and shared fixtures for memos_mcp tests."""
import os
import pytest
import tempfile


@pytest.fixture
def temp_db_path():
    """Provide a temporary database file path."""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_file.close()
    yield temp_file.name
    if os.path.exists(temp_file.name):
        os.unlink(temp_file.name)


@pytest.fixture
def temp_dir():
    """Provide a temporary directory."""
    temp_directory = tempfile.mkdtemp()
    yield temp_directory
    import shutil
    if os.path.exists(temp_directory):
        shutil.rmtree(temp_directory)


@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset singleton instances between tests."""
    import memos_mcp.database
    memos_mcp.database._db_instance = None
    yield
    memos_mcp.database._db_instance = None


@pytest.fixture
def sample_memory_data():
    """Provide sample memory data for testing."""
    return {
        "content": "This is a test memory",
        "agent_id": "test_agent",
        "metadata": {
            "source": "test",
            "timestamp": "2024-01-01T00:00:00",
            "tags": ["test", "sample"]
        }
    }


@pytest.fixture
def sample_tool_data():
    """Provide sample tool data for testing."""
    return {
        "name": "test_tool",
        "description": "A tool for testing",
        "usage": "Use this tool to test functionality",
        "tags": ["testing", "utility"]
    }