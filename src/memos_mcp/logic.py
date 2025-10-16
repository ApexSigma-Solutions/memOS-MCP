from memos_mcp.database import get_database
try:
    from memos_mcp.database.qdrant import get_qdrant_client  # expected real implementation
except Exception:
    get_qdrant_client = None  # fallback if not available

async def store_memory(agent_id: str, content: str, metadata: dict = None) -> dict:
    """
    Store persistent memory for an agent and attempt optional vector embedding storage.
    
    Parameters:
        agent_id (str): Identifier of the agent owning the memory.
        content (str): Text content of the memory to store.
        metadata (dict, optional): Additional metadata to attach to the memory.
    
    Returns:
        dict: Operation result containing:
            - status (str): "success" on success, "error" on failure.
            - memory_id (str|int): Identifier of the stored memory record when successful.
            - point_id (str|int|None): Identifier of the stored embedding/point if an external vector store is available and the embedding was stored; `None` if no embedding was stored or embedding storage failed.
            - message (str, optional): Error message when `status` is "error".
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
    Retrieve memories most relevant to a text query for a specific agent.
    
    Parameters:
    	agent_id (str): Identifier of the agent whose memories should be searched.
    	query (str): Text query used to find similar memories.
    	top_k (int): Maximum number of results to return (default 5).
    
    Returns:
    	list: A list of memory records. When a vector search backend is available and succeeds, each record may include a `similarity_score` field (higher means more similar). Returns an empty list if no vector search is available, no matches are found, or the search fails.
    """
    db = get_database()

    if callable(get_qdrant_client):
        try:
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
        except Exception as e:
            print(f"Warning: Qdrant unavailable or failed during search: {e}")

    # Fallback: no vector search available; return empty or a simple heuristic
    return []

async def register_tool(tool_name: str, description: str, usage: str, tags: list = None) -> dict:
    """
    Register a tool in persistent storage so the agent can reference it later.
    
    Parameters:
        tags (list, optional): List of tag strings to categorize the tool.
    
    Returns:
        dict: {"status": "success", "tool_id": <id>} on success, or {"status": "error", "message": <reason>} on failure.
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
    
    This function provides access to the agent's memory graph. Currently it returns an empty dictionary as a placeholder for the graph structure.
    
    Returns:
        dict: A dictionary representing the agent's memory graph (currently empty).
    """
    return {}

async def tool_registry(agent_id: str) -> list:
    """
    Return the list of tools registered in storage for the agent.
    
    Returns:
        list: A list of tool records, each containing fields such as `id`, `name`, `description`, `usage`, and `tags`.
    """
    db = get_database()
    return db.get_all_tools()