from functools import lru_cache
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration sourced from environment variables."""

    # Application metadata
    app_name: str = "Document Chat Assistant"
    version: str = "0.1.0"
    debug: bool = False
    log_level: str = "INFO"

    # Security & auth
    secret_key: str = "change-me"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Database configuration
    postgres_url: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/mythai",
        description="SQLAlchemy database URL for PostgreSQL",
    )
    mongodb_url: str = Field(default="mongodb://localhost:27017")
    mongodb_db_name: str = Field(default="mythai")

    # LLM configuration
    gemini_api_key: Optional[str] = None
    gemini_model: str = Field(
        default="gemini-1.5-flash-latest",
        description="Default Google Gemini model identifier",
    )

    # File upload constraints
    max_file_size: int = Field(default=10 * 1024 * 1024, description="Max upload size in bytes")
    allowed_file_types: List[str] = Field(default_factory=lambda: ["application/pdf"])

    # CORS configuration
    allowed_origins: List[str] = Field(default_factory=lambda: ["*"])

    @field_validator("allowed_file_types", mode="before")
    @classmethod
    def parse_allowed_file_types(
        cls, value: str | List[str]
    ) -> List[str]:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_allowed_origins(cls, value: str | List[str]) -> List[str]:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    """Return a cached settings instance."""

    return Settings()
