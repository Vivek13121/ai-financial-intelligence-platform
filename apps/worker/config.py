"""
worker/config.py — Worker service settings.

Why a separate config for the worker?
  The worker has different concerns from the ingest service:
    - It needs DATABASE_URL to connect to PostgreSQL directly.
    - It needs REDIS_URL to connect to the queue.
    - It does NOT need RSS feed URLs or HTTP client settings.

  Keeping each service's config scoped to what it actually needs makes
  it obvious what each service depends on — useful when deploying to
  separate machines in production.

Settings:
  DATABASE_URL  : PostgreSQL connection URL (same as backend API).
                  The worker writes directly to the DB — no HTTP roundtrip.
  REDIS_URL     : Redis connection URL for rq to listen on.
  LOG_LEVEL     : Logging verbosity.
  WORKER_BURST  : If True, worker exits after queue is empty (useful for
                  testing). If False, worker runs indefinitely.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class WorkerSettings(BaseSettings):
    # PostgreSQL — worker writes articles directly to the DB
    database_url: str

    # Redis — worker listens for jobs here
    redis_url: str = "redis://localhost:6379"

    # Logging verbosity: DEBUG | INFO | WARNING | ERROR
    log_level: str = "INFO"

    # burst mode: process all queued jobs then exit (True = useful for tests)
    worker_burst: bool = False

    model_config = SettingsConfigDict(
        # Same shared configs/.env as the API and ingest services.
        # Path is relative to where the process is launched (apps/worker/).
        env_file="../../configs/.env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = WorkerSettings()
