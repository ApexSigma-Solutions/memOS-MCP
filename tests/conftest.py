"""Pytest configuration and shared fixtures for memos_mcp tests."""
import os
import pytest
import tempfile


@pytest.fixture
def temp_db_path():
    """
    Create a temporary file with a '.db' suffix and provide its filesystem path for a test.
    
    The file is created and closed before the fixture returns. After the test finishes, the file is removed if it still exists.
    
    Returns:
        db_path (str): Filesystem path to the temporary `.db` file.
    """
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_file.close()
    yield temp_file.name
    if os.path.exists(temp_file.name):
        os.unlink(temp_file.name)


@pytest.fixture
def temp_dir():
    """
    Create and provide a temporary directory for a test, removing it after the test completes.
    
    Returns:
        temp_directory (str): Filesystem path to the created temporary directory; the directory is deleted after the fixture is torn down.
    """
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
    """
    Sample memory record used in tests.
    
    Returns:
        dict: A memory dictionary with keys:
            - content (str): The memory text.
            - agent_id (str): Identifier of the agent that created the memory.
            - metadata (dict): Additional metadata with keys:
                - source (str): Origin of the memory.
                - timestamp (str): ISO 8601 timestamp string.
                - tags (list[str]): List of tag strings.
    """
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
    """
    Provide a canonical sample tool dictionary for use in tests.
    
    Returns:
        dict: A dictionary representing a tool with keys:
            - name (str): Identifier for the tool.
            - description (str): Short human-readable description.
            - usage (str): Example or brief usage instructions.
            - tags (list[str]): List of tag strings categorizing the tool.
    """
    return {
        "name": "test_tool",
        "description": "A tool for testing",
        "usage": "Use this tool to test functionality",
        "tags": ["testing", "utility"]
    }
