from typing import Optional
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    memos_db_type: str = "sqlite"
    memos_db_path: str = "/data/sqlite/memory.db"

    postgres_host: str = "localhost"
    postgres_port: int = 5800
    postgres_db: str = "omega_kg_stable"
    postgres_user: str = "omega_user"
    postgres_password: Optional[str] = None
    postgres_schema: str = "memos"
    
    # PGVector settings
    embedding_dimension: int = 1024
    embedding_model: str = "placeholder"  # Use "bge-m3" or "openai" in production

    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: Optional[str] = None

    fastmcp_server_port: int = 8080
    fastmcp_server_host: str = "0.0.0.0"
    fastmcp_server_log_level: str = "INFO"
    fastmcp_server_transport: str = "sse"

    memos_enable_tool_registry: bool = True
    memos_enable_graph_memory: bool = False
    memos_max_memory_size: int = 1000

    # Better Web Service (BWS) API Configuration
    bws_access_token: Optional[str] = None
    bws_api_key: Optional[str] = None
    bws_api_secret: Optional[str] = None
    bws_base_url: str = "https://api.betterwebservice.com"
    bws_timeout: int = 30

    # BWS Secret IDs (for Bitwarden integration)
    linear_webhook_secret_prd_id: Optional[str] = None
    postgres_password_prd_id: Optional[str] = None
    neo4j_password_prd_id: Optional[str] = None
    linear_api_key_prd_id: Optional[str] = None
    perplexity_api_key_prd_id: Optional[str] = None
    gemini_api_key_prd_id: Optional[str] = None
    nanogpt_omegakg_api_key: Optional[str] = None
    jwt_secret_key_id: Optional[str] = None
    ollama_okg_api_key_prd_id: Optional[str] = None
    hookdeck_api_key_prd_id: Optional[str] = None
    bws_api_key_prd_id: Optional[str] = None
    bws_api_secret_prd_id: Optional[str] = None

    @model_validator(mode="after")
    def check_passwords(self) -> "Settings":
        if self.memos_db_type == "postgres" and not self.postgres_password:
            raise ValueError("POSTGRES_PASSWORD must be set when using PostgreSQL")
        if self.memos_enable_graph_memory and not self.neo4j_password:
            raise ValueError("NEO4J_PASSWORD must be set when graph memory is enabled")
        return self


settings = Settings()
