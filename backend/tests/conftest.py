"""Avoid test traffic consuming the developer's real limiter/cache namespace."""
import os
from uuid import uuid4

import pytest
from redis.exceptions import RedisError

from app.providers.cache import get_cache


@pytest.fixture(autouse=True)
def isolated_redis_namespaces(monkeypatch):
    namespace = "civicpulse:test:suite:" + uuid4().hex
    monkeypatch.setenv("RATE_LIMIT_PREFIX", namespace + ":rate")
    monkeypatch.setenv("STATS_REDIS_PREFIX", namespace + ":stats")
    monkeypatch.setenv("TRIAGE_REDIS_PREFIX", namespace + ":triage")
    monkeypatch.setenv("RATE_LIMIT_REQUESTS", "10")
    monkeypatch.setenv("RATE_LIMIT_WINDOW_SECONDS", "60")
    yield
    if os.getenv("RUN_DB_TESTS") == "1":
        try:
            keys = list(get_cache().scan_iter(match=namespace + ":*"))
            if keys:
                get_cache().delete(*keys)
        except RedisError:
            pass
