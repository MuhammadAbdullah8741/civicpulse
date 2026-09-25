import os
from functools import lru_cache

from redis import Redis


@lru_cache(maxsize=1)
def get_cache() -> Redis:
    return Redis.from_url(
        os.environ.get("REDIS_URL", "redis://cache:6379/0"),
        decode_responses=True,
        socket_connect_timeout=2,
        socket_timeout=2,
    )


def check_cache() -> None:
    get_cache().ping()
