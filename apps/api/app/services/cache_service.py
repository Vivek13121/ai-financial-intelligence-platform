import json
import logging
import redis
from typing import Optional, Any
from app.config import settings

logger = logging.getLogger(__name__)

# Initialize Redis client lazily to avoid startup crashes if Redis is not running
redis_client = None
try:
    if settings.redis_url:
        redis_client = redis.Redis.from_url(settings.redis_url, decode_responses=True)
except Exception as e:
    logger.warning(f"Could not connect to Redis: {e}")

def get_cache(key: str) -> Optional[Any]:
    if not redis_client:
        return None
    try:
        value = redis_client.get(key)
        if value:
            logger.info(f"Cache HIT for key: {key}")
            return json.loads(value)
        logger.info(f"Cache MISS for key: {key}")
        return None
    except Exception as e:
        logger.error(f"Redis get error for key {key}: {e}")
        return None

def set_cache(key: str, value: Any, ttl_seconds: int = 21600) -> None:
    if not redis_client:
        return
    try:
        redis_client.setex(key, ttl_seconds, json.dumps(value))
        logger.info(f"Cache SET for key: {key} with TTL {ttl_seconds}")
    except Exception as e:
        logger.error(f"Redis set error for key {key}: {e}")
