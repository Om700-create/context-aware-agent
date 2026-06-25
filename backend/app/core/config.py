"""
Centralized application configuration.
All values are overridable via environment variables / .env file.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "Context-Aware Conversational AI Platform"
    ENV: str = "development"
    DEBUG: bool = True

    # Database - defaults to local SQLite so the project runs with zero setup.
    # Swap to a Postgres URL (e.g. postgresql+psycopg2://user:pass@host/db) in production.
    DATABASE_URL: str = "sqlite:///./app.db"

    # Vector store (local, file-based Chroma - no server required)
    CHROMA_PERSIST_DIR: str = "./chroma_data"
    CHROMA_COLLECTION: str = "documents"

    # LLM configuration - pluggable. The platform works with ANY of these:
    # 1) Ollama running locally (set LLM_PROVIDER=ollama)
    # 2) An OpenAI-compatible API (set LLM_PROVIDER=openai + OPENAI_API_KEY)
    # 3) No LLM configured at all (set LLM_PROVIDER=offline) - uses deterministic
    #    extractive answers so the demo still fully works end-to-end.
    LLM_PROVIDER: str = "offline"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen3:8b"
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_MODEL: str = "gpt-4o-mini"

    EMBEDDING_PROVIDER: str = "local"  # local = hashing-based offline embedder (no downloads needed)

    UPLOAD_DIR: str = "./app/uploads"
    MAX_UPLOAD_MB: int = 25

    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    SECRET_KEY: str = "change-me-in-production-please"

    RATE_LIMIT: str = "60/minute"


settings = Settings()
