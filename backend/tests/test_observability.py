import json
import logging

from fastapi.testclient import TestClient
from prometheus_client import REGISTRY

from app.main import app
from app.observability import JsonFormatter, request_id
from app.providers.triage.simulated import SimulatedTriage
from app.services.triage import triage_with_fallback


def test_request_id_propagation_and_validation():
    with TestClient(app) as client:
        response = client.get("/health", headers={"X-Request-ID": "test-request-123"})
        assert response.headers["X-Request-ID"] == "test-request-123"
        generated = client.get("/health", headers={"X-Request-ID": "invalid id"})
        assert generated.headers["X-Request-ID"] != "invalid id"
        assert len(generated.headers["X-Request-ID"]) == 36


def test_metrics_are_exported_with_route_templates():
    with TestClient(app) as client:
        client.get("/health")
        client.get("/api/complaints/not-a-uuid")
        response = client.get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers["Content-Type"]
    assert 'route="/api/complaints/{complaint_id}"' in response.text
    assert "civicpulse_request_duration_seconds_bucket" in response.text
    assert "civicpulse_triage_fallback_total" in response.text


def test_fallback_emits_one_warning_and_increments_counter(caplog):
    before = REGISTRY.get_sample_value("civicpulse_triage_fallback_total") or 0
    with caplog.at_level(logging.WARNING):
        result, provider = triage_with_fallback(
            SimulatedTriage(mode="error"), "Burst water pipe outside.", "Street", "test-observation"
        )
    records = [record for record in caplog.records if record.getMessage() == "triage_fallback"]
    assert len(records) == 1
    assert records[0].complaint_id == "test-observation"
    assert records[0].error_class == "RuntimeError"
    assert provider == "rules:fallback"
    assert REGISTRY.get_sample_value("civicpulse_triage_fallback_total") == before + 1


def test_json_formatter_carries_request_id_and_safe_fields():
    token = request_id.set("formatter-test")
    try:
        record = logging.LogRecord("test", logging.WARNING, "", 1, "triage_fallback", (), None)
        record.complaint_id = "synthetic-id"
        record.provider = "llm:groq"
        record.error_class = "TimeoutError"
        data = json.loads(JsonFormatter().format(record))
        assert data["request_id"] == "formatter-test"
        assert data["provider"] == "llm:groq"
        assert data["error_class"] == "TimeoutError"
        assert "text" not in data
    finally:
        request_id.reset(token)


def test_lifespan_closes_both_resources_after_requests(monkeypatch):
    from app import main
    closed = []
    monkeypatch.setattr(main, "close_database", lambda: closed.append("postgres"))
    monkeypatch.setattr(main, "close_cache", lambda: closed.append("redis"))
    with TestClient(app) as client:
        assert client.get("/health").status_code == 200
        assert closed == []
    assert closed == ["postgres", "redis"]
