"""
config.py — Ingestion service settings.

Phase 3 change:
  The ingest service no longer POSTs directly to the API.
  It pushes jobs to a Redis queue instead.
  api_base_url and request_timeout_seconds have been removed.
  redis_url has been added.

Settings:
  REDIS_URL  : Redis connection URL. Read from the shared configs/.env.
               Default: redis://localhost:6379 (local dev).
  LOG_LEVEL  : Logging verbosity (DEBUG | INFO | WARNING | ERROR).
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class IngestSettings(BaseSettings):
    # Redis queue target — jobs are pushed here instead of directly to the API
    redis_url: str = "redis://localhost:6379"

    # Logging verbosity: DEBUG | INFO | WARNING | ERROR
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        # Reads from the shared configs/.env at the monorepo root.
        # Path is relative to where the process is launched (apps/ingest/).
        env_file="../../configs/.env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # silently ignore DB vars, app vars, etc.
    )


# Single shared instance — import this everywhere inside the ingest package.
settings = IngestSettings()
