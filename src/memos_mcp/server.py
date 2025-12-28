"""
memOS MCP Server Entrypoint
Integrates local tools and the Omega Intelligence Layer.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from mcp.server.fastmcp import FastMCP

# Import Configuration
from src.memos_mcp.config import Settings

# Import Core Logic
from src.memos_mcp.logic import MemosLogic

# Import Tools (The Mirmir Bridge)
from src.memos_mcp.tools.intelligence import consult_mirmir

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("memos_mcp")

# Global Logic Instance
logic_instance: MemosLogic = None


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[None]:
    """
    Manages the lifecycle of the memOS server.
    Initializes database connections on startup.
    """
    global logic_instance
    logger.info("🚀 Starting memOS MCP Server (Port 8768)...")

    settings = Settings()

    try:
        # Initialize Core Logic (Database, Vector Store, etc.)
        logic_instance = MemosLogic(settings)
        await logic_instance.initialize()
        logger.info("✅ memOS Logic Layer Initialized.")

        yield

    except Exception as e:
        logger.error(f"❌ Critical Startup Failure: {e}")
        raise
    finally:
        logger.info("🛑 Shutting down memOS MCP Server...")
        if logic_instance:
            await logic_instance.shutdown()


# Initialize FastMCP
mcp = FastMCP("memOS", lifespan=lifespan, dependencies=["neo4j", "pydantic"])

# --- REGISTER TOOLS ---

# 1. Intelligence Layer (The Brain)
mcp.add_tool(consult_mirmir)


# 2. Memory Tools (Placeholders for Logic Layer)
@mcp.tool()
async def search_memory(query: str, limit: int = 5) -> str:
    """Searches the memOS knowledge base/vector store."""
    if not logic_instance:
        return "Error: System not initialized."
    return await logic_instance.search(query, limit)


@mcp.tool()
async def store_memory(content: str, tags: list[str] = []) -> str:
    """Stores a new memory fragment."""
    if not logic_instance:
        return "Error: System not initialized."
    return await logic_instance.store(content, tags)


@mcp.resource("config://status")
def get_system_status() -> str:
    """Returns the health status of the memOS ecosystem."""
    status = "ONLINE" if logic_instance else "INITIALIZING"
    return f"memOS Status: {status}\nIntelligence Layer: ACTIVE (Mirmir Connected)"


if __name__ == "__main__":
    mcp.run()
