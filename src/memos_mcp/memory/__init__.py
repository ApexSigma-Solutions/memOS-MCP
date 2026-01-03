"""
Memory module for memOS.MCP ephemeral storage.

Provides Redis-backed working memory and scratchpad functionality.
"""

from .redis_client import (
    RedisMemoryClient,
    MemoryEntry,
    get_redis_client,
)

__all__ = [
    "RedisMemoryClient",
    "MemoryEntry",
    "get_redis_client",
]
