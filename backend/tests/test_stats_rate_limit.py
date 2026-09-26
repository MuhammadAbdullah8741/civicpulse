import os
from concurrent.futures import ThreadPoolExecutor
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from redis.exceptions import ConnectionError as RedisConnectionError
from sqlalchemy import text

from app.main import app
from app.providers.cache import get_cache
from app.repositories.database import get_engine
from app.services import rate_limit, stats

requires_services = pytest.mark.skipif(
    os.getenv("RUN_DB_TESTS") != "1", reason="Requires PostgreSQL and Redis"
)


@requires_services
def test_stats_miss_hit_ttl_and_invalidation_on_both_writes():
    complaint_id = None
    try:
        with TestClient(app) as client:
            first = client.get("/api/stats")
            assert first.status_code == 200
            assert first.headers["X-Cache"] == "MISS"
            assert 0 < get_cache().ttl(stats.keys()[1]) <= 30
            before = first.json()
            assert sum(before["by_category"].values()) == before["total"]
            assert sum(before["by_priority"].values()) == before["total"]
            assert client.get("/api/stats").headers["X-Cache"] == "HIT"
            created = client.post("/api/complaints", json={
                "text": "Burst water pipe flooding the street.", "location": "Synthetic stats test"
            })
            assert created.status_code == 201
            complaint_id = UUID(created.json()["id"])
            after = client.get("/api/stats")
            assert after.headers["X-Cache"] == "MISS"
            assert after.json()["total"] == before["total"] + 1
            assert after.json()["by_category"]["water"] == before["by_category"]["water"] + 1
            status = client.patch(f"/api/complaints/{complaint_id}/status", json={"status": "in_progress"})
            assert status.status_code == 200
            changed = client.get("/api/stats")
            assert changed.headers["X-Cache"] == "MISS"
            assert changed.json()["by_status"]["in_progress"] == before["by_status"]["in_progress"] + 1
    finally:
        if complaint_id:
            with get_engine().begin() as connection:
                connection.execute(text("DELETE FROM complaints WHERE id=:id"), {"id": complaint_id})


@requires_services
def test_stale_reader_cannot_repopulate_invalidated_cache():
    client = get_cache()
    generation_key, data_key = stats.keys()
    old = str(client.get(generation_key) or "0")
    stats.invalidate()
    client.eval(stats.STORE_IF_CURRENT, 2, generation_key, data_key, old, '{"total":-1}', 30)
    assert client.get(data_key) is None


@requires_services
def test_invalid_cache_value_is_replaced():
    get_cache().setex(stats.keys()[1], 30, '{"nonsense":true}')
    data, state = stats.get_stats()
    assert state == "MISS"
    assert data["total"] >= 0
    assert stats.get_stats()[1] == "HIT"


@requires_services
def test_limiter_is_atomic_under_concurrent_callers(monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_REQUESTS", "3")
    def attempt(_):
        try:
            rate_limit.check("192.0.2.10")
            return True
        except rate_limit.RateLimitExceeded as error:
            assert 1 <= error.retry_after <= 60
            return False
    with ThreadPoolExecutor(max_workers=8) as pool:
        accepted = list(pool.map(attempt, range(12)))
    assert sum(accepted) == 3
    assert 0 < get_cache().ttl(rate_limit.key_for("192.0.2.10")) <= 60
    rate_limit.check("192.0.2.11")
    # Simulate key expiry without a time.sleep-based test.
    get_cache().expire(rate_limit.key_for("192.0.2.10"), 0)
    rate_limit.check("192.0.2.10")


@requires_services
def test_http_429_has_retry_after_and_does_not_save(monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_REQUESTS", "1")
    complaint_id = None
    try:
        with TestClient(app) as client:
            payload = {"text": "Burst water pipe flooding the street.", "location": "Synthetic limit test"}
            created = client.post("/api/complaints", json=payload)
            assert created.status_code == 201
            complaint_id = UUID(created.json()["id"])
            before = client.get("/api/complaints").json()["total"]
            denied = client.post("/api/complaints", json=payload)
            assert denied.status_code == 429
            assert 1 <= int(denied.headers["Retry-After"]) <= 60
            assert client.get("/api/complaints").json()["total"] == before
    finally:
        if complaint_id:
            with get_engine().begin() as connection:
                connection.execute(text("DELETE FROM complaints WHERE id=:id"), {"id": complaint_id})


def test_stats_reads_database_if_redis_unavailable(monkeypatch):
    class BrokenCache:
        def pipeline(self, **kwargs):
            raise RedisConnectionError("Synthetic outage")
    monkeypatch.setattr(stats, "get_cache", lambda: BrokenCache())
    monkeypatch.setattr(stats, "aggregate", lambda: {"total": 7})
    assert stats.get_stats() == ({"total": 7}, "MISS")


def test_rate_limiter_fails_closed_if_redis_unavailable(monkeypatch):
    class BrokenCache:
        def eval(self, *args):
            raise RedisConnectionError("Synthetic outage")
    monkeypatch.setattr(rate_limit, "get_cache", lambda: BrokenCache())
    with TestClient(app) as client:
        response = client.post("/api/complaints", json={
            "text": "Water pipe leaking outside.", "location": "Synthetic Street"
        })
    assert response.status_code == 503
