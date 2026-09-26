from fastapi import APIRouter, Response

from app.services.stats import StatsResponse, get_stats

router = APIRouter(tags=["statistics"])


@router.get("/api/stats", response_model=StatsResponse)
def statistics(response: Response):
    data, cache_state = get_stats()
    response.headers["X-Cache"] = cache_state
    response.headers["Cache-Control"] = "no-store"
    return data
