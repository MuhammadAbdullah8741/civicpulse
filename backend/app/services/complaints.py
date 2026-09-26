from time import perf_counter
from typing import Any
from uuid import UUID, uuid4

from app.providers.triage.base import TriageProvider
from app.repositories import complaints as repository
from app.schemas import ComplaintCreate, ComplaintResponse, Status
from app.services.status import allowed_transitions, validate_transition
from app.services.triage_cache import triage_with_cache


class ComplaintNotFoundError(Exception):
    pass


class ConcurrentUpdateError(Exception):
    pass


def as_response(row: dict[str, Any]) -> ComplaintResponse:
    return ComplaintResponse(
        **row,
        allowed_transitions=allowed_transitions(Status(row["status"])),
    )


def create(
    payload: ComplaintCreate, provider: TriageProvider
) -> ComplaintResponse:
    started = perf_counter()
    complaint_id = uuid4()
    result, triaged_by = triage_with_cache(
        provider, payload.text, payload.location, str(complaint_id)
    )
    latency = max(0, round((perf_counter() - started) * 1000))

    row = repository.create({
        **payload.model_dump(),
        "id": complaint_id,
        "category": result.category.value,
        "priority": result.priority.value,
        "ai_summary": result.summary,
        "triaged_by": triaged_by,
        "triage_latency_ms": latency,
    })
    return as_response(row)


def get(complaint_id: UUID) -> ComplaintResponse:
    row = repository.get(complaint_id)
    if row is None:
        raise ComplaintNotFoundError("Complaint not found")
    return as_response(row)


def list_page(category, priority, status, page: int, page_size: int):
    rows, total = repository.list_page(
        category, priority, status, page, page_size
    )
    return {
        "items": [as_response(row) for row in rows],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


def change_status(
    complaint_id: UUID, requested: Status
) -> ComplaintResponse:
    existing = get(complaint_id)
    validate_transition(existing.status, requested)

    updated = repository.update_status(
        complaint_id, existing.status.value, requested.value
    )
    if updated is None:
        raise ConcurrentUpdateError(
            "Complaint status changed; refresh the complaint and retry."
        )
    return as_response(updated)

