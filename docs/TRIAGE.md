# AI triage operation and validation

| TRIAGE_PROVIDER | Implementation | Recorded name |
|---|---|---|
| llm | Hosted Groq, openai/gpt-oss-20b by default | llm:groq |
| ollama | Local llama3.2:1b by default | llm:ollama |
| rules | Deterministic keyword classifier | rules |
| simulated | Deterministic CI provider with failure injection | simulated |

Provider failure records rules:fallback. Set TRIAGE_PROVIDER in .env and
recreate the backend after changes. `docker compose exec -e TRIAGE_PROVIDER=...`
changes only that command's environment, not the running API's default.

## Local Ollama

Start `docker compose --profile local-ai up -d --wait ollama`, then
`docker compose exec ollama ollama pull llama3.2:1b`. Warm with
`docker compose exec ollama ollama run llama3.2:1b "Reply with just OK."`.
The app always keeps its ten-second per-attempt deadline. A slow cold start can
fall back; do not lengthen the deadline merely to hide it. `ollama_models`
persists weights. Use `docker compose stop ollama` when not testing local AI.

## Hosted model and limits

The earlier llama-3.1-8b-instant request returned HTTP 404/model_not_found for
this account. Its models endpoint listed openai/gpt-oss-20b, which succeeded.
This is why model selection is environment-configurable rather than assumed.
Groq's rate-limit documentation is https://console.groq.com/docs/rate-limits .
Exact account limits must be recorded from the team's console before submission;
no unverified request/token quota is claimed here. Do not include keys in evidence.

## Guardrails and test interpretation

Complaint text is JSON-delimited as untrusted data after a separate system
instruction. Groq requests JSON mode; Ollama requests a JSON schema. Pydantic
validates category, priority, summary length/single-line format and confidence.
No model output is executed or interpolated into SQL.

`test_prompt_injection.py` POSTs malicious complaint text through the real API
and persistence path with a mocked hosted response. It checks prompt separation,
contact redaction and both a valid result and an out-of-schema category that
must trigger rules fallback. This deterministic test demonstrates enforcement;
it does not prove a live LLM cannot be semantically manipulated within the enum.

`test_transport.py` verifies the ten-second deadline and cancellation without
sleeping. Existing retry tests prove exact attempt counts for errors. Existing
fallback tests prove HTTP 201 and persistence when a provider fails.

## Observed verification before this final AI test phase

User-provided Windows Docker output on 26 September 2026:
- Phase 1: 72 passed, statement coverage 87.63%; live llm:ollama returned water/high.
- Phase 2: 79 passed, statement coverage 90.08%.
- Controlled cache benchmark: 2 calls, 1 provider execution, 1 hit, 50% hit rate.
- Metadata endpoint: simulated default, TTL 86400, latest outcomes and latencies.

Final tests and GitHub CI/partner review are pending. Capture their actual
results; do not treat the expected test count as evidence. See TRIAGE-CACHE.md
for measurement scope and ADRs 0001/0004 for provider and privacy trade-offs.
