import os
from .base import Database
from .sqlite import SQLiteDatabase
from .postgres import PostgresDatabase
from .neo4j import Neo4jDatabase
from ..config import settings

_db_instance = None

def get_database() -> Database:
    """
    Obtain the module-wide Database instance configured for the current environment.
    
    Initializes and caches a single Database instance on first call: if the TESTING environment variable is set a test SQLite instance is used; otherwise the instance type is chosen from application settings. Subsequent calls return the cached instance.
    
    Returns:
        Database: The cached module-level Database instance.
    
    Raises:
        ValueError: If the configured database type in settings is not supported.
    """
    global _db_instance
    if _db_instance is None:
        if os.environ.get("TESTING"):
            _db_instance = SQLiteDatabase(db_path="test_memory.db")
        else:
            db_type = settings.memos_db_type
            if db_type == "sqlite":
                _db_instance = SQLiteDatabase(db_path=settings.memos_db_path)
            elif db_type == "postgres":
                _db_instance = PostgresDatabase()
            elif db_type == "neo4j":
                _db_instance = Neo4jDatabase()
            else:
                raise ValueError(f"Unsupported database type: {db_type}")
    return _db_instance