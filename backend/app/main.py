from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.routes.complaints import router as complaints_router
from app.routes.health import router as health_router
from app.services.complaints import (
    ComplaintNotFoundError,
    ConcurrentUpdateError,
)
from app.services.status import InvalidTransitionError

app = FastAPI(
    title="CivicPulse API",
    version="0.2.0",
    description="Municipal complaint intake and triage.",
)

app.include_router(health_router)
app.include_router(complaints_router)


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
