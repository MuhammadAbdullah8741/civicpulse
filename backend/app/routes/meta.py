from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from redis.exceptions import RedisError

from app.providers.triage.factory import create_provider
from app.services.triage_cache import provider_metadata

router = APIRouter(prefix="/api/meta", tags=["observability"])


class TriageOutcome(BaseModel):
    provider: str
    latency_ms: int
    fallback: bool
    cache_hit: bool
    timestamp: datetime


class ProviderMetadata(BaseModel):
    active_provider: str
    cache_ttl_seconds: int
    triage_requests: int
    cache_hits: int
    cache_hit_rate: float
    recent_outcomes: list[TriageOutcome]


@router.get("/providers", response_model=ProviderMetadata)
def get_providers():
    try:
        return provider_metadata(create_provider().name)
    except RedisError:
        raise HTTPException(
            status_code=503,
            detail="Provider history unavailable: Redis is unreachable.",
        ) from None
