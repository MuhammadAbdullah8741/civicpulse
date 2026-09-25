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
