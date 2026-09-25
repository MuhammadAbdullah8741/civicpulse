# AI assistance record

## Initial project setup

Tool: ChatGPT.

ChatGPT supplied PowerShell setup commands, the initial FastAPI application,
the health endpoint, its pytest test, and the initial GitHub Actions workflow.

The health endpoint has no database dependency to meet the assignment's
liveness requirement.

Student verification and subsequent changes:
Pending execution and review. Update this section with actual test results,
changes made, and the reasons for those changes.

Verification:
- Ran the health endpoint test inside a Python 3.12 Docker container.
- Result: 1 passed.
- Started the backend and confirmed /health returned {"status":"ok"}.
- GitHub Actions verification is pending.

## Database and Compose implementation

ChatGPT supplied the initial Compose configuration, backend Dockerfile,
database connection module, Alembic migration, synthetic seed complaints,
database tests, and CI database job.

Verified locally:
- Migration reached 0001 (head).
- First seed inserted 30 complaints.
- Repeating the seed inserted zero additional complaints.
- All 30 complaints survived Compose down/up.

Database test and CI results will be recorded after execution.
