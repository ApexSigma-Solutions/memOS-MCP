from fastmcp import FastMCP
from . import logic

mcp = FastMCP("MemOS Cognitive Server")

mcp.tool(logic.store_memory)
mcp.tool(logic.retrieve_context)
mcp.tool(logic.register_tool)
mcp.resource("memory://{agent_id}/graph")(logic.memory_graph)
mcp.resource("memory://{agent_id}/tools")(logic.tool_registry)

if __name__ == "__main__":
    mcp.run()
