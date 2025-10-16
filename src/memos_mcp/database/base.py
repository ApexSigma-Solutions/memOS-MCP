from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

class Database(ABC):
    @abstractmethod
    def store_memory(self, content: str, agent_id: str, metadata: Optional[Dict[str, Any]] = None) -> Optional[int]:
        """
        Store a memory item with its content and associate it with an agent.
        
        Parameters:
            content (str): The textual content of the memory.
            agent_id (str): Identifier of the agent associated with the memory.
            metadata (Optional[Dict[str, Any]]): Optional additional attributes to store with the memory (e.g., timestamps, tags, source).
        
        Returns:
            Optional[int]: The identifier of the stored memory if saved, otherwise `None`.
        """
        pass

    @abstractmethod
    def get_memory(self, memory_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a stored memory by its identifier.
        
        Parameters:
            memory_id (int): Identifier of the memory to retrieve.
        
        Returns:
            memory (Optional[Dict[str, Any]]): The memory record as a dictionary if found, `None` otherwise.
        """
        pass

    @abstractmethod
    def get_memories_by_ids(self, memory_ids: List[int]) -> List[Dict[str, Any]]:
        """
        Retrieve multiple memories by their identifiers.
        
        Parameters:
            memory_ids (List[int]): List of memory IDs to fetch.
        
        Returns:
            List[Dict[str, Any]]: A list of memory dictionaries corresponding to the specified IDs; only memories that exist are included.
        """
        pass

    @abstractmethod
    def update_memory_embedding_id(self, memory_id: int, embedding_id: str) -> bool:
        """
        Update the embedding identifier associated with an existing memory.
        
        @param memory_id: Identifier of the memory to update.
        @param embedding_id: New embedding identifier to associate with the memory.
        @returns: `true` if the embedding identifier was updated, `false` otherwise.
        """
        pass

    @abstractmethod
    def register_tool(self, name: str, description: str, usage: str, tags: Optional[List[str]] = None) -> Optional[int]:
        """
        Register a tool with its metadata and return its assigned identifier.
        
        Parameters:
            name (str): Human-readable name of the tool.
            description (str): Short description of what the tool does.
            usage (str): Example or guidance on how the tool should be used.
            tags (Optional[List[str]]): Optional list of tags for categorization or search.
        
        Returns:
            tool_id (Optional[int]): Integer identifier assigned to the registered tool, or `None` if registration failed.
        """
        pass

    @abstractmethod
    def get_tool(self, tool_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a registered tool by its identifier.
        
        Parameters:
        	tool_id (int): Identifier of the tool to retrieve.
        
        Returns:
        	tool (Optional[Dict[str, Any]]): Dictionary representing the tool if found, `None` otherwise.
        """
        pass

    @abstractmethod
    def get_tools_by_context(self, query_context: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Retrieve tools relevant to a textual context.
        
        Parameters:
            query_context (str): Textual context or query used to match and rank tools.
            limit (int): Maximum number of tools to return; defaults to 10.
        
        Returns:
            List[Dict[str, Any]]: A list of tool records matching the context, each represented as a dictionary.
        """
        pass

    @abstractmethod
    def get_all_tools(self) -> List[Dict[str, Any]]:
        """
        Return a list of all registered tools with their metadata.
        
        Returns:
            List[Dict[str, Any]]: A list of tool records, where each record is a dictionary containing tool fields such as identifier, name, description, usage, and optional tags.
        """
        pass