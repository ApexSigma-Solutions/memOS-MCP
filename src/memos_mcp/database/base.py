from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

class Database(ABC):
    @abstractmethod
    def store_memory(self, content: str, agent_id: str, metadata: Optional[Dict[str, Any]] = None) -> Optional[int]:
        """
        Persist a memory entry associated with an agent.
        
        Parameters:
            content (str): Text content of the memory to persist.
            agent_id (str): Identifier of the agent the memory belongs to.
            metadata (Optional[Dict[str, Any]]): Optional additional data to store with the memory (for example timestamps, source, or tags).
        
        Returns:
            Optional[int]: Identifier of the stored memory if persisted, `None` if the memory was not stored.
        """
        pass

    @abstractmethod
    def get_memory(self, memory_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a stored memory entry by its identifier.
        
        Parameters:
            memory_id (int): Identifier of the memory to retrieve.
        
        Returns:
            Optional[Dict[str, Any]]: Dictionary representing the memory record, or `None` if no matching memory is found.
        """
        pass

    @abstractmethod
    def get_memories_by_ids(self, memory_ids: List[int]) -> List[Dict[str, Any]]:
        """
        Retrieve multiple memory entries by their IDs.
        
        Parameters:
            memory_ids (List[int]): List of memory identifiers to retrieve.
        
        Returns:
            List[Dict[str, Any]]: List of memory dictionaries corresponding to the provided IDs; IDs that are not found are omitted from the result.
        """
        pass

    @abstractmethod
    def update_memory_embedding_id(self, memory_id: int, embedding_id: str) -> bool:
        """
        Update the embedding identifier associated with a stored memory.
        
        Parameters:
            memory_id (int): Identifier of the memory to update.
            embedding_id (str): Embedding identifier to associate with the memory.
        
        Returns:
            bool: `True` if the update succeeded, `False` otherwise.
        """
        pass

    @abstractmethod
    def register_tool(self, name: str, description: str, usage: str, tags: Optional[List[str]] = None) -> Optional[int]:
        """
        Register a tool with its metadata for later lookup.
        
        Parameters:
        	name (str): Human-readable tool name.
        	description (str): Short description of what the tool does.
        	usage (str): Example or summary of how the tool should be used.
        	tags (Optional[List[str]]): Optional list of tags to categorize or index the tool.
        
        Returns:
        	tool_id (Optional[int]): Identifier of the registered tool if successful, or `None` if registration failed.
        """
        pass

    @abstractmethod
    def get_tool(self, tool_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a registered tool by its identifier.
        
        Parameters:
            tool_id (int): Identifier of the tool to retrieve.
        
        Returns:
            Optional[Dict[str, Any]]: Dictionary representing the tool and its metadata if found, `None` if no tool exists with the given identifier.
        """
        pass

    @abstractmethod
    def get_tools_by_context(self, query_context: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Retrieve tools whose metadata or descriptions best match the given context string.
        
        Parameters:
            query_context (str): Context or query text used to find relevant tools.
            limit (int): Maximum number of tools to return.
        
        Returns:
            List[Dict[str, Any]]: A list of tool records that match the context, up to `limit` items.
        """
        pass

    @abstractmethod
    def get_all_tools(self) -> List[Dict[str, Any]]:
        """
        Return a list of all registered tool records.
        
        Returns:
            List[Dict[str, Any]]: A list of tool dictionaries; empty list if no tools are registered.
        """
        pass