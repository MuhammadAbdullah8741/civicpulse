from uuid import NAMESPACE_URL, uuid5

from sqlalchemy import text

from app.repositories.database import get_engine


def seed_complaints(samples: list[dict[str, str]]) -> tuple[int, int]:
    statement = text("""
        INSERT INTO complaints (
            id, text, location, reporter_contact,
            category, priority, status, ai_summary,
            triaged_by, triage_latency_ms
        )
        VALUES (
            :id, :text, :location, NULL,
            CAST(:category AS complaint_category),
            CAST(:priority AS complaint_priority),
            CAST(:status AS complaint_status),
            :ai_summary, 'rules', 0
        )
        ON CONFLICT (id) DO NOTHING
        RETURNING id
    """)

    inserted = 0
    with get_engine().begin() as connection:
        for sample in samples:
            row = dict(sample)
            seed_id = uuid5(
                NAMESPACE_URL,
                "civicpulse:seed:v1:"
                + sample["location"]
                + ":"
                + sample["text"],
            )
            result = connection.execute(
                statement,
                {**row, "id": seed_id},
            )
            if result.scalar_one_or_none() is not None:
                inserted += 1

        total = connection.execute(
            text("SELECT count(*) FROM complaints")
        ).scalar_one()

    return inserted, int(total)
