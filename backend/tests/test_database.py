import os
from uuid import uuid4

import pytest
from sqlalchemy import inspect, text
from sqlalchemy.exc import DBAPIError

from app.repositories.database import get_engine

pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_DB_TESTS") != "1",
    reason="Requires a migrated PostgreSQL database",
)


@pytest.fixture
def connection():
    with get_engine().connect() as conn:
        transaction = conn.begin()
        try:
            yield conn
        finally:
            transaction.rollback()


INSERT = text("""
    INSERT INTO complaints (
        id, text, location, category, priority,
        ai_summary, triaged_by, triage_latency_ms
    )
    VALUES (
        :id, :text, :location,
        CAST(:category AS complaint_category),
        CAST(:priority AS complaint_priority),
        :ai_summary, :triaged_by, :triage_latency_ms
    )
    RETURNING status, created_at, updated_at
""")


def valid_complaint():
    return {
        "id": uuid4(),
        "text": "Water pipe is leaking outside the school.",
        "location": "School Road",
        "category": "water",
        "priority": "normal",
        "ai_summary": "Leaking water pipe near the school.",
        "triaged_by": "rules",
        "triage_latency_ms": 2,
    }


def test_database_defaults_and_timezone(connection):
    row = connection.execute(
        INSERT, valid_complaint()
    ).mappings().one()

    assert row["status"] == "open"
    assert row["created_at"].utcoffset() is not None
    assert row["updated_at"].utcoffset() is not None
    assert row["created_at"] == row["updated_at"]


@pytest.mark.parametrize(
    "field,value,expected_sqlstate",
    [
        ("text", "short", "23514"),
        ("text", "x" * 2001, "23514"),
        ("location", "ab", "23514"),
        ("location", "x" * 201, "22001"),
        ("category", "invalid_category", "22P02"),
        ("priority", "urgent", "22P02"),
        ("ai_summary", "x" * 141, "22001"),
        ("ai_summary", "First line\nSecond line", "23514"),
        ("triage_latency_ms", -1, "23514"),
        ("triaged_by", "", "23514"),
    ],
)
def test_database_rejects_invalid_values(
    connection, field, value, expected_sqlstate
):
    complaint = valid_complaint()
    complaint[field] = value

    with pytest.raises(DBAPIError) as error:
        connection.execute(INSERT, complaint)

    assert error.value.orig.sqlstate == expected_sqlstate


def test_required_indexes_exist(connection):
    indexes = {
        index["name"]: index["column_names"]
        for index in inspect(connection).get_indexes("complaints")
    }
    assert indexes["ix_complaints_status_priority"] == ["status", "priority"]
    assert indexes["ix_complaints_created_at"] == ["created_at"]
