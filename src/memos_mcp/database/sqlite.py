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
        Initialize a SQLite-backed database connection, create the schema, and prepare a session factory.
        
        If the TESTING environment variable is set, the database path is replaced with "test_memory.db". The constructor creates the parent directory for the database file when applicable, builds the SQLite URL, instantiates a SQLAlchemy engine and metadata, calls _define_tables to declare the schema, creates all tables on the engine, and configures SessionLocal (autocommit=False, autoflush=False) for producing sessions.
        
        Parameters:
            db_path (str): Path to the SQLite database file (defaults to "memory.db").
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
        Define the database schema on the instance metadata by creating two SQL tables: `memories` and `registered_tools`.
        
        - `memories`: stores persisted memory entries with columns:
            - `id`: primary key, auto-incrementing integer.
            - `content`: text payload of the memory.
            - `agent_id`: identifier of the agent that created the memory (defaults to "default_agent").
            - `memory_metadata`: JSON object with arbitrary metadata for the memory.
            - `embedding_id`: optional string reference to an embedding.
            - `created_at`: timestamp set to the current UTC time when the row is created.
            - `updated_at`: timestamp set to the current UTC time when the row is created and updated on modifications.
        
        - `registered_tools`: stores tool registrations with columns:
            - `id`: primary key, auto-incrementing integer.
            - `name`: unique tool name.
            - `description`: textual description of the tool.
            - `usage`: textual usage instructions or examples.
            - `tags`: JSON array or object of tags/metadata.
            - `created_at`: timestamp set to the current UTC time when the row is created.
            - `updated_at`: timestamp set to the current UTC time when the row is created and updated on modifications.
        
        The tables are attached to the instance's SQLAlchemy MetaData as `self.memories` and `self.registered_tools`.
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
        Provide a context-managed SQLAlchemy session.
        
        Yields a SQLAlchemy Session instance for use within a context manager. The session's transaction is committed when the context exits normally; if an exception occurs the transaction is rolled back and the exception is re-raised. The session is closed in all cases.
        
        Returns:
            Session: A managed SQLAlchemy Session instance.
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
        Insert a memory record into the database and return its primary key.
        
        Parameters:
        	content (str): Text content of the memory.
        	agent_id (str): Identifier of the agent associated with the memory.
        	metadata (Optional[Dict[str, Any]]): Arbitrary JSON-serializable metadata to store with the memory.
        
        Returns:
        	memory_id (Optional[int]): The primary key of the inserted memory row, or `None` if the insertion did not produce an ID.
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
        Retrieve a memory by its ID.
        
        If a memory with the given ID exists, returns a dictionary representation of the row where the stored `memory_metadata` column is exposed as the `metadata` key; returns `None` if no matching memory is found.
        
        Returns:
            dict: Memory record with `metadata` key, or `None` if not found.
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
        Retrieve memories with the given IDs from the database.
        
        Parameters:
            memory_ids (List[int]): List of memory primary keys to fetch.
        
        Returns:
            List[Dict[str, Any]]: A list of dictionaries representing each found memory. Each dictionary contains the row fields with `memory_metadata` renamed to `metadata` (e.g., keys include `id`, `content`, `agent_id`, `metadata`, `embedding_id`, `created_at`, `updated_at`).
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
        Set the embedding identifier for an existing memory record.
        
        Parameters:
            memory_id (int): Primary key of the memory to update.
            embedding_id (str): Embedding identifier to assign to the memory.
        
        Returns:
            bool: `True` after the memory's `embedding_id` has been updated.
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
            name (str): Human-readable unique name of the tool.
            description (str): Description of what the tool does.
            usage (str): Example or instructions for using the tool.
            tags (Optional[List[str]]): Optional list of tags categorizing the tool.
        
        Returns:
            tool_id (int | None): The primary key of the newly inserted tool, or `None` if insertion did not produce an id.
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
            dict: A dictionary mapping column names to values for the tool if found, `None` otherwise.
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
        Search registered tools by context and return up to `limit` matching tool records.
        
        Parameters:
            query_context (str): Substring to match against a tool's description or usage (case-insensitive).
            limit (int): Maximum number of matching tools to return.
        
        Returns:
            List[Dict[str, Any]]: A list of matching tool records as dictionaries keyed by column names.
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
            A list of dictionaries where each dictionary represents a tool row with column names as keys and their values as values.
        """
        with self.get_session() as session:
            results = session.execute(self.registered_tools.select()).fetchall()
            return [dict(row._mapping) for row in results]