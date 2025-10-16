from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

class Database(ABC):
    @abstractmethod
    def store_memory(self, content: str, agent_id: str, metadata: Optional[Dict[str, Any]] = None) -> Optional[int]:
        """
        Store a memory item associated with a specific agent.
        
        Parameters:
            content (str): The textual content of the memory.
            agent_id (str): Identifier of the agent to which the memory belongs.
            metadata (Optional[Dict[str, Any]]): Optional additional key-value data to persist with the memory (e.g., tags, timestamps, source).
        
        Returns:
            memory_id (Optional[int]): The identifier of the newly stored memory, or `None` if the memory could not be stored.
        """
        pass

    @abstractmethod
    def get_memory(self, memory_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a stored memory by its identifier.
        
        Parameters:
            memory_id (int): Identifier of the memory to retrieve.
        
        Returns:
            memory (Optional[Dict[str, Any]]): Dictionary representing the memory if found, `None` otherwise.
        """
        pass

    @abstractmethod
    def get_memories_by_ids(self, memory_ids: List[int]) -> List[Dict[str, Any]]:
        """
        Retrieve multiple memories by their identifiers.
        
        Parameters:
            memory_ids (List[int]): List of memory IDs to retrieve.
        
        Returns:
            List[Dict[str, Any]]: A list of memory objects (dictionaries) corresponding to the provided IDs. IDs that do not match any stored memory are omitted from the result.
        """
        pass

    @abstractmethod
    def update_memory_embedding_id(self, memory_id: int, embedding_id: str) -> bool:
        """
        Update the embedding identifier associated with a stored memory.
        
        Parameters:
            memory_id (int): Identifier of the memory to update.
            embedding_id (str): Identifier of the embedding to associate with the memory.
        
        Returns:
            bool: `True` if the embedding id was successfully updated, `False` otherwise.
        """
        pass

    @abstractmethod
    def register_tool(self, name: str, description: str, usage: str, tags: Optional[List[str]] = None) -> Optional[int]:
        """
        Register a tool's metadata for later retrieval by ID or context.
        
        Parameters:
            name (str): Human-readable name of the tool.
            description (str): Short description of the tool's purpose or behavior.
            usage (str): Example or explanation of how the tool should be used.
            tags (Optional[List[str]]): Optional list of tags or keywords to categorize the tool.
        
        Returns:
            tool_id (Optional[int]): Integer identifier assigned to the registered tool if successful, `None` otherwise.
        """
        pass

    @abstractmethod
    def get_tool(self, tool_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a registered tool by its identifier.
        
        Parameters:
            tool_id (int): The unique identifier of the tool to retrieve.
        
        Returns:
            Optional[Dict[str, Any]]: A dictionary representing the tool record if found, `None` otherwise.
        """
        pass

    @abstractmethod
    def get_tools_by_context(self, query_context: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Retrieve tools matching a textual context query, ordered by relevance.
        
        Parameters:
        	query_context (str): Text used to search tool descriptions and usage.
        	limit (int): Maximum number of tools to return (defaults to 10).
        
        Returns:
        	List[Dict[str, Any]]: List of tool records that match `query_context`, limited to `limit` items.
        """
        pass

    @abstractmethod
    def get_all_tools(self) -> List[Dict[str, Any]]:
        """
        Retrieve all registered tools.
        
        Returns:
            List[Dict[str, Any]]: A list of dictionaries, each representing a registered tool (for example: id, name, description, usage, tags). Returns an empty list if no tools are registered.
        """
        pass