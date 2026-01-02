import logging
from memos_mcp.database import get_database

logger = logging.getLogger(__name__)


class MemosLogic:
    """Core logic layer for memOS MCP Server"""

    def __init__(self, settings=None):
        """Initialize the MemosLogic layer"""
        self.settings = settings
        self.db = None
        self.qdrant_client = None

    async def initialize(self):
        """Initialize database connections"""
        self.db = get_database()
        logger.info("✅ MemosLogic database initialized.")

    async def shutdown(self):
        """Shutdown database connections"""
        logger.info("🛑 MemosLogic shutting down...")
        self.db = None
        self.qdrant_client = None

    async def search(self, query: str, limit: int = 5) -> str:
        """Search memories"""
        try:
            results = await retrieve_context("default", query, limit)
            if not results:
                return f"No memories found for query: {query}"
            return str(results)
        except Exception as e:
            logger.error(f"Search error: {e}")
            return f"Search failed: {e}"

    async def store(self, content: str, tags: list[str] = []) -> str:
        """Store a memory"""
        try:
            result = await store_memory("default", content, {"tags": tags})
            return str(result)
        except Exception as e:
            logger.error(f"Store error: {e}")
            return f"Store failed: {e}"



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
    
    # Note: Vector embedding storage disabled (using PG Vector)
    return {"status": "success", "memory_id": memory_id, "point_id": None}


async def retrieve_context(agent_id: str, query: str, top_k: int = 5) -> list:
    """Retrieve relevant context from agent memory"""
    db = get_database()
    
    # Note: Vector search disabled (using PG Vector)
    # Return empty list for now - PG Vector search to be implemented
    logger.info("Vector search via Qdrant disabled - using database fallback")
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
