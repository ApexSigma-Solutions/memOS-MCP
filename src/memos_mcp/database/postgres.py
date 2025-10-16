import os
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import JSON, Column, DateTime, Integer, String, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

from .base import Database

Base = declarative_base()


class Memory(Base):
    __tablename__ = "memories"
    id = Column(Integer, primary_key=True, autoincrement=True)
    content = Column(Text, nullable=False)
    agent_id = Column(String(255), nullable=False, default="default_agent")
    memory_metadata = Column(JSON, nullable=True)
    embedding_id = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class RegisteredTool(Base):
    __tablename__ = "registered_tools"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=False)
    usage = Column(Text, nullable=False)
    tags = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PostgresDatabase(Database):
    def __init__(self):
        """
        Initialize the PostgreSQL-backed database connection and ensure ORM tables exist.
        
        Reads DATABASE_URL from the environment or constructs a connection URL from POSTGRES_HOST (default "localhost"), POSTGRES_PORT (default 5432), POSTGRES_DB (default "memos"), POSTGRES_USER (default "apexsigma_user"), and POSTGRES_PASSWORD (default "your_secure_postgres_password_here"); then creates a SQLAlchemy engine and session factory and creates all tables defined on Base metadata.
        """
        self.database_url = os.environ.get("DATABASE_URL")
        if not self.database_url:
            self.host = os.environ.get("POSTGRES_HOST", "localhost")
            self.port = int(os.environ.get("POSTGRES_PORT", 5432))
            self.database = os.environ.get("POSTGRES_DB", "memos")
            self.user = os.environ.get("POSTGRES_USER", "apexsigma_user")
            self.password = os.environ.get("POSTGRES_PASSWORD", "your_secure_postgres_password_here")
            self.database_url = f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"

        self.engine = create_engine(self.database_url, echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        Base.metadata.create_all(bind=self.engine)

    @contextmanager
    def get_session(self) -> Session:
        """
        Provide a transactional SQLAlchemy session as a context manager.
        
        Yields a SQLAlchemy Session for performing database operations. The session is committed when the context block exits normally; if an exception occurs the transaction is rolled back and the exception is re-raised. The session is always closed when the context ends.
        Returns:
            session (Session): An active SQLAlchemy Session yielded for use within the context manager.
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
        Create a Memory record with the given content and agent identifier, persist it, and return its database id.
        
        Parameters:
        	content (str): The textual content of the memory.
        	agent_id (str): Identifier of the agent that owns or created the memory.
        	metadata (Optional[Dict[str, Any]]): Optional arbitrary metadata to associate with the memory.
        
        Returns:
        	Optional[int]: The id of the newly created memory if available, otherwise `None`.
        """
        with self.get_session() as session:
            memory = Memory(content=content, agent_id=agent_id, memory_metadata=metadata)
            session.add(memory)
            session.flush()
            return memory.id

    def get_memory(self, memory_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a memory record by its ID.
        
        Returns:
            dict or None: A dictionary with keys `id`, `content`, `agent_id`, `metadata`, `embedding_id`, `created_at`, and `updated_at` when a memory with the given ID exists, otherwise `None`.
        """
        with self.get_session() as session:
            memory = session.query(Memory).filter(Memory.id == memory_id).first()
            if memory:
                return {
                    "id": memory.id,
                    "content": memory.content,
                    "agent_id": memory.agent_id,
                    "metadata": memory.memory_metadata,
                    "embedding_id": memory.embedding_id,
                    "created_at": memory.created_at,
                    "updated_at": memory.updated_at,
                }
            return None

    def get_memories_by_ids(self, memory_ids: List[int]) -> List[Dict[str, Any]]:
        """
        Fetches memories whose IDs are in `memory_ids` and returns a list of dictionary representations.
        
        Parameters:
            memory_ids (List[int]): Sequence of memory IDs to retrieve. Only existing memories are returned; missing IDs are omitted.
        
        Returns:
            List[Dict[str, Any]]: A list of dictionaries, one per found memory, each containing:
                - `id`: memory primary key
                - `content`: stored text content
                - `agent_id`: associated agent identifier
                - `metadata`: stored memory metadata (JSON) or None
                - `embedding_id`: associated embedding identifier or None
                - `created_at`: creation timestamp (UTC)
                - `updated_at`: last update timestamp (UTC)
        """
        with self.get_session() as session:
            memories = session.query(Memory).filter(Memory.id.in_(memory_ids)).all()
            return [
                {
                    "id": m.id,
                    "content": m.content,
                    "agent_id": m.agent_id,
                    "metadata": m.memory_metadata,
                    "embedding_id": m.embedding_id,
                    "created_at": m.created_at,
                    "updated_at": m.updated_at,
                }
                for m in memories
            ]

    def update_memory_embedding_id(self, memory_id: int, embedding_id: str) -> bool:
        """
        Update the embedding identifier for an existing memory record.
        
        Parameters:
            memory_id (int): Primary key of the memory to update.
            embedding_id (str): New embedding identifier to assign to the memory.
        
        Returns:
            bool: `True` if a memory with `memory_id` was found and updated, `False` otherwise.
        """
        with self.get_session() as session:
            memory = session.query(Memory).filter(Memory.id == memory_id).first()
            if memory:
                memory.embedding_id = embedding_id
                memory.updated_at = datetime.utcnow()
                return True
            return False

    def register_tool(self, name: str, description: str, usage: str, tags: Optional[List[str]] = None) -> Optional[int]:
        """
        Create and persist a RegisteredTool record in the database and return its identifier.
        
        Parameters:
            tags (Optional[List[str]]): Optional list of tag strings to associate with the tool.
        
        Returns:
            int | None: The database id of the newly created tool, or `None` if creation did not succeed.
        """
        with self.get_session() as session:
            tool = RegisteredTool(name=name, description=description, usage=usage, tags=tags)
            session.add(tool)
            session.flush()
            return tool.id

    def get_tool(self, tool_id: int) -> Optional[Dict[str, Any]]:
        """
        Fetch a registered tool by its ID.
        
        Returns:
            A dict containing `id`, `name`, `description`, `usage`, `tags`, `created_at`, and `updated_at` if a tool with `tool_id` exists, `None` otherwise.
        """
        with self.get_session() as session:
            tool = session.query(RegisteredTool).filter(RegisteredTool.id == tool_id).first()
            if tool:
                return {
                    "id": tool.id,
                    "name": tool.name,
                    "description": tool.description,
                    "usage": tool.usage,
                    "tags": tool.tags,
                    "created_at": tool.created_at,
                    "updated_at": tool.updated_at,
                }
            return None

    def get_tools_by_context(self, query_context: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Return registered tools whose description or usage contains the given context string.
        
        Parameters:
            query_context (str): Substring to match against tool descriptions and usage (case-insensitive).
            limit (int): Maximum number of tools to return.
        
        Returns:
            List[Dict[str, Any]]: List of dictionaries for each matching tool containing keys `id`, `name`, `description`, `usage`, `tags`, `created_at`, and `updated_at`.
        """
        with self.get_session() as session:
            tools = (
                session.query(RegisteredTool)
                .filter(
                    (RegisteredTool.description.ilike(f"%{query_context}%"))
                    | (RegisteredTool.usage.ilike(f"%{query_context}%"))
                )
                .limit(limit)
                .all()
            )
            return [
                {
                    "id": t.id,
                    "name": t.name,
                    "description": t.description,
                    "usage": t.usage,
                    "tags": t.tags,
                    "created_at": t.created_at,
                    "updated_at": t.updated_at,
                }
                for t in tools
            ]

    def get_all_tools(self) -> List[Dict[str, Any]]:
        """
        Retrieve all registered tools from the database.
        
        Returns:
            List[Dict[str, Any]]: A list of dictionaries representing registered tools. Each dictionary contains the keys
            `id`, `name`, `description`, `usage`, `tags`, `created_at`, and `updated_at`.
        """
        with self.get_session() as session:
            tools = session.query(RegisteredTool).all()
            return [
                {
                    "id": t.id,
                    "name": t.name,
                    "description": t.description,
                    "usage": t.usage,
                    "tags": t.tags,
                    "created_at": t.created_at,
                    "updated_at": t.updated_at,
                }
                for t in tools
            ]