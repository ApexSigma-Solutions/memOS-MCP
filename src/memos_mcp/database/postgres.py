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
        Initialize the PostgresDatabase by configuring the connection, creating the SQLAlchemy engine and session factory, and ensuring ORM tables exist.
        
        Reads connection configuration from environment variables: if DATABASE_URL is set it is used directly; otherwise POSTGRES_HOST (default "localhost"), POSTGRES_PORT (default 5432), POSTGRES_DB (default "memos"), POSTGRES_USER (default "apexsigma_user") and POSTGRES_PASSWORD (required) are used to build the Postgres URL. Raises ValueError if POSTGRES_PASSWORD is not provided when DATABASE_URL is not set. Creates the SQLAlchemy engine, a sessionmaker bound to that engine, and invokes metadata.create_all to create any missing tables.
        """
        self.database_url = os.environ.get("DATABASE_URL")
        if not self.database_url:
            self.host = os.environ.get("POSTGRES_HOST", "localhost")
            self.port = int(os.environ.get("POSTGRES_PORT", 5432))
            self.database = os.environ.get("POSTGRES_DB", "memos")
            self.user = os.environ.get("POSTGRES_USER", "apexsigma_user")
            self.password = os.environ.get("POSTGRES_PASSWORD")
            if not self.password:
                raise ValueError("POSTGRES_PASSWORD environment variable must be set.")
            self.database_url = f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"

        self.engine = create_engine(self.database_url, echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        Base.metadata.create_all(bind=self.engine)

    @contextmanager
    def get_session(self) -> Session:
        """
        Provide a transactional SQLAlchemy session context.
        
        Yields a SQLAlchemy Session. The session is committed when the context exits normally, rolled back and the original exception re-raised if an exception occurs, and always closed on exit.
        
        Returns:
            session (Session): A transactional SQLAlchemy Session to use within a `with`-style context.
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
        Create and persist a new Memory record.
        
        Parameters:
        	content (str): Text content to store in the memory.
        	agent_id (str): Identifier of the agent owning the memory.
        	metadata (Optional[Dict[str, Any]]): Optional JSON-serializable metadata associated with the memory.
        
        Returns:
        	int or None: The new memory's database id if created, `None` otherwise.
        """
        with self.get_session() as session:
            memory = Memory(content=content, agent_id=agent_id, memory_metadata=metadata)
            session.add(memory)
            session.flush()
            return memory.id

    def get_memory(self, memory_id: int) -> Optional[Dict[str, Any]]:
        """
        Fetches a stored memory record by its identifier.
        
        Returns:
            A dictionary with keys `id`, `content`, `agent_id`, `metadata`, `embedding_id`, `created_at`, and `updated_at` representing the memory if found; `None` otherwise.
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
        Retrieve memories matching the provided IDs.
        
        Parameters:
            memory_ids (List[int]): IDs of the memories to retrieve.
        
        Returns:
            List[Dict[str, Any]]: A list of dictionaries for each found memory with keys:
                `id`, `content`, `agent_id`, `metadata`, `embedding_id`, `created_at`, `updated_at`.
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
        Update the embedding_id of the Memory with the given id and refresh its updated_at timestamp.
        
        Sets the Memory.embedding_id to the provided value and updates Memory.updated_at to the current UTC time if a memory with the given id exists.
        
        Returns:
            True if the memory was found and updated, False otherwise.
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
        Create and persist a RegisteredTool record.
        
        Parameters:
            name (str): Human-readable tool name (must be unique).
            description (str): Long-form description of what the tool does.
            usage (str): Example or guidance on how the tool is used.
            tags (Optional[List[str]]): Optional list of tags associated with the tool.
        
        Returns:
            int: The database id of the created tool, or `None` if an id was not assigned.
        """
        with self.get_session() as session:
            tool = RegisteredTool(name=name, description=description, usage=usage, tags=tags)
            session.add(tool)
            session.flush()
            return tool.id

    def get_tool(self, tool_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a registered tool by its primary key.
        
        Returns:
            A dictionary containing the tool's fields (`id`, `name`, `description`, `usage`, `tags`, `created_at`, `updated_at`) if a tool with `tool_id` exists, `None` otherwise.
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
        Finds registered tools whose description or usage contains the given query context.
        
        Searches RegisteredTool records for a case-insensitive match of `query_context` within the `description` or `usage`, and returns up to `limit` matching tools as dictionaries.
        
        Parameters:
            query_context (str): Substring to search for in tool description or usage (case-insensitive).
            limit (int): Maximum number of tools to return.
        
        Returns:
            List[Dict[str, Any]]: List of tool dictionaries with keys `id`, `name`, `description`, `usage`, `tags`, `created_at`, and `updated_at`.
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