import json
import logging

from app.core.extensions import redis_client

logger = logging.getLogger(__name__)


def cache_get(key):
    """Get parsed JSON from Redis. Returns None on miss or error."""
    try:
        value = redis_client.get(key)
        if value:
            return json.loads(value)
    except Exception:
        logger.warning("Redis read failed for key=%s", key, exc_info=True)
    return None


def cache_set(key, data, ttl):
    """Set JSON in Redis with TTL. Silently fails on error."""
    try:
        redis_client.setex(key, ttl, json.dumps(data))
    except Exception:
        logger.warning("Redis write failed for key=%s", key, exc_info=True)
