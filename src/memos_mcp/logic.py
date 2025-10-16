from memos_mcp.database import get_database
try:
    from memos_mcp.database.qdrant import get_qdrant_client  # expected real implementation
except Exception:
    get_qdrant_client = None  # fallback if not available

async def store_memory(agent_id: str, content: str, metadata: dict = None) -> dict:
    """Store persistent memory for an agent"""
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
    """Retrieve relevant context from agent memory"""
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
    """Register tool awareness in agent memory"""
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
    """Access agent's known tools"""
    db = get_database()
    return db.get_all_tools()
