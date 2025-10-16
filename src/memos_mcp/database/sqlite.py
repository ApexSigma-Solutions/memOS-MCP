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
        Initialize the SQLite-based persistence backend, configure the SQLAlchemy engine and metadata, define and create required tables, and prepare the session factory.
        
        Parameters:
            db_path (str): Filesystem path to the SQLite database file. If the environment variable `TESTING` is set, the path is overridden to `"test_memory.db"`. The containing directory will be created if it does not exist.
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
        Define and attach SQLAlchemy Table metadata for the instance.
        
        Creates two tables on self.metadata:
        - memories: id, content, agent_id, memory_metadata, embedding_id, created_at, updated_at.
        - registered_tools: id, name, description, usage, tags, created_at, updated_at.
        
        These table objects are assigned to self.memories and self.registered_tools.
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
        Provide a transactional SQLAlchemy session scoped to a context block.
        
        The yielded session is committed when the context exits normally, rolled back and the original exception re-raised if an exception occurs, and always closed on exit.
        
        Returns:
            session (Session): A `Session` instance opened for the duration of the context.
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
        Create and persist a memory record.
        
        Parameters:
            content (str): The textual content of the memory.
            agent_id (str): Identifier of the agent owning the memory.
            metadata (Optional[Dict[str, Any]]): Optional metadata stored under the `memory_metadata` column.
        
        Returns:
            inserted_id (Optional[int]): The primary key of the newly inserted memory, or `None` if insertion did not produce an id.
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
        Convert a SQLAlchemy result row into a plain dictionary and normalize the metadata key for memory rows.
        
        Parameters:
        	row (Any): A SQLAlchemy result row or mapping; may be falsy to indicate no result.
        	table_name (str): The originating table name; when equal to "memories", `memory_metadata` will be renamed to `metadata`.
        
        Returns:
        	dict | None: A dictionary built from the row's mapping with `memory_metadata` renamed to `metadata` for memory rows, or `None` if `row` is falsy.
        """
        if not row:
            return None
    
        d = dict(row._mapping)
        if table_name == "memories" and "memory_metadata" in d:
            d["metadata"] = d.pop("memory_metadata")
        return d

    def get_memory(self, memory_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a memory by its id.
        
        Returns:
            dict: The memory record as a dictionary (with `metadata` key if present), or `None` if no row matches `memory_id`.
        """
        with self.get_session() as session:
            result = session.execute(
                self.memories.select().where(self.memories.c.id == memory_id)
            ).first()
            return self._row_to_dict(result, "memories")

    def get_memories_by_ids(self, memory_ids: List[int]) -> List[Dict[str, Any]]:
        """
        Retrieve memory records for the given memory IDs.
        
        Parameters:
            memory_ids (List[int]): Primary key IDs of the memories to fetch.
        
        Returns:
            List[Dict[str, Any]]: A list of memory records as dictionaries. Each record includes all stored columns and uses the key `metadata` (renamed from `memory_metadata`).
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
        Set the embedding identifier for a memory record.
        
        Parameters:
            memory_id (int): Primary key of the memory to update.
            embedding_id (str): Identifier to store in the memory's `embedding_id` column.
        
        Returns:
            bool: `True` after the update.
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
        Register a tool and persist its metadata.
        
        Parameters:
            name (str): Unique tool name.
            description (str): Human-readable description of the tool.
            usage (str): Example or instructions describing how to use the tool.
            tags (Optional[List[str]]): Optional list of tags associated with the tool.
        
        Returns:
            tool_id (int): The primary key of the newly registered tool if insertion succeeded, `None` otherwise.
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
        
        Parameters:
            tool_id (int): The primary key ID of the tool to fetch.
        
        Returns:
            Optional[Dict[str, Any]]: A dictionary mapping column names to their values for the tool if found, `None` otherwise.
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
        Finds registered tools whose description or usage contains the given query text (case-insensitive).
        
        Parameters:
            query_context (str): Text to match against the tool's description and usage (substring, case-insensitive).
            limit (int): Maximum number of tools to return.
        
        Returns:
            List[Dict[str, Any]]: A list of dictionaries for matching tools; each dictionary contains the tool table's columns (e.g., id, name, description, usage, tags, created_at, updated_at).
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
            List[Dict[str, Any]]: A list of dictionaries representing each tool row; keys correspond to the columns of the `registered_tools` table.
        """
        with self.get_session() as session:
            results = session.execute(self.registered_tools.select()).fetchall()
            return [dict(row._mapping) for row in results]