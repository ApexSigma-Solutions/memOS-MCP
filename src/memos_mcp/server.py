import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
from fastmcp import FastMCP
from . import logic
from .database import get_database
try:
    from .database.qdrant import get_qdrant_client
except ImportError:
    logger.info("Qdrant is not available. Proceeding without Qdrant support.")
    get_qdrant_client = None
mcp = FastMCP("MemOS Cognitive Server")

@mcp.tool()
async def health():
    return {"status": "healthy", "service": "memos_mcp"}

mcp.tool(logic.store_memory)
mcp.tool(logic.retrieve_context)
mcp.tool(logic.register_tool)
mcp.resource("memory://{agent_id}/graph")(logic.memory_graph)
mcp.resource("memory/tools")(logic.tool_registry)

def init_clients():
    try:
        get_database()
        if get_qdrant_client:
            get_qdrant_client()
        logger.info("Database and Qdrant clients initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize clients: {e}")
        exit(1)

if __name__ == "__main__":
    init_clients()
    mcp.run()
