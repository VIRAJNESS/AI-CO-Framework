"""12-factor configuration for the AI engine.

Every environment-specific value is injected via environment variables with
local-safe defaults, so the service runs out-of-the-box with zero cloud keys
(LLM_PROVIDER=mock, STORAGE_PROVIDER=local).
"""

from enum import Enum
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class StorageProviderName(str, Enum):
    LOCAL = "local"
    S3 = "s3"
    AZURE_BLOB = "azure_blob"
    GCS = "gcs"


class LLMProviderName(str, Enum):
    MOCK = "mock"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    AZURE_OPENAI = "azure_openai"
    BEDROCK = "bedrock"
    VERTEX = "vertex"


class Settings(BaseSettings):
    """Application settings, resolved once at startup (cached)."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "ai-engine"
    version: str = "0.1.0"

    # Provider switches (cloud-agnostic)
    storage_provider: StorageProviderName = StorageProviderName.LOCAL
    llm_provider: LLMProviderName = LLMProviderName.MOCK

    # Persistence
    db_url: str = "postgresql+psycopg://aicoach:aicoach_local_dev@localhost:5432/aicoach"
    redis_url: str = "redis://localhost:6379/0"

    # Object storage (S3-compatible — MinIO locally)
    s3_endpoint: str = "http://localhost:9000"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_bucket: str = "ai-coach-artifacts"

    # Local filesystem storage root (STORAGE_PROVIDER=local)
    local_storage_path: str = "./artifacts"


@lru_cache
def get_settings() -> Settings:
    """Cached settings accessor — use as a FastAPI dependency."""
    return Settings()
