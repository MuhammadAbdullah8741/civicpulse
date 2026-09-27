import os
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.main import app
from app.providers.triage.simulated import SimulatedTriage
from app.repositories.database import get_engine
from app.routes.complaints import get_triage_provider


@pytest.mark.skipif(
    os.environ.get("RUN_DB_TESTS") != "1",
    reason="Requires a migrated PostgreSQL database",
)
@pytest.mark.parametrize("mode", ["error", "malformed"])
def test_provider_failure_still_saves_complaint(mode):
    complaint_id = None
    app.dependency_overrides[get_triage_provider] = (
        lambda: SimulatedTriage(mode=mode)
    )

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/complaints",
                json={
                    "text": "Burst water pipe, water entering houses.",
                    "location": "Fallback Test Street",
                },
            )
            assert response.status_code == 201
            data = response.json()
            complaint_id = UUID(data["id"])

            assert data["triaged_by"] == "rules:fallback"
            assert data["category"] == "water"
            assert data["priority"] == "high"

            saved = client.get(f"/api/complaints/{complaint_id}")
            assert saved.status_code == 200
            assert saved.json()["triaged_by"] == "rules:fallback"

    finally:
        app.dependency_overrides.pop(get_triage_provider, None)
        if complaint_id is not None:
            with get_engine().begin() as connection:
                connection.execute(
                    text("DELETE FROM complaints WHERE id = :id"),
                    {"id": complaint_id},
                )
