from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    memos_db_type: str = "sqlite"
    memos_db_path: str = "/data/sqlite/memory.db"

    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "memos"
    postgres_user: str = "memos_user"
    postgres_password: str = "secure_password"

    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "neo4j_password"

    fastmcp_server_port: int = 8080
    fastmcp_server_host: str = "0.0.0.0"
    fastmcp_server_log_level: str = "INFO"
    fastmcp_server_transport: str = "sse"

    memos_enable_tool_registry: bool = True
    memos_enable_graph_memory: bool = False
    memos_max_memory_size: int = 1000

settings = Settings()
