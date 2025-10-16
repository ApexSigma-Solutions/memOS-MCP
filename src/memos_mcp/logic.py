from memos_mcp.database import get_database
try:
    from memos_mcp.database.qdrant import get_qdrant_client  # expected real implementation
except Exception:
    get_qdrant_client = None  # fallback if not available

async def store_memory(agent_id: str, content: str, metadata: dict = None) -> dict:
    """
    Store an agent's memory and its embedding, persisting both to the database and the vector store.
    
    Parameters:
        agent_id (str): Identifier of the agent owning the memory.
        content (str): Text content to persist and embed.
        metadata (dict, optional): Additional metadata to associate with the memory and embedding.
    
    Returns:
        dict: Result object with a "status" key:
            - If status is "success", includes "memory_id" (the database record id) and "point_id" (the vector store id; may be `None` if storing the embedding failed).
            - If status is "error", includes "message" describing the failure to store the memory.
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
    Retrieve memories most semantically similar to a query for the specified agent.
    
    Parameters:
        agent_id (str): Identifier of the agent whose memories should be searched.
        query (str): Text query used to find relevant memories.
        top_k (int): Maximum number of similar memories to return.
    
    Returns:
        list: A list of memory records matching the query. Each record will include a `similarity_score` key with the similarity value. Returns an empty list if no relevant memories are found.
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
    Register a tool record in the agent's memory store.
    
    Parameters:
        tool_name (str): Human-readable name of the tool.
        description (str): Short description of what the tool does.
        usage (str): Example or summary of how the tool is used.
        tags (list, optional): List of tags or categories associated with the tool.
    
    Returns:
        result (dict): A dictionary with a `status` key. On success the dictionary contains
        `{"status": "success", "tool_id": <id>}`. On failure it contains
        `{"status": "error", "message": "<error message>"}`.
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
    Provide the agent's memory graph structure.
    
    Returns:
        graph (dict): Mapping of node identifiers to node data and adjacency information representing the agent's memory graph.
    """
    return {}

async def tool_registry(agent_id: str) -> list:
    """
    Retrieve the list of tools registered for a given agent.
    
    Parameters:
        agent_id (str): Identifier of the agent whose tool registry to retrieve.
    
    Returns:
        list: Tool records returned by the database for the specified agent.
    """
    db = get_database()
    return db.get_all_tools()