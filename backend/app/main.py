import logging
import re
from contextlib import asynccontextmanager
from time import perf_counter
from uuid import uuid4

from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from redis.exceptions import RedisError
from sqlalchemy.exc import SQLAlchemyError
from starlette.responses import Response

from app.observability import LATENCY, REQUESTS, request_id
from app.providers.cache import close_cache
from app.repositories.database import close_database
from app.routes.stats import router as stats_router
from app.services.rate_limit import RateLimitExceeded

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.routes.complaints import router as complaints_router
from app.routes.health import router as health_router
from app.routes.meta import router as meta_router
from app.services.complaints import (
    ComplaintNotFoundError,
    ConcurrentUpdateError,
)
from app.services.status import InvalidTransitionError

@asynccontextmanager
async def lifespan(app):
    # Uvicorn drains requests before triggering lifespan shutdown.
    try:
        yield
    finally:
        try:
            close_database()
        finally:
            close_cache()
        logging.getLogger(__name__).info("resources_closed")


app = FastAPI(
    lifespan=lifespan,
    title="CivicPulse API",
    version="0.3.0",
    description="Municipal complaint intake and triage.",
)

app.include_router(health_router)
app.include_router(complaints_router)
app.include_router(meta_router)
app.include_router(stats_router)


@app.exception_handler(RequestValidationError)
async def validation_error(
    request: Request, exc: RequestValidationError
):
    return JSONResponse(
        status_code=400,
        content={
            "detail": "Validation failed",
            "errors": [
                {
                    "field": ".".join(str(part) for part in error["loc"]),
                    "message": error["msg"],
                    "type": error["type"],
                }
                for error in exc.errors()
            ],
        },
    )


@app.exception_handler(ComplaintNotFoundError)
async def not_found(request: Request, exc: ComplaintNotFoundError):
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(InvalidTransitionError)
async def invalid_transition(request: Request, exc: InvalidTransitionError):
    return JSONResponse(status_code=409, content={"detail": str(exc)})


@app.exception_handler(ConcurrentUpdateError)
async def concurrent_update(request: Request, exc: ConcurrentUpdateError):
    return JSONResponse(status_code=409, content={"detail": str(exc)})


@app.middleware("http")
async def observe_request(request: Request, call_next):
    supplied = request.headers.get("X-Request-ID", "")
    rid = supplied if re.fullmatch(r"[A-Za-z0-9._-]{1,80}", supplied) else str(uuid4())
    token = request_id.set(rid)
    started = perf_counter()
    status = 500
    try:
        response = await call_next(request)
        status = response.status_code
        response.headers["X-Request-ID"] = rid
        return response
    finally:
        route = getattr(request.scope.get("route"), "path", "unmatched")
        method = request.method if request.method in {"GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS", "HEAD"} else "OTHER"
        elapsed = perf_counter() - started
        REQUESTS.labels(method, route, str(status)).inc()
        LATENCY.labels(method, route).observe(elapsed)
        logging.getLogger(__name__).info("http_request", extra={
            "method": method, "route": route, "status": status,
            "latency_ms": round(elapsed * 1000),
        })
        request_id.reset(token)


@app.exception_handler(RateLimitExceeded)
async def limited(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "Too many complaints; try again later."},
        headers={"Retry-After": str(exc.retry_after)},
    )


@app.exception_handler(RedisError)
async def redis_unavailable(request: Request, exc: RedisError):
    return JSONResponse(status_code=503, content={"detail": "Redis unavailable; retry shortly."})


@app.exception_handler(SQLAlchemyError)
async def database_unavailable(request: Request, exc: SQLAlchemyError):
    return JSONResponse(status_code=503, content={"detail": "Database unavailable; retry shortly."})


@app.get("/metrics", include_in_schema=False)
def metrics():
    return Response(generate_latest(), headers={"Content-Type": CONTENT_TYPE_LATEST})
