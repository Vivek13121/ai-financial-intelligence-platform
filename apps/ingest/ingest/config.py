"""
config.py — Ingestion service settings.

Why a separate config for ingest?
  The ingest service is a standalone process — it does NOT import the backend
  app package. It communicates with the backend exclusively over HTTP (POST
  /api/v1/articles). Having its own config keeps the boundary clean and
  means ingest can be deployed independently on a separate machine later.

Settings loaded here:
  API_BASE_URL : where the backend API is running. Defaults to localhost
                 during development. Override via environment variable or .env.
  REQUEST_TIMEOUT_SECONDS : how long to wait for the API before giving up.
  LOG_LEVEL : controls verbosity of console output.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class IngestSettings(BaseSettings):
    # Backend API target
    api_base_url: str = "http://localhost:8000"

    # HTTP client timeout when POSTing articles to the backend
    request_timeout_seconds: int = 10

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
