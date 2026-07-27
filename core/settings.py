"""
Centralized application settings.

All runtime configuration is sourced from environment variables or an
optional .env file.  Module-level algorithm parameters (scoring weights,
thresholds, model names) remain in their own ``config.py`` files; those
are tuning knobs, not deployment parameters.

Usage
-----
    from core.settings import get_settings

    settings = get_settings()
    print(settings.log_level)        # "INFO"
    print(settings.is_production)    # False

The singleton is cached after the first call.  To reload settings in
tests, call ``get_settings.cache_clear()`` before re-invoking.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application-level runtime settings.

    Pydantic validates every field at construction time, so a
    misconfigured deployment fails immediately rather than silently
    producing wrong results at runtime.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",        # unknown env vars are silently ignored
        populate_by_name=True,
    )

    # ── Application identity ───────────────────────────────────────────────────
    app_name:    str = "Resume Parser System"
    app_version: str = "1.0.0"
    environment: Literal["development", "staging", "production"] = "development"
    debug:       bool = False

    # ── Logging ────────────────────────────────────────────────────────────────
    log_level:        Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    log_format:       Literal["json", "text"] = "text"
    log_file:         Optional[str] = None
    log_max_bytes:    int = Field(default=10_485_760, gt=0)   # 10 MB
    log_backup_count: int = Field(default=5, ge=0)

    # ── File processing ────────────────────────────────────────────────────────
    max_upload_size_mb: int   = Field(default=10, gt=0, le=100)
    temp_dir:           str   = "/tmp/resume_parser"          # noqa: S108

    # ── Embedding model ────────────────────────────────────────────────────────
    # Override at deployment time to pin a specific model version.
    embedding_model_name: str = "all-MiniLM-L6-v2"
    embedding_cache_size: int = Field(default=1024, gt=0)
    embedding_batch_size: int = Field(default=32,   gt=0)

    # ── Streamlit server ───────────────────────────────────────────────────────
    server_port:             int  = Field(default=8501, ge=1024, le=65535)
    server_headless:         bool = True
    server_enable_xsrf:      bool = True
    server_max_upload_mb:    int  = Field(default=10, gt=0)

    # ── Validators ────────────────────────────────────────────────────────────

    @field_validator("log_level", mode="before")
    @classmethod
    def _normalise_log_level(cls, v: str) -> str:
        return str(v).upper()

    # ── Computed properties ───────────────────────────────────────────────────

    @property
    def is_production(self) -> bool:
        """True when running in the production environment."""
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        """True when running in the development environment."""
        return self.environment == "development"

    @property
    def max_upload_bytes(self) -> int:
        """Maximum permitted upload size in bytes."""
        return self.max_upload_size_mb * 1_048_576


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Return the application settings singleton.

    The instance is constructed once and cached for the process lifetime.
    In tests, clear the cache with ``get_settings.cache_clear()`` before
    each test that needs custom settings.

    Example::

        def test_custom_log_level(monkeypatch):
            monkeypatch.setenv("LOG_LEVEL", "DEBUG")
            get_settings.cache_clear()
            settings = get_settings()
            assert settings.log_level == "DEBUG"
    """
    return Settings()
