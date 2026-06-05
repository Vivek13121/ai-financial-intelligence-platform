"""
packages/queue/connection.py — Shared Redis connection factory.

Why a factory function instead of a module-level connection?
  Redis connections are not fork-safe. If we create a connection at
  import time and then fork workers (as rq does internally), the child
  process inherits a broken connection.

  get_redis_connection() creates a fresh connection each time it's called,
  which is safe to call in any process — ingest producer, worker consumer,
  or a future monitoring service.

  redis-py's ConnectionPool handles connection reuse within a single process
  automatically, so calling this multiple times in the same process is cheap.

REDIS_URL format:
  redis://[:password@]host[:port][/db_number]
  e.g. redis://localhost:6379        (no auth, default db)
       redis://:mypassword@localhost:6379/0  (with auth)

  The URL is read from configs/.env via the shared environment variable
  REDIS_URL. Both ingest and worker read the same configs/.env.
"""

import os

import redis


def get_redis_connection() -> redis.Redis:
    """
    Create and return a Redis connection using REDIS_URL from the environment.

    Falls back to redis://localhost:6379 if REDIS_URL is not set,
    which is the correct default for local development.

    decode_responses=False:
      rq stores job data as raw bytes. If decode_responses=True,
      redis-py decodes everything to str, breaking rq's internal
      byte-level serialization. Always use False for rq connections.
    """
    url = os.getenv("REDIS_URL", "redis://localhost:6379")
    return redis.from_url(url, decode_responses=False)
