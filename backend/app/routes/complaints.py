from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.providers.triage.rules import RuleBasedTriage
from app.schemas import (
    Category,
    ComplaintCreate,
    ComplaintPage,
    ComplaintResponse,
    Priority,
    Status,
    StatusUpdate,
)
from app.services import complaints as service

router = APIRouter(prefix="/api/complaints", tags=["complaints"])


def get_triage_provider() -> RuleBasedTriage:
    return RuleBasedTriage()


@router.post("", response_model=ComplaintResponse, status_code=201)
def create_complaint(
    payload: ComplaintCreate,
    provider: Annotated[RuleBasedTriage, Depends(get_triage_provider)],
):
    return service.create(payload, provider)


@router.get("", response_model=ComplaintPage)
def list_complaints(
    category: Category | None = None,
    priority: Priority | None = None,
    status: Status | None = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
):
    return service.list_page(category, priority, status, page, page_size)


@router.get("/{complaint_id}", response_model=ComplaintResponse)
def get_complaint(complaint_id: UUID):
    return service.get(complaint_id)


@router.patch("/{complaint_id}/status", response_model=ComplaintResponse)
def update_complaint_status(complaint_id: UUID, payload: StatusUpdate):
    return service.change_status(complaint_id, payload.status)
