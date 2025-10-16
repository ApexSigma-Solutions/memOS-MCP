from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

class Database(ABC):
    @abstractmethod
    def store_memory(self, content: str, agent_id: str, metadata: Optional[Dict[str, Any]] = None) -> Optional[int]:
        """
        Store a memory entry associated with an agent and return its identifier.
        
        Parameters:
            content (str): The text content of the memory to store.
            agent_id (str): Identifier of the agent owning or generating the memory.
            metadata (Optional[Dict[str, Any]]): Optional additional attributes to store with the memory (e.g., timestamps, tags, source).
        
        Returns:
            Optional[int]: The stored memory's numeric identifier if created, or `None` if storage failed or no identifier is available.
        """
        pass

    @abstractmethod
    def get_memory(self, memory_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a stored memory by its identifier.
        
        Returns:
            memory (Optional[Dict[str, Any]]): A dictionary with the memory's data (for example: id, content, agent_id, metadata, embedding_id) if the memory exists, `None` otherwise.
        """
        pass

    @abstractmethod
    def get_memories_by_ids(self, memory_ids: List[int]) -> List[Dict[str, Any]]:
        """
        Retrieve multiple memories by their identifiers.
        
        Parameters:
            memory_ids (List[int]): List of memory IDs to retrieve.
        
        Returns:
            List[Dict[str, Any]]: A list of memory data dictionaries for the provided IDs.
        """
        pass

    @abstractmethod
    def update_memory_embedding_id(self, memory_id: int, embedding_id: str) -> bool:
        """
        Update the embedding identifier associated with a memory entry.
        
        Parameters:
            memory_id (int): ID of the memory to update.
            embedding_id (str): New embedding identifier to associate with the memory.
        
        Returns:
            `true` if the update succeeded, `false` otherwise.
        """
        pass

    @abstractmethod
    def register_tool(self, name: str, description: str, usage: str, tags: Optional[List[str]] = None) -> Optional[int]:
        """
        Register a tool with its metadata and return the assigned tool identifier.
        
        Parameters:
            name (str): Human-readable name of the tool.
            description (str): Short description of the tool's purpose.
            usage (str): Example or instructions for how the tool should be used.
            tags (Optional[List[str]]): Optional list of tags for categorization or search.
        
        Returns:
            Optional[int]: The unique identifier of the registered tool if registration succeeds, `None` otherwise.
        """
        pass

    @abstractmethod
    def get_tool(self, tool_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a registered tool by its unique identifier.
        
        Parameters:
            tool_id (int): Unique identifier of the tool to retrieve.
        
        Returns:
            Optional[Dict[str, Any]]: A dictionary containing the tool's stored data (for example: `name`, `description`, `usage`, `tags`) if found, `None` otherwise.
        """
        pass

    @abstractmethod
    def get_tools_by_context(self, query_context: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Retrieve tools relevant to a textual query context.
        
        Parameters:
        	query_context (str): Text used to match and rank tools by relevance.
        	limit (int): Maximum number of tool records to return (default 10).
        
        Returns:
        	List[Dict[str, Any]]: A list of tool data dictionaries matching the context, ordered by relevance, up to `limit`.
        """
        pass

    @abstractmethod
    def get_all_tools(self) -> List[Dict[str, Any]]:
        """
        Return a list of all registered tools.
        
        Returns:
            tools (List[Dict[str, Any]]): A list of dictionaries where each dictionary contains metadata for a registered tool (for example: id, name, description, usage, and optional tags).
        """
        pass