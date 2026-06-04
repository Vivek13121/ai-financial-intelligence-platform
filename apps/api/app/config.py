"""
config.py — Application settings loaded from environment variables.

Why pydantic-settings?
  - Reads from .env files AND real environment variables automatically.
  - All settings are typed and validated at startup.
  - If a required variable is missing, the app crashes immediately with a
    clear error — far better than a cryptic failure deep inside the code.

How it fits the architecture:
  Every other module imports `settings` from here. There is exactly one
  place where config lives, making it trivial to audit or change.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Database
    database_url: str

    # Application
    app_env: str = "development"
    debug: bool = True

    # API metadata
    app_name: str = "AI Financial Intelligence Platform"
    app_version: str = "0.1.0"

    model_config = SettingsConfigDict(
        # Looks for .env relative to where the process is launched.
        # The canonical location is configs/.env at the monorepo root.
        env_file="../../configs/.env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",   # silently ignore unrecognised vars (e.g. POSTGRES_USER)
    )


# Single shared instance — import this everywhere.
settings = Settings()
