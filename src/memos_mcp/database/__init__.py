import os
from .base import Database
from .sqlite import SQLiteDatabase
from .postgres import PostgresDatabase
from .neo4j import Neo4jDatabase
from ..config import settings

_db_instance = None

_db_instance = None

def get_db_instance() -> Database:
    """
    Selects and constructs a Database implementation based on application settings.
    
    Returns:
        A Database instance configured according to settings.memos_db_type:
        - "sqlite": SQLiteDatabase initialized with settings.memos_db_path
        - "postgres": PostgresDatabase
        - "neo4j": Neo4jDatabase
    
    Raises:
        ValueError: If settings.memos_db_type is not one of "sqlite", "postgres", or "neo4j".
    """
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
    Provide a cached singleton Database instance. If no instance is cached, a new one is created; when the environment variable `TESTING` is set, an in-memory SQLite database is used.
    
    Returns:
        Database: The cached Database instance.
    """
    global _db_instance
    if _db_instance is None:
        if os.environ.get("TESTING"):
            _db_instance = SQLiteDatabase(db_path=":memory:")
        else:
            _db_instance = get_db_instance()
    return _db_instance