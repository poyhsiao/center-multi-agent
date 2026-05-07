"""Redis client and operations."""
import json
from typing import Optional
import redis

from app.config import settings


def get_redis_client() -> redis.Redis:
    """Get Redis client instance."""
    return redis.Redis.from_url(settings.redis_url, decode_responses=True)


def store_refresh_token(
    user_id: str,
    device_id: str,
    jti: str,
    payload: dict,
) -> None:
    """
    Store refresh token in Redis.

    Key pattern: rt:<user_id>:<device_id>
    Stores:
      - jti:<jti>: JSON payload
      - current: current jti
      - created_at: timestamp
    """
    client = get_redis_client()
    key = f"rt:{user_id}:{device_id}"

    import time
    created_at = int(time.time())

    # Store all JTIs for this user+device (keep history for sliding window)
    client.hset(key, f"jti:{jti}", json.dumps(payload))
    client.hset(key, "current", jti)
    client.hset(key, "created_at", created_at)

    # Set expiry on the hash (7 days + buffer)
    client.expire(key, 60 * 60 * 24 * 8)


def get_current_jti(user_id: str, device_id: str) -> Optional[str]:
    """Get the current (most recent) jti for user+device."""
    client = get_redis_client()
    key = f"rt:{user_id}:{device_id}"
    return client.hget(key, "current")


def get_token_payload(user_id: str, device_id: str, jti: str) -> Optional[dict]:
    """Get stored payload for a specific jti."""
    client = get_redis_client()
    key = f"rt:{user_id}:{device_id}"
    data = client.hget(key, f"jti:{jti}")
    if data:
        return json.loads(data)
    return None


def blacklist_refresh_token(jti: str, ttl_seconds: int) -> None:
    """
    Add a refresh token to the blacklist.

    Blacklisted tokens cannot be used for refresh.
    TTL should match remaining token validity.
    """
    client = get_redis_client()
    key = f"blacklist:rt:{jti}"
    client.setex(key, ttl_seconds, "1")


def is_token_blacklisted(jti: str) -> bool:
    """Check if a token is blacklisted."""
    client = get_redis_client()
    key = f"blacklist:rt:{jti}"
    return client.exists(key) == 1


def store_device_registration(
    user_id: str,
    device_id: str,
    fingerprint: str,
    trusted: bool = False,
) -> None:
    """Register or update a device."""
    client = get_redis_client()
    key = f"device:{user_id}:{device_id}"

    import time
    client.hset(key, mapping={
        "fingerprint": fingerprint,
        "trusted": "1" if trusted else "0",
        "last_active": int(time.time()),
    })
    client.expire(key, 60 * 60 * 24 * 30)  # 30 days


def get_device_fingerprint(user_id: str, device_id: str) -> Optional[str]:
    """Get registered fingerprint for a device."""
    client = get_redis_client()
    key = f"device:{user_id}:{device_id}"
    return client.hget(key, "fingerprint")