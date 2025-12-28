import logging
from memos_mcp.database import get_database

try:
    from memos_mcp.database.qdrant import get_qdrant_client
except ImportError:
    get_qdrant_client = None

logger = logging.getLogger(__name__)


async def store_memory(agent_id: str, content: str, metadata: dict = None) -> dict:
    """Store persistent memory for an agent"""
    db = get_database()
    try:
        memory_id = db.store_memory(
            content=content, agent_id=agent_id, metadata=metadata
        )
        if memory_id is None:
            return {"status": "error", "message": "Failed to store memory"}
    except Exception as e:
        logger.error("Failed to store memory: %s", e)
        return {"status": "error", "message": "Failed to store memory"}

    if get_qdrant_client:
        qdrant_client = get_qdrant_client()
        embedding = qdrant_client.generate_placeholder_embedding(content)
        point_id = qdrant_client.store_embedding(
            embedding=embedding,
            memory_id=memory_id,
            agent_id=agent_id,
            metadata=metadata,
        )
        if point_id is None:
            logger.warning("Failed to store embedding for memory %s", memory_id)
        else:
            db.update_memory_embedding_id(memory_id, point_id)
        return {"status": "success", "memory_id": memory_id, "point_id": point_id}
    return {"status": "success", "memory_id": memory_id, "point_id": None}


async def retrieve_context(agent_id: str, query: str, top_k: int = 5) -> list:
    """Retrieve relevant context from agent memory"""
    db = get_database()
    if not get_qdrant_client:
        return []

    qdrant_client = get_qdrant_client()
    query_embedding = qdrant_client.generate_placeholder_embedding(query)
    search_results = qdrant_client.search_similar_memories(
        query_embedding=query_embedding, top_k=top_k, agent_id=agent_id
    )
    memory_ids = [result["memory_id"] for result in search_results]
    if not memory_ids:
        return []
    try:
        memories = db.get_memories_by_ids(memory_ids)
        memory_scores = {
            result["memory_id"]: result["score"] for result in search_results
        }
        for memory in memories:
            memory["similarity_score"] = memory_scores.get(memory["id"])
        return memories
    except Exception as e:
        logger.error("Failed to retrieve memories: %s", e)
        return []


async def register_tool(
    tool_name: str, description: str, usage: str, tags: list = None
) -> dict:
    """Register tool awareness in agent memory"""
    db = get_database()
    try:
        tool_id = db.register_tool(
            name=tool_name, description=description, usage=usage, tags=tags
        )
        if tool_id is None:
            return {"status": "error", "message": "Failed to register tool"}
        return {"status": "success", "tool_id": tool_id}
    except Exception as e:
        logger.error("Failed to register tool: %s", e)
        return {"status": "error", "message": "Failed to register tool"}


async def memory_graph(agent_id: str) -> dict:
    """Access agent's memory graph structure"""
    return {}


async def tool_registry() -> list:
    """Access agent's known tools"""
    db = get_database()
    try:
        return db.get_all_tools()
    except Exception as e:
        logger.error("Failed to get all tools: %s", e)
        return []
