from typing import Any
from uuid import UUID

from sqlalchemy import text

from app.repositories.database import get_engine


def create(data: dict[str, Any]) -> dict[str, Any]:
    statement = text("""
        INSERT INTO complaints (
            id, text, location, reporter_contact, category, priority,
            ai_summary, triaged_by, triage_latency_ms
        )
        VALUES (
            :id, :text, :location, :reporter_contact,
            CAST(:category AS complaint_category),
            CAST(:priority AS complaint_priority),
            :ai_summary, :triaged_by, :triage_latency_ms
        )
        RETURNING *
    """)
    with get_engine().begin() as connection:
        return dict(connection.execute(statement, data).mappings().one())


def get(complaint_id: UUID) -> dict[str, Any] | None:
    with get_engine().connect() as connection:
        row = connection.execute(
            text("SELECT * FROM complaints WHERE id = :id"),
            {"id": complaint_id},
        ).mappings().one_or_none()
        return dict(row) if row is not None else None


def list_page(
    category: str | None,
    priority: str | None,
    status: str | None,
    page: int,
    page_size: int,
) -> tuple[list[dict[str, Any]], int]:
    clauses = []
    parameters: dict[str, Any] = {}
    filters = (
        ("category", category, "complaint_category"),
        ("priority", priority, "complaint_priority"),
        ("status", status, "complaint_status"),
    )
    for column, value, enum_type in filters:
        if value is not None:
            clauses.append(f"{column} = CAST(:{column} AS {enum_type})")
            parameters[column] = value

    where = " WHERE " + " AND ".join(clauses) if clauses else ""
    # Column/type names above are fixed constants, never user input.
    with get_engine().connect().execution_options(
        isolation_level="REPEATABLE READ"
    ) as connection:
        with connection.begin():
            total = connection.execute(
                text("SELECT count(*) FROM complaints" + where),
                parameters,
            ).scalar_one()

            rows = connection.execute(
                text(
                    "SELECT * FROM complaints" + where
                    + " ORDER BY created_at DESC, id DESC"
                    + " LIMIT :limit OFFSET :offset"
                ),
                {
                    **parameters,
                    "limit": page_size,
                    "offset": (page - 1) * page_size,
                },
            ).mappings().all()

    return [dict(row) for row in rows], int(total)


def update_status(
    complaint_id: UUID,
    expected_status: str,
    requested_status: str,
) -> dict[str, Any] | None:
    with get_engine().begin() as connection:
        row = connection.execute(
            text("""
                UPDATE complaints
                SET status = CAST(:requested AS complaint_status),
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = :id
                  AND status = CAST(:expected AS complaint_status)
                RETURNING *
            """),
            {
                "id": complaint_id,
                "expected": expected_status,
                "requested": requested_status,
            },
        ).mappings().one_or_none()

    return dict(row) if row is not None else None
