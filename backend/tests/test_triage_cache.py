import os
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from redis.exceptions import ConnectionError as RedisConnectionError

from app.main import app
from app.providers.cache import get_cache
from app.providers.triage.rules import RuleBasedTriage
from app.providers.triage.simulated import SimulatedTriage
from app.services import triage_cache


@pytest.fixture
def isolated_cache(monkeypatch):
    if os.environ.get("RUN_DB_TESTS") != "1":
        pytest.skip("Requires Redis integration environment")
    namespace = "civicpulse:test:triage:" + uuid4().hex
    monkeypatch.setenv("TRIAGE_REDIS_PREFIX", namespace)
    monkeypatch.setenv("TRIAGE_PROVIDER", "simulated")
    yield namespace
    keys = list(get_cache().scan_iter(match=namespace + ":*"))
    if keys:
        get_cache().delete(*keys)


class CountingProvider:
    name = "test-counting"

    def __init__(self):
        self.calls = 0

    def triage(self, text, location):
        self.calls += 1
        return RuleBasedTriage().triage(text, location)


def test_duplicate_uses_cache_and_measures_hit_rate(isolated_cache):
    provider = CountingProvider()
    args = (provider, "Burst water pipe flooding the street.", "Synthetic Street", "test-id")
    first = triage_cache.triage_with_cache(*args)
    second = triage_cache.triage_with_cache(*args)
    assert first == second
    assert provider.calls == 1
    key = triage_cache.cache_key(*args[:3])
    assert 0 < get_cache().ttl(key) <= 86400
    meta = triage_cache.provider_metadata(provider.name)
    assert meta["triage_requests"] == 2
    assert meta["cache_hits"] == 1
    assert meta["cache_hit_rate"] == 0.5
    assert meta["recent_outcomes"][0]["cache_hit"] is True
    print("Controlled cache benchmark: requests=2, provider_calls=1, hits=1, hit_rate=50%")


def test_fallback_is_not_cached_and_history_is_bounded(isolated_cache):
    provider = SimulatedTriage(mode="error")
    args = (provider, "Burst water pipe flooding the street.", "Synthetic Street", "test-id")
    for _ in range(22):
        _, actual = triage_cache.triage_with_cache(*args)
        assert actual == "rules:fallback"
    assert get_cache().get(triage_cache.cache_key(*args[:3])) is None
    meta = triage_cache.provider_metadata(provider.name)
    assert meta["triage_requests"] == 22
    assert meta["cache_hits"] == 0
    assert len(meta["recent_outcomes"]) == 20
    assert all(row["fallback"] for row in meta["recent_outcomes"])


def test_invalid_cached_output_is_recomputed(isolated_cache):
    provider = CountingProvider()
    args = (provider, "Burst water pipe flooding the street.", "Synthetic Street", "test-id")
    key = triage_cache.cache_key(*args[:3])
    get_cache().setex(key, 60, '{"category":"unicorn"}')
    result, actual = triage_cache.triage_with_cache(*args)
    assert result.category.value == "water"
    assert actual == provider.name
    assert provider.calls == 1
    assert triage_cache.provider_metadata(provider.name)["cache_hits"] == 0


def test_cache_key_separates_models_and_locations(monkeypatch):
    class Provider:
        name = "llm:ollama"
    provider = Provider()
    monkeypatch.setenv("OLLAMA_MODEL", "model-a")
    first = triage_cache.cache_key(provider, "Complaint body", "Street A")
    monkeypatch.setenv("OLLAMA_MODEL", "model-b")
    assert triage_cache.cache_key(provider, "Complaint body", "Street A") != first
    monkeypatch.setenv("OLLAMA_MODEL", "model-a")
    assert triage_cache.cache_key(provider, "Complaint body", "Street B") != first
    assert "Complaint body" not in first


def test_redis_outage_does_not_block_triage(monkeypatch):
    class UnavailableCache:
        def get(self, *args):
            raise RedisConnectionError("Synthetic outage")
        def setex(self, *args):
            raise RedisConnectionError("Synthetic outage")
        def pipeline(self, **kwargs):
            raise RedisConnectionError("Synthetic outage")
    monkeypatch.setattr(triage_cache, "get_cache", lambda: UnavailableCache())
    result, actual = triage_cache.triage_with_cache(
        SimulatedTriage(), "Burst water pipe flooding the street.", "Test Street", "test-id"
    )
    assert actual == "simulated"
    assert result.category.value == "water"


def test_provider_history_endpoint(isolated_cache):
    triage_cache.triage_with_cache(
        SimulatedTriage(), "Burst water pipe flooding the street.", "Test Street", "test-id"
    )
    with TestClient(app) as client:
        response = client.get("/api/meta/providers")
    assert response.status_code == 200
    body = response.json()
    assert body["active_provider"] == "simulated"
    assert body["cache_ttl_seconds"] == 86400
    assert body["triage_requests"] == 1
    assert body["recent_outcomes"][0]["latency_ms"] >= 0
    assert body["recent_outcomes"][0]["fallback"] is False


def test_provider_history_returns_503_on_redis_outage(monkeypatch):
    from app.routes import meta
    def unavailable(active_provider):
        raise RedisConnectionError("Synthetic outage")
    monkeypatch.setattr(meta, "provider_metadata", unavailable)
    with TestClient(app) as client:
        response = client.get("/api/meta/providers")
    assert response.status_code == 503
    assert "Redis" in response.json()["detail"]
