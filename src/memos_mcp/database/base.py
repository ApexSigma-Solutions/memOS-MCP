from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

class Database(ABC):
    @abstractmethod
    def store_memory(self, content: str, agent_id: str, metadata: Optional[Dict[str, Any]] = None) -> Optional[int]:
        """
        Store a memory item associated with an agent.
        
        Parameters:
            content (str): The textual content of the memory.
            agent_id (str): Identifier of the agent that owns or created the memory.
            metadata (Optional[Dict[str, Any]]): Optional arbitrary key-value data to store alongside the memory.
        
        Returns:
            memory_id (Optional[int]): The identifier of the stored memory if creation succeeded, `None` otherwise.
        """
        pass

    @abstractmethod
    def get_memory(self, memory_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a stored memory by its identifier.
        
        Parameters:
            memory_id (int): The identifier of the memory to retrieve.
        
        Returns:
            Optional[Dict[str, Any]]: A dictionary representing the memory record, or `None` if no memory exists for the given `memory_id`.
        """
        pass

    @abstractmethod
    def get_memories_by_ids(self, memory_ids: List[int]) -> List[Dict[str, Any]]:
        """
        Retrieve multiple memory records for the given memory IDs.
        
        Parameters:
        	memory_ids (List[int]): List of memory identifiers to retrieve.
        
        Returns:
        	List[Dict[str, Any]]: A list of memory dictionaries corresponding to the provided IDs; only existing memories are included.
        """
        pass

    @abstractmethod
    def update_memory_embedding_id(self, memory_id: int, embedding_id: str) -> bool:
        """
        Update the embedding identifier associated with a stored memory.
        
        Parameters:
            memory_id (int): Identifier of the memory record to update.
            embedding_id (str): Identifier of the embedding to associate with the memory.
        
        Returns:
            bool: True if the memory was found and its embedding_id was updated, False otherwise.
        """
        pass

    @abstractmethod
    def register_tool(self, name: str, description: str, usage: str, tags: Optional[List[str]] = None) -> Optional[int]:
        """
        Register a tool with its name, description, usage instructions, and optional tags.
        
        Parameters:
            tags (Optional[List[str]]): Optional list of tags to categorize or group the tool.
        
        Returns:
            Optional[int]: Identifier of the newly registered tool, or `None` if registration did not create an entry.
        """
        pass

    @abstractmethod
    def get_tool(self, tool_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a registered tool by its identifier.
        
        Parameters:
            tool_id (int): The numeric identifier of the tool to retrieve.
        
        Returns:
            Optional[Dict[str, Any]]: A dictionary representing the tool (for example: `{"id": ..., "name": ..., "description": ..., "usage": ..., "tags": [...]}`) if found, `None` otherwise.
        """
        pass

    @abstractmethod
    def get_tools_by_context(self, query_context: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Retrieve tools relevant to the provided query context, ordered by relevance and limited by `limit`.
        
        Parameters:
            query_context (str): Textual context or query used to match and rank relevant tools.
            limit (int): Maximum number of tool records to return.
        
        Returns:
            List[Dict[str, Any]]: A list of tool dictionaries matching the context, up to `limit` items.
        """
        pass

    @abstractmethod
    def get_all_tools(self) -> List[Dict[str, Any]]:
        """
        Return a list of all registered tools.
        
        Each item in the returned list is a dictionary representing a tool (for example: id, name, description, usage, and optional tags).
        Returns:
            A list of tool dictionaries.
        """
        pass