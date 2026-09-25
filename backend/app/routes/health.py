from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.services.readiness import dependency_status

router = APIRouter()


@router.get("/health", tags=["operations"])
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready", tags=["operations"])
def ready():
    dependencies = dependency_status()
    healthy = all(value == "ok" for value in dependencies.values())

    return JSONResponse(
        status_code=200 if healthy else 503,
        content={
            "status": "ready" if healthy else "not_ready",
            "dependencies": dependencies,
        },
    )
