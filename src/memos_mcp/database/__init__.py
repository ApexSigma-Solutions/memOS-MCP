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
    Create a Database instance based on settings.
    
    Reads `settings.memos_db_type` and, when it is "sqlite", returns an `SQLiteDatabase`
    configured with `settings.memos_db_path`.
    
    Returns:
        Database | None: An `SQLiteDatabase` when `memos_db_type` is "sqlite", `None` otherwise.
    """
    db_type = settings.memos_db_type
    if db_type == "sqlite":
        return SQLiteDatabase(db_path=settings.memos_db_path)
import os
from threading import Lock
from .base import Database
from .sqlite import SQLiteDatabase
from .postgres import PostgresDatabase
from .neo4j import Neo4jDatabase
from ..config import settings

_db_instance = None
_db_lock = Lock()

def get_database() -> Database:
    """
    Get the process-wide singleton Database instance configured from application settings.
    
    If the TESTING environment variable is set, returns an SQLite instance using "test_memory.db".
    Otherwise, selects backend based on settings.memos_db_type: "sqlite" -> SQLiteDatabase(settings.memos_db_path),
    "postgres" -> PostgresDatabase, "neo4j" -> Neo4jDatabase. Raises ValueError for unsupported database types.
    Returns:
        Database: The singleton Database instance.
    """
    global _db_instance
    with _db_lock:
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