import hashlib
import os

from app.providers.cache import get_cache

# Counter and TTL are updated atomically in Redis, shared by every replica.
SCRIPT = """
local count = redis.call('INCR', KEYS[1])
if count == 1 then redis.call('EXPIRE', KEYS[1], ARGV[1]) end
return {count, redis.call('TTL', KEYS[1])}
"""


class RateLimitExceeded(Exception):
    def __init__(self, retry_after: int):
        self.retry_after = retry_after


def key_for(ip: str) -> str:
    prefix = os.getenv("RATE_LIMIT_PREFIX", "civicpulse:rate:v1")
    return prefix + ":" + hashlib.sha256(ip.encode()).hexdigest()


def check(ip: str) -> None:
    limit = max(1, int(os.getenv("RATE_LIMIT_REQUESTS", "10")))
    window = max(1, int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60")))
    count, ttl = get_cache().eval(SCRIPT, 1, key_for(ip), window)
    if int(count) > limit:
        raise RateLimitExceeded(max(1, int(ttl)))
