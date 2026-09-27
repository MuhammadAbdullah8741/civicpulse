# ADR 0001: A replaceable triage provider

Status: accepted for the assignment implementation.

## Context

A remote provider can time out, be rate-limited or return invalid JSON. HTTP
routes and SQL persistence must not depend on any vendor response format.

## Decision

`TriageProvider` in `backend/app/providers/triage/base.py` exposes `name` and
`triage(text, location) -> TriageResult`. `factory.py` selects rules, simulated,
llm (Groq), or ollama using TRIAGE_PROVIDER. Routes obtain this dependency;
services orchestrate caching, validated calls, retry and fallback. Repositories
persist the result without importing a vendor client.

`transport.py` bounds each HTTP call with asyncio.timeout(10) plus httpx timeouts.
`services/triage.py` retries once after 0.1-0.3 seconds of jitter, only for timeout,
429 and 5xx. Authentication, bad requests and validation errors are not retried.
All terminal provider failures use rules and record rules:fallback. This bound
is per attempt, not a ten-second total request budget.

## Consequences

Providers are substitutable and CI needs no API key or model download. Tests
mock the transport and use simulated results; live model accuracy is evaluated
separately. Schema validation enforces shape, enums and bounds, not factual
correctness. Rules can misclassify and hosted/local models remain probabilistic.

Cached results are segregated by provider/model/input and expire after 24 hours.
Fallback is not cached as a successful provider result. Ollama runs behind the
local-ai Compose profile to avoid expensive CI downloads; start it explicitly
for the five-service demonstration. Its named volume preserves model weights.
