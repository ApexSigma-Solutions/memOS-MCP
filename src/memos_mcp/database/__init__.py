import os
from .base import Database
from .sqlite import SQLiteDatabase
from .postgres import PostgresDatabase
from .neo4j import Neo4jDatabase
from ..config import settings

_db_instance = None

_db_instance = None

def get_db_instance() -> Database:
    """Creates and returns a database instance based on settings."""
    db_type = settings.memos_db_type
    if db_type == "sqlite":
        return SQLiteDatabase(db_path=settings.memos_db_path)
    if db_type == "postgres":
        return PostgresDatabase()
    if db_type == "neo4j":
        return Neo4jDatabase()
    raise ValueError(f"Unsupported database type: {db_type}")

def get_database() -> Database:
    """
    Returns a cached singleton database instance.
    This function can be patched during testing to return a test-specific database.
    """
    global _db_instance
    if _db_instance is None:
        if os.environ.get("TESTING"):
            _db_instance = SQLiteDatabase(db_path=":memory:")
        else:
            _db_instance = get_db_instance()
    return _db_instance
