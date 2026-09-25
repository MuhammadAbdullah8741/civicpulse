import os
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.main import app
from app.repositories.database import get_engine


@pytest.mark.parametrize(
    "payload,field",
    [
        ({"text": "short", "location": "Street 12"}, "body.text"),
        (
            {"text": "Water pipe leaking outside.", "location": "ab"},
            "body.location",
        ),
        (
            {
                "text": "Water pipe leaking outside.",
                "location": "Street 12",
                "priority": "high",
            },
            "body.priority",
        ),
    ],
)
def test_invalid_complaint_returns_field_level_400(payload, field):
    with TestClient(app) as client:
        response = client.post("/api/complaints", json=payload)

    assert response.status_code == 400
    assert field in {
        error["field"] for error in response.json()["errors"]
    }


def test_page_size_above_limit_returns_400():
    with TestClient(app) as client:
        response = client.get("/api/complaints?page_size=101")
    assert response.status_code == 400


@pytest.mark.skipif(
    os.environ.get("RUN_DB_TESTS") != "1",
    reason="Requires a migrated PostgreSQL database",
)
def test_complaint_lifecycle_against_postgres():
    complaint_id = None
    try:
        with TestClient(app) as client:
            created = client.post(
                "/api/complaints",
                json={
                    "text": "Burst water pipe, water entering houses.",
                    "location": "Integration Test Street",
                },
            )
            assert created.status_code == 201
            data = created.json()
            complaint_id = UUID(data["id"])

            assert data["category"] == "water"
            assert data["priority"] == "high"
            assert data["status"] == "open"
            assert data["triaged_by"] == "rules"
            assert data["triage_latency_ms"] >= 0

            path = f"/api/complaints/{complaint_id}"
            fetched = client.get(path)
            assert fetched.status_code == 200
            assert fetched.json() == data

            listing = client.get(
                "/api/complaints",
                params={
                    "category": "water",
                    "priority": "high",
                    "status": "open",
                    "page_size": 100,
                },
            )
            assert listing.status_code == 200
            items = listing.json()["items"]
            assert all(
                item["category"] == "water"
                and item["priority"] == "high"
                and item["status"] == "open"
                for item in items
            )

            changed = client.patch(
                path + "/status", json={"status": "in_progress"}
            )
            assert changed.status_code == 200
            assert changed.json()["status"] == "in_progress"

            invalid = client.patch(
                path + "/status", json={"status": "open"}
            )
            assert invalid.status_code == 409
            assert invalid.json()["detail"] == (
                "Invalid status transition: in_progress -> open"
            )
            assert client.get(path).json()["status"] == "in_progress"

            resolved = client.patch(
                path + "/status", json={"status": "resolved"}
            )
            assert resolved.status_code == 200
            assert resolved.json()["allowed_transitions"] == []

            assert client.get(
                f"/api/complaints/{uuid4()}"
            ).status_code == 404

    finally:
        if complaint_id is not None:
            with get_engine().begin() as connection:
                connection.execute(
                    text("DELETE FROM complaints WHERE id = :id"),
                    {"id": complaint_id},
                )
