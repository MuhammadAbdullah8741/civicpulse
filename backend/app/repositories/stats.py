from typing import Any

from sqlalchemy import text

from app.repositories.database import get_engine
from app.schemas import Category, Priority, Status


def aggregate() -> dict[str, Any]:
    # A single SQL statement gives every dimension the same snapshot.
    with get_engine().connect() as connection:
        rows = connection.execute(text("""
            SELECT category, priority, status, count(*) AS count
            FROM complaints GROUP BY category, priority, status
        """)).mappings().all()
    result: dict[str, Any] = {
        "total": 0,
        "by_category": dict.fromkeys(Category, 0),
        "by_priority": dict.fromkeys(Priority, 0),
        "by_status": dict.fromkeys(Status, 0),
    }
    for row in rows:
        count = int(row["count"])
        result["total"] += count
        for field in ("category", "priority", "status"):
            result["by_" + field][row[field]] += count
    return result
