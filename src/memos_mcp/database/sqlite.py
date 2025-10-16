import os
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Integer,
    String,
    Text,
    create_engine,
    MetaData,
    Table,
)
from sqlalchemy.orm import sessionmaker, Session
from .base import Database

class SQLiteDatabase(Database):
    def __init__(self, db_path: str = "memory.db"):
        """
        Initialize the SQLiteDatabase: prepare the filesystem path, create the SQLite engine and metadata, define and create required tables, and initialize the session factory.
        
        Parameters:
            db_path (str): Filesystem path to the SQLite database file. If the environment variable `TESTING` is set, this will be overridden to "test_memory.db".
        """
        if os.environ.get("TESTING"):
            db_path = "test_memory.db"

        db_dir = os.path.dirname(db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)

        self.database_url = f"sqlite:///{db_path}"
        self.engine = create_engine(self.database_url, echo=False)
        self.metadata = MetaData()
        self._define_tables()
        self.metadata.create_all(bind=self.engine)
        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )

    def _define_tables(self):
        """
        Define the SQLAlchemy table objects used by this SQLiteDatabase instance.
        
        Creates and assigns two Table objects on self:
        - self.memories: stores persisted memory entries with columns for id, content, agent_id, memory_metadata, embedding_id, created_at, and updated_at.
        - self.registered_tools: stores tool registrations with columns for id, name, description, usage, tags, created_at, and updated_at.
        
        Both tables use self.metadata for their MetaData and include automatic timestamp columns for creation and last update.
        """
        self.memories = Table(
            "memories",
            self.metadata,
            Column("id", Integer, primary_key=True, autoincrement=True),
            Column("content", Text, nullable=False),
            Column("agent_id", String(255), nullable=False, default="default_agent"),
            Column("memory_metadata", JSON, nullable=True),
            Column("embedding_id", String(255), nullable=True),
            Column("created_at", DateTime, default=datetime.utcnow),
            Column("updated_at", DateTime, default=datetime.utcnow, onupdate=datetime.utcnow),
        )

        self.registered_tools = Table(
            "registered_tools",
            self.metadata,
            Column("id", Integer, primary_key=True, autoincrement=True),
            Column("name", String(255), nullable=False, unique=True),
            Column("description", Text, nullable=False),
            Column("usage", Text, nullable=False),
            Column("tags", JSON, nullable=True),
            Column("created_at", DateTime, default=datetime.utcnow),
            Column("updated_at", DateTime, default=datetime.utcnow, onupdate=datetime.utcnow),
        )

    @contextmanager
    def get_session(self) -> Session:
        """
        Provide a transactional SQLAlchemy session as a context manager.
        
        Yields a SQLAlchemy Session for performing database operations. The transaction is committed when the context exits normally, rolled back if an exception occurs, and the session is always closed.
        
        Returns:
            Session: The active SQLAlchemy session yielded to the context.
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def store_memory(self, content: str, agent_id: str, metadata: Optional[Dict[str, Any]] = None) -> Optional[int]:
        """
        Insert a memory record and return its primary key.
        
        Parameters:
        	content (str): The textual content of the memory.
        	agent_id (str): Identifier of the agent associated with the memory.
        	metadata (Optional[Dict[str, Any]]): Optional metadata stored in the `memory_metadata` JSON column.
        
        Returns:
        	int | None: The inserted memory's primary key ID, or `None` if the insertion did not produce an ID.
        """
        with self.get_session() as session:
            result = session.execute(
                self.memories.insert().values(
                    content=content, agent_id=agent_id, memory_metadata=metadata
                )
            )
            return result.inserted_primary_key[0]

    def _row_to_dict(self, row: Any, table_name: str) -> Dict[str, Any]:
        if not row:
            return None
    
        d = dict(row._mapping)
        if table_name == "memories" and "memory_metadata" in d:
            d["metadata"] = d.pop("memory_metadata")
        return d

    def get_memory(self, memory_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a stored memory by its ID.
        
        If found, returns a dictionary of the memory row where the database column `memory_metadata` is renamed to `metadata`.
        
        Parameters:
            memory_id (int): Primary key of the memory to retrieve.
        
        Returns:
            dict or None: A dictionary representing the memory (with `metadata`), or `None` if no matching row exists.
        """
        with self.get_session() as session:
            result = session.execute(
                self.memories.select().where(self.memories.c.id == memory_id)
            ).first()
            return self._row_to_dict(result, "memories")

    def get_memories_by_ids(self, memory_ids: List[int]) -> List[Dict[str, Any]]:
        """
        Retrieve memories matching the provided IDs.
        
        Parameters:
            memory_ids (List[int]): List of memory primary key IDs to fetch.
        
        Returns:
            List[Dict[str, Any]]: A list of memory records as dictionaries. Each dictionary contains the row fields with `memory_metadata` renamed to `metadata`. If no rows match, an empty list is returned.
        """
        if not memory_ids:
            return []
        with self.get_session() as session:
            results = session.execute(
                self.memories.select().where(self.memories.c.id.in_(memory_ids))
            ).fetchall()
            output = []
            for row in results:
                new_row = dict(row._mapping)
                new_row["metadata"] = new_row.pop("memory_metadata")
                output.append(new_row)
            return output

    def update_memory_embedding_id(self, memory_id: int, embedding_id: str) -> bool:
        """
        Update the embedding identifier for a memory record.
        
        Parameters:
        	memory_id (int): Primary key of the memory to update.
        	embedding_id (str): New embedding identifier to set on the memory.
        
        Returns:
        	bool: `True` if the update operation was executed.
        """
        with self.get_session() as session:
            session.execute(
                self.memories.update()
                .where(self.memories.c.id == memory_id)
                .values(embedding_id=embedding_id)
            )
            return True

    def register_tool(self, name: str, description: str, usage: str, tags: Optional[List[str]] = None) -> Optional[int]:
        """
        Register a new tool in the database and return its primary key.
        
        Parameters:
            name (str): Tool name (must be unique).
            description (str): Detailed description of the tool.
            usage (str): Example or explanation of how the tool is used.
            tags (Optional[List[str]]): Optional list of tags categorizing the tool.
        
        Returns:
            Optional[int]: The inserted tool's primary key ID, or `None` if the ID is unavailable.
        """
        with self.get_session() as session:
            result = session.execute(
                self.registered_tools.insert().values(
                    name=name, description=description, usage=usage, tags=tags
                )
            )
            return result.inserted_primary_key[0]

    def get_tool(self, tool_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a registered tool by its primary key.
        
        Returns:
            dict: The tool row as a dictionary keyed by column names, or `None` if no matching tool is found.
        """
        with self.get_session() as session:
            result = session.execute(
                self.registered_tools.select().where(
                    self.registered_tools.c.id == tool_id
                )
            ).first()
            return dict(result._mapping) if result else None

    def get_tools_by_context(self, query_context: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Return tools whose description or usage contains the provided query context (case-insensitive).
        
        Parameters:
        	query_context (str): Substring to search for in the tool `description` or `usage` fields; matching is case-insensitive.
        	limit (int): Maximum number of tools to return.
        
        Returns:
        	List[Dict[str, Any]]: A list of dictionaries, each representing a row from the `registered_tools` table (columns such as `id`, `name`, `description`, `usage`, `tags`, `created_at`, `updated_at`, etc.).
        """
        with self.get_session() as session:
            results = session.execute(
                self.registered_tools.select()
                .where(
                    (self.registered_tools.c.description.ilike(f"%{query_context}%"))
                    | (self.registered_tools.c.usage.ilike(f"%{query_context}%"))
                )
                .limit(limit)
            ).fetchall()
            return [dict(row._mapping) for row in results]

    def get_all_tools(self) -> List[Dict[str, Any]]:
        """
        Return all registered tools stored in the database as dictionaries keyed by column name.
        
        Returns:
            List[Dict[str, Any]]: A list where each item is a dictionary representing a registered tool row with keys such as `id`, `name`, `description`, `usage`, `tags`, `created_at`, and `updated_at`.
        """
        with self.get_session() as session:
            results = session.execute(self.registered_tools.select()).fetchall()
            return [dict(row._mapping) for row in results]