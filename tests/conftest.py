"""Pytest configuration and shared fixtures for memos_mcp tests."""
import os
import pytest
import tempfile


@pytest.fixture
def temp_db_path():
    """
    Provide a filesystem path to a temporary `.db` file for use in tests.
    
    Yields:
        str: Path to the temporary `.db` file created for the test. The file is removed after the test completes if it still exists.
    """
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_file.close()
    yield temp_file.name
    if os.path.exists(temp_file.name):
        os.unlink(temp_file.name)


@pytest.fixture
def temp_dir():
    """
    Create and yield a temporary directory for use in tests.
    
    The directory is removed (including its contents) after the caller finishes using it if it still exists.
    
    Returns:
        temp_directory (str): Filesystem path to the created temporary directory.
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
    Provide a sample memory dictionary for tests.
    
    Returns:
        sample_memory (dict): A dictionary representing a memory with the following keys:
            - content (str): The memory text.
            - agent_id (str): Identifier of the agent that created the memory.
            - metadata (dict): Additional metadata containing:
                - source (str): Origin of the memory (e.g., "test").
                - timestamp (str): ISO 8601 timestamp string.
                - tags (list[str]): List of tag strings associated with the memory.
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
    Provide a sample tool data dictionary for tests.
    
    Returns:
        dict: A dictionary representing a tool with the following keys:
            - name (str): Tool identifier.
            - description (str): Short description of the tool.
            - usage (str): Usage instructions or summary.
            - tags (list[str]): List of tag strings categorizing the tool.
    """
    return {
        "name": "test_tool",
        "description": "A tool for testing",
        "usage": "Use this tool to test functionality",
        "tags": ["testing", "utility"]
    }