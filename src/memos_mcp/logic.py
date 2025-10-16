from memos_mcp.database import get_database
from memos_mcp.database.qdrant import get_qdrant_client

async def store_memory(agent_id: str, content: str, metadata: dict = None) -> dict:
    """
    Store a piece of persistent memory for the specified agent and record its vector embedding.
    
    Parameters:
        agent_id (str): Identifier of the agent owning the memory.
        content (str): Textual content of the memory to store.
        metadata (dict, optional): Arbitrary metadata to attach to the memory.
    
    Returns:
        result (dict): On success, `{'status': 'success', 'memory_id': <id>, 'point_id': <embedding_point_id>}`.
        On failure to persist the memory, `{'status': 'error', 'message': 'Failed to store memory'}`. If embedding storage fails,
        `point_id` will be `None` while the memory record remains stored.
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
    Retrieve relevant memories for an agent that are most similar to a query.
    
    Parameters:
        agent_id (str): Identifier of the agent whose memories will be searched.
        query (str): Text query used to find relevant memories.
        top_k (int): Maximum number of similar memories to return.
    
    Returns:
        list: A list of memory dictionaries matched to the query. Each returned memory includes a
        `similarity_score` field indicating the match score. Returns an empty list if no matches are found.
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
    Register a tool in the persistent tool registry for agents.
    
    Parameters:
        tool_name (str): Human-readable name of the tool.
        description (str): Short description of the tool's purpose.
        usage (str): Usage notes or example invocation for the tool.
        tags (list, optional): List of tag strings to categorize the tool.
    
    Returns:
        dict: On success, `{"status": "success", "tool_id": <id>}` where `<id>` is the database-assigned tool identifier.
              On failure, `{"status": "error", "message": "Failed to register tool"}`.
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
    """Access agent's memory graph structure"""
    return {}

async def tool_registry(agent_id: str) -> list:
    """
    Return the list of tools known to the system for the given agent.
    
    Parameters:
        agent_id (str): Identifier of the agent (currently not used by the implementation).
    
    Returns:
        list: A list of tool records as provided by the database.
    """
    db = get_database()
    return db.get_all_tools()