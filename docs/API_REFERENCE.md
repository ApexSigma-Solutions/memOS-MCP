# API Reference

This document provides a reference for the MCP tools and resources provided by the MemOS FastMCP server.

## Tools

### `store_memory(agent_id: str, content: str, metadata: dict = None) -> dict`

Stores a persistent memory for an agent.

**Parameters:**

- `agent_id` (str): The ID of the agent.
- `content` (str): The content of the memory.
- `metadata` (dict, optional): A dictionary of metadata to store with the memory.

**Returns:**

A dictionary containing the status of the operation and the ID of the new memory.

### `retrieve_context(agent_id: str, query: str, top_k: int = 5) -> list`

Retrieves relevant context from an agent's memory.

**Parameters:**

- `agent_id` (str): The ID of the agent.
- `query` (str): The query to search for.
- `top_k` (int, optional): The number of results to return.

**Returns:**

A list of memory objects that match the query.

### `register_tool(tool_name: str, description: str, usage: str, tags: list = None) -> dict`

Registers a new tool in the tool registry.

**Parameters:**

- `tool_name` (str): The name of the tool.
- `description` (str): A description of the tool.
- `usage` (str): Instructions on how to use the tool.
- `tags` (list, optional): A list of tags to categorize the tool.

**Returns:**

A dictionary containing the status of the operation and the ID of the new tool.

## Resources

### `memory://{agent_id}/graph`

Accesses an agent's memory graph structure.

**Parameters:**

- `agent_id` (str): The ID of the agent.

**Returns:**

A dictionary representing the agent's memory graph.

### `memory://{agent_id}/tools`

Accesses an agent's known tools.

**Parameters:**

- `agent_id` (str): The ID of the agent.

**Returns:**

A list of tool objects that the agent has registered.
