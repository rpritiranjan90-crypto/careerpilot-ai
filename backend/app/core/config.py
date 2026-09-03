"""Application configuration loaded from environment variables and .env file."""

from __future__ import annotations

from typing import Any
import json
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable override."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Core
    app_name: str = "CareerPilot AI"
    environment: str = Field(default="development")
    debug: bool = Field(default=False)

    @model_validator(mode="after")
    def _validate_production_safety(self) -> Settings:
        """Refuse to start in production with dangerous configuration."""
        if self.environment == "production":
            if self.dev_token_auth:
                raise ValueError(
                    "FATAL: DEV_TOKEN_AUTH cannot be enabled in production. "
                    "Set DEV_TOKEN_AUTH=false in your production environment."
                )
            if not self.supabase_jwt_secret:
                raise ValueError(
                    "FATAL: SUPABASE_JWT_SECRET is not set. "
                    "A valid JWT secret is required in production."
                )
            if not self.database_url:
                raise ValueError(
                    "FATAL: DATABASE_URL is not set. "
                    "A database is required in production."
                )
        return self

    # CORS - comma separated origins or JSON array in env
    cors_origins: Any = Field(default_factory=lambda: ["http://localhost:3000"])

    # Supabase / Database
    supabase_url: str = Field(default="")
    supabase_anon_key: str = Field(default="")
    supabase_service_role_key: str = Field(default="")
    supabase_jwt_secret: str = Field(default="")
    database_url: str = Field(default="")
    # Postgres schema to use for CareerPilot tables. Defaults to "careerpilot"
    # so the app can share a Supabase project with other apps without colliding
    # in the public schema. Set to "public" to use the default schema.
    db_schema: str = Field(default="careerpilot")

    # Dev-only fallback: if true and no JWT secret is configured, accept
    # a "Bearer <user_id>" token. NEVER enable in production.
    dev_token_auth: bool = Field(default=False)

    # AI provider (Ollama)
    ollama_base_url: str = Field(default="http://localhost:11434")
    ollama_model: str = Field(default="llama3.2:3b")
    ollama_timeout: int = Field(default=120)

    # Groq cloud AI (free tier — https://console.groq.com)
    # If set, Groq is used instead of Ollama.
    # Get your key from: https://console.groq.com/keys
    groq_api_key: str = Field(default="")
    groq_model: str = Field(default="llama-3.1-8b-instant")

    # File uploads
    upload_dir: str = Field(default="./uploads")
    max_upload_size_mb: int = Field(default=5)
    allowed_extensions: Any = Field(
        default_factory=lambda: ["pdf", "docx", "txt"]
    )

    # Rate limiting (per user per hour)
    rate_limit_analyze: int = Field(default=20)
    rate_limit_interview: int = Field(default=30)

    # Security
    api_key_header: str = "X-API-Key"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_origins(cls, v: object) -> list[str]:
        """Allow comma separated list in env vars."""
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                try:
                    parsed = json.loads(v)
                    if isinstance(parsed, list):
                        return [str(item).strip() for item in parsed if str(item).strip()]
                except Exception:
                    pass
            return [item.strip() for item in v.split(",") if item.strip()]
        if isinstance(v, (list, tuple, set)):
            return [str(item).strip() for item in v if str(item).strip()]
        return ["http://localhost:3000"]

    @field_validator("allowed_extensions", mode="before")
    @classmethod
    def _split_ext(cls, v: object) -> list[str]:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                try:
                    parsed = json.loads(v)
                    if isinstance(parsed, list):
                        return [str(item).strip().lower() for item in parsed if str(item).strip()]
                except Exception:
                    pass
            return [item.strip().lower() for item in v.split(",") if item.strip()]
        if isinstance(v, (list, tuple, set)):
            return [str(item).strip().lower() for item in v if str(item).strip()]
        return ["pdf", "docx", "txt"]


settings = Settings()
