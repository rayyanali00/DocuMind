from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "INFO"

    # DB
    database_url: str = "sqlite+aiosqlite:///./data/documind.db"

    # Redis / Celery
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # Storage
    upload_dir: Path = Path("./data/uploads")
    storage_dir: Path = Path("./data/storage")
    max_upload_size_mb: int = Field(default=100, ge=1)

    # Vector / BM25
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "documind_chunks"
    opensearch_url: str = "http://localhost:9200"
    opensearch_index: str = "documind_chunks"

    # Models
    embedding_model: str = "BAAI/bge-large-en-v1.5"
    embedding_dim: int = 1024
    reranker_model: str = "BAAI/bge-reranker-large"

    # Chunking
    chunk_buffer_size: int = 1
    chunk_breakpoint_percentile: int = 95

    # Retrieval
    retrieval_top_k: int = 30
    rerank_top_n: int = 10
    cache_ttl_seconds: int = 1800

    # OCR
    tesseract_lang: str = "eng"

    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024

    def ensure_dirs(self) -> None:
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.storage_dir.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.ensure_dirs()
    return settings
