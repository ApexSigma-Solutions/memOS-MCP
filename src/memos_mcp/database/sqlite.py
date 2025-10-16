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
        Initialize the SQLiteDatabase backend and prepare the SQLAlchemy engine, metadata, tables, and session factory.
        
        If the environment variable `TESTING` is set, the database path is overridden to "test_memory.db". Ensures the directory for the database file exists, creates the SQLite engine and metadata, defines and creates tables, and configures a session factory for producing sessions.
        
        Parameters:
            db_path (str): Filesystem path to the SQLite database file (default: "memory.db").
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
        Define SQLAlchemy Table objects for `memories` and `registered_tools` on this instance's metadata.
        
        Creates:
        - `memories`: stores textual memories with fields for id, content, agent_id, memory_metadata (JSON), embedding_id, created_at, and updated_at.
        - `registered_tools`: stores tool registry entries with fields for id, name, description, usage, tags (JSON), created_at, and updated_at.
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
        
        Returns:
            session (Session): A SQLAlchemy Session instance. The context manager commits the session on successful exit, rolls back on exception, and always closes the session.
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
        Create a new memory record and persist it to the database.
        
        Parameters:
            content (str): The text content of the memory.
            agent_id (str): Identifier of the agent owning the memory.
            metadata (Optional[Dict[str, Any]]): Optional metadata to store; saved to the `memory_metadata` JSON column.
        
        Returns:
            Optional[int]: ID of the newly inserted memory row, or `None` if no ID was produced.
        """
        with self.get_session() as session:
            result = session.execute(
                self.memories.insert().values(
                    content=content, agent_id=agent_id, memory_metadata=metadata
                )
            )
            return result.inserted_primary_key[0]

    def get_memory(self, memory_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a memory record by its ID and return it as a dictionary with `metadata` mapped from the stored `memory_metadata`.
        
        Returns:
            dict: The memory record with table columns as keys and `metadata` containing the JSON metadata, or `None` if no record matches the given `memory_id`.
        """
        with self.get_session() as session:
            result = session.execute(
                self.memories.select().where(self.memories.c.id == memory_id)
            ).first()
            if result:
                row = dict(result._mapping)
                row["metadata"] = row.pop("memory_metadata")
                return row
            return None

    def get_memories_by_ids(self, memory_ids: List[int]) -> List[Dict[str, Any]]:
        """
        Retrieve memories matching the given IDs.
        
        Parameters:
            memory_ids (List[int]): List of memory row IDs to fetch.
        
        Returns:
            List[Dict[str, Any]]: List of dictionaries for each matched memory row. Each dictionary contains the table columns and has the `memory_metadata` column renamed to `metadata`.
        """
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
        Set the embedding_id for the memory record identified by memory_id.
        
        Parameters:
            memory_id (int): ID of the memory row to update.
            embedding_id (str): Embedding identifier to store on the memory row.
        
        Returns:
            bool: `True` after the update statement is executed.
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
        Register a new tool in the database.
        
        Parameters:
            tags (Optional[List[str]]): Optional list of tags associated with the tool.
        
        Returns:
            tool_id (Optional[int]): The newly created tool's primary key ID, or `None` if the insertion did not produce an ID.
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
        Retrieve a registered tool by its ID.
        
        Parameters:
        	tool_id (int): The primary key ID of the tool to retrieve.
        
        Returns:
        	tool (Dict[str, Any] | None): A mapping of the tool's column names to their values, or None if no tool with the given ID exists.
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
        Finds registered tools whose description or usage contains the given context string (case-insensitive), limited to the specified number.
        
        Parameters:
            query_context (str): Substring to search for in tool description or usage.
            limit (int): Maximum number of tools to return.
        
        Returns:
            List[Dict[str, Any]]: A list of tool records as dictionaries for the matched tools.
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
        Retrieve all registered tools from the database.
        
        Returns:
            List[Dict[str, Any]]: A list of tool records where each record maps column names (e.g., id, name, description, usage, tags, created_at, updated_at) to their stored values.
        """
        with self.get_session() as session:
            results = session.execute(self.registered_tools.select()).fetchall()
            return [dict(row._mapping) for row in results]