from fastapi import FastAPI

from app.routes.health import router as health_router

app = FastAPI(
    title="CivicPulse API",
    version="0.1.0",
    description="Municipal complaint intake and triage.",
)

app.include_router(health_router)
