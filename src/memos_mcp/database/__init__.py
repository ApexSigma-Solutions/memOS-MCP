import os
from .base import Database
from .sqlite import SQLiteDatabase
from .postgres import PostgresDatabase
from .neo4j import Neo4jDatabase
from ..config import settings

_db_instance = None

def get_database() -> Database:
    """
    Provide the application's singleton Database instance configured from the environment and settings.
    
    If the module already holds a cached instance, that instance is returned. When no instance exists, the function:
    - Uses a SQLite database with path "test_memory.db" if the TESTING environment variable is set.
    - Otherwise selects the implementation based on settings.memos_db_type:
      - "sqlite": SQLiteDatabase using settings.memos_db_path
      - "postgres": PostgresDatabase
      - "neo4j": Neo4jDatabase
    
    Returns:
        Database: The application's singleton Database instance.
    
    Raises:
        ValueError: If settings.memos_db_type specifies an unsupported database type.
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