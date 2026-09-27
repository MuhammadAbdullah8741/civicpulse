import pytest
from fastapi.testclient import TestClient
from redis.exceptions import ConnectionError as RedisConnectionError
from sqlalchemy.exc import SQLAlchemyError

from app.main import app
from app.services import readiness


@pytest.mark.parametrize(
    "postgres_ok,redis_ok,expected_status",
    [
        (True, True, 200),
        (False, True, 503),
        (True, False, 503),
        (False, False, 503),
    ],
)
def test_readiness_reports_dependencies(
    monkeypatch, postgres_ok, redis_ok, expected_status
):
    def database_probe():
        if not postgres_ok:
            raise SQLAlchemyError("Database unavailable")

    def cache_probe():
        if not redis_ok:
            raise RedisConnectionError("Redis unavailable")

    monkeypatch.setattr(readiness, "check_database", database_probe)
    monkeypatch.setattr(readiness, "check_cache", cache_probe)

    with TestClient(app) as client:
        response = client.get("/ready")
        health = client.get("/health")

    assert response.status_code == expected_status
    assert response.json()["dependencies"] == {
        "postgres": "ok" if postgres_ok else "unavailable",
        "redis": "ok" if redis_ok else "unavailable",
    }
    assert health.status_code == 200
    assert health.json() == {"status": "ok"}
