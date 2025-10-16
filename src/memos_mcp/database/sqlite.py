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
        Initialize the SQLiteDatabase instance, set up the SQLite engine, create required directories and tables, and prepare a session factory.
        
        Parameters:
            db_path (str): Filesystem path for the SQLite database file. If the environment variable `TESTING` is set, this will be overridden to "test_memory.db".
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
        Define the 'memories' and 'registered_tools' tables on this instance's MetaData.
        
        Creates two Table objects attached to self.metadata:
        - memories: stores persisted agent memories with fields for id, content, agent_id, memory metadata (JSON), optional embedding_id, and created/updated timestamps.
        - registered_tools: stores tool registrations with fields for id, unique name, description, usage instructions, optional tags (JSON), and created/updated timestamps.
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
        
        Yields:
            session (Session): Active SQLAlchemy session; commits the transaction on normal exit, rolls back if an exception occurs, and always closes the session.
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
        Insert a new memory record into the memories table and return its primary key.
        
        Parameters:
            content (str): The textual content of the memory.
            agent_id (str): Identifier of the agent that created the memory.
            metadata (Optional[Dict[str, Any]]): Optional JSON-serializable metadata stored in the memory_metadata column.
        
        Returns:
            Optional[int]: The inserted row's primary key id, or `None` if it could not be determined.
        """
        with self.get_session() as session:
            result = session.execute(
                self.memories.insert().values(
                    content=content, agent_id=agent_id, memory_metadata=metadata
                )
            )
            return result.inserted_primary_key[0]

    def _row_to_dict(self, row: Any, table_name: str) -> Dict[str, Any]:
        """
        Convert a SQLAlchemy row result into a plain dictionary, remapping memory metadata for memories.
        
        Parameters:
            row (Any): A SQLAlchemy row/result object (or falsy) with a `_mapping` attribute.
            table_name (str): Name of the table the row came from; used to apply table-specific renames.
        
        Returns:
            dict: A dictionary of column names to values for the row. If `table_name` is "memories" and the row contains
            the `memory_metadata` key, that key is renamed to `metadata`.
            None: If `row` is falsy.
        """
        if not row:
            return None
    
        d = dict(row._mapping)
        if table_name == "memories" and "memory_metadata" in d:
            d["metadata"] = d.pop("memory_metadata")
        return d

    def get_memory(self, memory_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a memory record by its primary key.
        
        Returns:
            dict: Memory fields with `memory_metadata` renamed to `metadata` if the memory exists, `None` otherwise.
        """
        with self.get_session() as session:
            result = session.execute(
                self.memories.select().where(self.memories.c.id == memory_id)
            ).first()
            return self._row_to_dict(result, "memories")

    def get_memories_by_ids(self, memory_ids: List[int]) -> List[Dict[str, Any]]:
        """
        Retrieve memory rows matching the given IDs.
        
        Parameters:
            memory_ids (List[int]): List of memory primary key IDs to retrieve.
        
        Returns:
            List[Dict[str, Any]]: A list of dictionaries for each matching memory row. Each dictionary contains the row's columns with the database column `memory_metadata` renamed to `metadata`.
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
        Update the embedding_id field of a memory row.
        
        Parameters:
        	memory_id (int): Primary key of the memory to update.
        	embedding_id (str): New embedding identifier to set on the memory.
        
        Returns:
        	bool: True after executing the update.
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
        Insert a new tool into the registered_tools table.
        
        Parameters:
            name (str): Human-readable tool name.
            description (str): Detailed description of what the tool does.
            usage (str): Example or instructions for using the tool.
            tags (Optional[List[str]]): Optional list of tags categorizing the tool.
        
        Returns:
            int or None: The inserted tool's primary key id, or `None` if the id is not available.
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
            dict: A mapping of the tool row's column names to values if found, or `None` if no tool exists with the given id.
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
        Search registered tools for a text fragment in their description or usage and return matching tool records.
        
        Parameters:
            query_context (str): Substring to match against the tool's description or usage (case-insensitive).
            limit (int): Maximum number of results to return.
        
        Returns:
            List[Dict[str, Any]]: A list of dictionaries representing matching tool rows (columns include id, name, description, usage, tags, created_at, updated_at).
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
        Retrieve all registered tools from the database as dictionaries.
        
        Returns:
            List[Dict[str, Any]]: A list of dictionaries where each dictionary represents a row from the `registered_tools` table, mapping column names to their values.
        """
        with self.get_session() as session:
            results = session.execute(self.registered_tools.select()).fetchall()
            return [dict(row._mapping) for row in results]