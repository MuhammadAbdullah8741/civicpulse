# AI assistance record

Tool: ChatGPT/Codex. The assistant supplied substantial implementation code,
PowerShell commands, tests and documentation. The students installed files,
ran commands and supplied terminal output. AI authorship is disclosed; partner
contributions and review must be recorded honestly under their own identities.

## Supplied work

Initial FastAPI setup, Docker and Compose configuration, PostgreSQL/Alembic
schema, seed data, complaint API and state machine, readiness checks, GitHub CI,
triage interface and four providers, retry/fallback, Redis triage caching,
provider-history endpoint, test cases and provider/privacy documentation.

## Changes made during the guided work

- Coverage output moved to /tmp because the non-root container could not write
  its SQLite coverage file in the mounted /app directory on the CI runner.
- Groq model changed from llama-3.1-8b-instant to openai/gpt-oss-20b after an
  actual 404/model_not_found response and account model-list inspection.
- Ollama was initially deferred because of download size, then restored with
  the local-ai profile and persistent volume following the student's decision.
- Cached fallback results are excluded so temporary outages do not suppress
  recovery for 24 hours. CI explicitly selects simulated triage.

## Observed verification from student terminal output

- Initial health test: 1 passed; /health returned status ok.
- Seed inserted 30 rows, repeat inserted zero; Compose down/up preserved rows.
- Complaint API phase: 53 tests passed, approximately 86% coverage.
- Ollama phase: 72 tests passed, 87.63% coverage; live Ollama returned water/high.
- Cache phase: 79 tests passed, 90.08% coverage; controlled duplicate-input hit
  rate 50% (1 hit / 2 requests), provider history endpoint succeeded.

## Pending verification and ownership

Final prompt-injection/transport tests, updated CI and partner review must be
run and their actual results recorded. The team must understand and explain
all generated code at viva. This document does not claim that AI-generated
work was independently written by either partner or that unrun tests passed.

## Backend completion phase (verification pending)

ChatGPT supplied statistics aggregation/cache/invalidation, the Redis Lua limiter,
request-correlated JSON logging, Prometheus metrics, lifespan cleanup, Docker
shutdown configuration and associated tests. The user requested complete file
packages and performs all application execution and GitHub operations themselves.
Only syntax/package inspection was performed by the assistant for this phase.
Record actual test/CI results after running the package; no pass is claimed here.
