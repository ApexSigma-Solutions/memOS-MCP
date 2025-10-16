from memos_mcp.database import get_database
from memos_mcp.database.qdrant import get_qdrant_client

async def store_memory(agent_id: str, content: str, metadata: dict = None) -> dict:
    """
    Persist an agent's memory content and its associated vector embedding.
    
    Stores the provided content in the database, generates and stores a placeholder embedding for that memory, and links the embedding's point ID to the stored memory record.
    
    Parameters:
        agent_id (str): Identifier of the agent owning the memory.
        content (str): Text content to persist as memory.
        metadata (dict, optional): Additional metadata to attach to both the memory record and its embedding.
    
    Returns:
        dict: On success, {"status": "success", "memory_id": <memory_id>, "point_id": <point_id or None>}.
              On failure to store the memory, {"status": "error", "message": "Failed to store memory"}.
    """
    db = get_database()
    qdrant_client = get_qdrant_client()
    memory_id = db.store_memory(
        content=content,
        agent_id=agent_id,
        metadata=metadata
    )
    if memory_id is None:
        return {"status": "error", "message": "Failed to store memory"}
    embedding = qdrant_client.generate_placeholder_embedding(content)
    point_id = qdrant_client.store_embedding(
        embedding=embedding,
        memory_id=memory_id,
        agent_id=agent_id,
        metadata=metadata
    )
    if point_id is None:
        print(f"Warning: Failed to store embedding for memory {memory_id}")
    else:
        db.update_memory_embedding_id(memory_id, point_id)
    return {"status": "success", "memory_id": memory_id, "point_id": point_id}

async def retrieve_context(agent_id: str, query: str, top_k: int = 5) -> list:
    """
    Retrieve memories relevant to a query for the given agent.
    
    Searches the agent's stored memories by similarity to the query and returns the matching memory records with an added `similarity_score` field for each result.
    
    Parameters:
        top_k (int): Maximum number of similar memories to return.
    
    Returns:
        list: Memory objects matching the query, each augmented with a `similarity_score` (float).
    """
    db = get_database()
    qdrant_client = get_qdrant_client()
    query_embedding = qdrant_client.generate_placeholder_embedding(query)
    search_results = qdrant_client.search_similar_memories(
        query_embedding=query_embedding,
        top_k=top_k,
        agent_id=agent_id
    )
    memory_ids = [result["memory_id"] for result in search_results]
    if not memory_ids:
        return []
    memories = db.get_memories_by_ids(memory_ids)
    memory_scores = {result["memory_id"]: result["score"] for result in search_results}
    for memory in memories:
        memory["similarity_score"] = memory_scores.get(memory["id"])
    return memories

async def register_tool(tool_name: str, description: str, usage: str, tags: list = None) -> dict:
    """
    Register a tool in the agent's tool registry.
    
    Returns:
        dict: On success: `{"status": "success", "tool_id": <tool_id>}`. On failure: `{"status": "error", "message": "Failed to register tool"}`.
    """
    db = get_database()
    tool_id = db.register_tool(
        name=tool_name,
        description=description,
        usage=usage,
        tags=tags
    )
    if tool_id is None:
        return {"status": "error", "message": "Failed to register tool"}
    return {"status": "success", "tool_id": tool_id}

async def memory_graph(agent_id: str) -> dict:
    """
    Return the agent's memory graph structure.
    
    Parameters:
        agent_id (str): Identifier of the agent whose memory graph is requested.
    
    Returns:
        graph (dict): A mapping representing the agent's memory graph. Currently returns an empty dict as a placeholder when no graph is available.
    """
    return {}

async def tool_registry(agent_id: str) -> list:
    """
    Retrieve the tools known to the specified agent.
    
    Parameters:
        agent_id (str): Identifier of the agent whose tool registry to retrieve.
    
    Returns:
        list: Tool records retrieved from the database.
    """
    db = get_database()
    return db.get_all_tools()