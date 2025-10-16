from memos_mcp.database import get_database
try:
    from memos_mcp.database.qdrant import get_qdrant_client  # expected real implementation
except Exception:
    get_qdrant_client = None  # fallback if not available

async def store_memory(agent_id: str, content: str, metadata: dict = None) -> dict:
    """
    Persist an agent's memory and, if available, store a corresponding embedding in Qdrant.
    
    Parameters:
        agent_id (str): Identifier of the agent owning the memory.
        content (str): The memory text to persist.
        metadata (dict, optional): Additional metadata to associate with the memory.
    
    Returns:
        dict: A result object containing:
            - status (str): "success" or "error".
            - memory_id (str|None): Identifier of the stored memory on success.
            - point_id (str|None): Identifier of the stored embedding point if created, otherwise `None`.
    """
    db = get_database()

    memory_id = db.store_memory(
        content=content,
        agent_id=agent_id,
        metadata=metadata
    )
    if memory_id is None:
        return {"status": "error", "message": "Failed to store memory"}

    point_id = None
    # Optional Qdrant flow
    if callable(get_qdrant_client):
        try:
            qdrant_client = get_qdrant_client()
            embedding = qdrant_client.generate_placeholder_embedding(content)
            point_id = qdrant_client.store_embedding(
                embedding=embedding,
                memory_id=memory_id,
                agent_id=agent_id,
                metadata=metadata
            )
            if point_id:
                db.update_memory_embedding_id(memory_id, point_id)
            else:
                print(f"Warning: Failed to store embedding for memory {memory_id}")
        except Exception as e:
            print(f"Warning: Qdrant unavailable or failed: {e}")
    else:
        print("Info: Qdrant client not configured; skipping embedding storage")

    return {"status": "success", "memory_id": memory_id, "point_id": point_id}

async def retrieve_context(agent_id: str, query: str, top_k: int = 5) -> list:
    """
    Retrieve memories relevant to a query for a given agent.
    
    Searches the agent's stored memories for the top-k entries similar to the provided query and returns those memories annotated with a `similarity_score` for each memory.
    
    Parameters:
        top_k (int): Maximum number of similar memories to return.
    
    Returns:
        list: A list of memory records found for the agent, each augmented with a `similarity_score` field (float) indicating similarity to the query. If no matches are found, returns an empty list.
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
    Register a tool's metadata in the persistent agent tool registry.
    
    Parameters:
        tags (list, optional): List of tags or categories associated with the tool.
    
    Returns:
        dict: {"status": "success", "tool_id": <id>} on success; {"status": "error", "message": <reason>} on failure.
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
    Return the memory graph for the specified agent.
    
    Returns:
        graph (dict): Mapping representing the agent's memory graph; empty dict if no graph is available.
    """
    return {}

async def tool_registry(agent_id: str) -> list:
    """
    Retrieve the list of tools known by an agent.
    
    Parameters:
        agent_id (str): Identifier of the agent whose tools to retrieve.
    
    Returns:
        list: Tool records known to the agent.
    """
    db = get_database()
    return db.get_all_tools()