"""
Application configuration using Pydantic Settings.
All values are loaded from environment variables or a .env file.
Never commit secrets — use .env.example as the template.
"""
import os
from functools import lru_cache
from typing import Literal
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Don't load .env file in production — use platform env vars (Render, Railway, etc.)
_ENV_FILE = ".env" if os.environ.get("APP_ENV", "development") != "production" else None


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_ENV_FILE,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────────────────────
    app_env: Literal["development", "production", "test"] = "development"
    app_secret_key: str = Field(
        default="change-me-in-production-minimum-32-characters",
        min_length=32,
    )
    app_allowed_origins: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000"

    @property
    def allowed_origins(self) -> list[str]:
        return [o.strip() for o in self.app_allowed_origins.split(",")]

    # ── Database ─────────────────────────────────────────────────────────────
    database_url: str = "sqlite+aiosqlite:///./edupulse_v2.db"
    database_pool_size: int = 10
    database_max_overflow: int = 20

    @property
    def async_database_url(self) -> str:
        """Ensure asyncpg driver prefix for PostgreSQL URLs (Render gives plain postgresql://)."""
        url = self.database_url
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgres://"):   # Some providers use this alias
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        return url

    @property
    def sync_database_url(self) -> str:
        """Synchronous URL for Alembic migrations."""
        url = self.async_database_url
        return url.replace("postgresql+asyncpg://", "postgresql+psycopg2://")

    # ── Redis ────────────────────────────────────────────────────────────────
    redis_url: str = "redis://localhost:6379/0"

    # ── JWT ──────────────────────────────────────────────────────────────────
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    # ── LLM ──────────────────────────────────────────────────────────────────
    openai_api_key: str = ""
    llm_model: str = "gpt-4o-mini"
    llm_max_tokens: int = 2048
    llm_temperature: float = 0.3
    llm_enabled: bool = True

    # ── Anonymization ────────────────────────────────────────────────────────
    hmac_secret: str = Field(min_length=16, default="change-me-hmac-secret-minimum16")
    k_anonymity_threshold: int = 8

    # ── Rate Limiting ────────────────────────────────────────────────────────
    rate_limit_feedback_per_hour: int = 10
    rate_limit_auth_per_minute: int = 5
    rate_limit_api_per_minute: int = 60

    # ── Scoring Parameters ───────────────────────────────────────────────────
    scoring_alpha: float = 0.70
    scoring_bayes_k: int = 8
    scoring_winsor_low: int = 5
    scoring_winsor_high: int = 95
    temporal_cluster_window_hours: int = 24
    temporal_cluster_threshold: float = 0.5

    # ── Logging ──────────────────────────────────────────────────────────────
    log_level: str = "INFO"
    log_format: Literal["json", "pretty"] = "pretty"

    @field_validator("scoring_alpha")
    @classmethod
    def validate_alpha(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError("scoring_alpha must be between 0.0 and 1.0")
        return v


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance — call this everywhere instead of instantiating directly."""
    return Settings()
