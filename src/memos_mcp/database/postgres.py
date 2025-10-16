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
        Initialize the PostgresDatabase by configuring the connection URL, creating the SQLAlchemy engine and session factory, and ensuring ORM tables exist.
        
        Reads DATABASE_URL from the environment; if absent, builds the URL from POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB, POSTGRES_USER, and POSTGRES_PASSWORD. Creates an SQLAlchemy engine and a sessionmaker bound to that engine, then creates all tables defined on the declarative Base.
        
        Raises:
            ValueError: If POSTGRES_PASSWORD is not set when DATABASE_URL is not provided.
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
        Provide a context-managed SQLAlchemy Session that commits on successful exit and rolls back on exception.
        
        Returns:
            session (Session): Active SQLAlchemy session; committed when the context exits normally, rolled back if an exception occurs, and closed in all cases.
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
            content (str): Text content of the memory.
            agent_id (str): Identifier of the agent associated with the memory.
            metadata (Optional[Dict[str, Any]]): Optional JSON-serializable metadata for the memory.
        
        Returns:
            Optional[int]: The database ID of the newly created memory, or `None` if the ID could not be obtained.
        """
        with self.get_session() as session:
            memory = Memory(content=content, agent_id=agent_id, memory_metadata=metadata)
            session.add(memory)
            session.flush()
            return memory.id

    def get_memory(self, memory_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a memory entry by its ID.
        
        @returns dict containing memory fields (`id`, `content`, `agent_id`, `metadata`, `embedding_id`, `created_at`, `updated_at`) if found, `None` otherwise.
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
        Fetches memories that match the provided list of memory IDs.
        
        Parameters:
            memory_ids (List[int]): Memory record IDs to retrieve.
        
        Returns:
            List[Dict[str, Any]]: A list of dictionaries for each found memory containing the keys:
                `id`, `content`, `agent_id`, `metadata`, `embedding_id`, `created_at`, and `updated_at`.
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
        Set the embedding identifier for a stored memory.
        
        Parameters:
        	memory_id (int): ID of the memory record to update.
        	embedding_id (str): Embedding identifier to associate with the memory.
        
        Returns:
        	bool: `True` if the memory was found and updated, `False` otherwise.
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
        Register a new tool record in the database.
        
        Parameters:
            name (str): Unique tool name.
            description (str): Detailed description of the tool.
            usage (str): Instructions or examples for using the tool.
            tags (Optional[List[str]]): Optional list of tags to store with the tool (stored as JSON).
        
        Returns:
            tool_id (Optional[int]): The ID of the newly created tool, or `None` if creation failed.
        """
        with self.get_session() as session:
            tool = RegisteredTool(name=name, description=description, usage=usage, tags=tags)
            session.add(tool)
            session.flush()
            return tool.id

    def get_tool(self, tool_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a registered tool by its ID.
        
        Parameters:
            tool_id (int): ID of the registered tool to retrieve.
        
        Returns:
            dict: A mapping with keys `id`, `name`, `description`, `usage`, `tags`, `created_at`, and `updated_at` for the tool if found, `None` otherwise.
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
        Finds registered tools whose description or usage contains the given query text (case-insensitive).
        
        Searches RegisteredTool.description and RegisteredTool.usage with a case-insensitive substring match and returns up to `limit` matching tools.
        
        Parameters:
        	query_context (str): Substring to search for in tool descriptions and usage.
        	limit (int): Maximum number of tools to return. Defaults to 10.
        
        Returns:
        	List[Dict[str, Any]]: A list of dictionaries for matching tools. Each dictionary contains the keys:
        		`id`, `name`, `description`, `usage`, `tags`, `created_at`, and `updated_at`.
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
        Return a list of all registered tools.
        
        Returns:
            A list of dictionaries representing each RegisteredTool with keys `id`, `name`, `description`, `usage`, `tags`, `created_at`, and `updated_at`.
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