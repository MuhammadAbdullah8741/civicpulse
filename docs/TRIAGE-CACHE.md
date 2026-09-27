# Triage caching and provider history

## Implementation

`backend/app/services/triage_cache.py` wraps the existing validated retry/fallback
orchestrator. Exact complaint text and location, provider name, model ID and
simulated failure mode form a SHA-256 key. Redis stores validated results for
86,400 seconds. Bump the `v1` namespace if prompt/rule semantics change.

Different locations intentionally do not share a cached classification. This
keeps the interface safe if a future provider uses location. The cache does not
deduplicate complaint records: every valid POST still creates its own record.

Fallback results are not cached under the failed provider. Redis cache or
telemetry failures do not discard an otherwise valid triage result. Invalid
cached values are deleted and recomputed. Concurrent cold requests can each call
the model; single-flight locking is not implemented in this phase.

`GET /api/meta/providers` reports the configured provider, TTL, cumulative counts,
hit fraction and newest 20 outcomes shared across backend processes. Redis
transactions atomically update the list and counters. Counters count completed
triage calls (including calls before a later database failure), not necessarily
persisted complaints. A metadata read returns 503 if Redis is unreachable.

Latency measures triage plus cache work before telemetry recording. The complaint
row's enclosing measurement also includes recording overhead, so the two values
can differ slightly. Cached results retain the original provider name and set
`cache_hit=true` in history. History stores no complaint body or contact details.
SHA-256 hides the input in key names but does not encrypt cached summaries or
prevent guessing predictable input. Redis must stay on the internal network.

## Reproducible measurement

Run the full suite with `-rP` to include successful-test output. The controlled
benchmark submits identical input twice in a unique Redis namespace and asserts:
2 requests, 1 actual provider call, 1 hit, hit rate 0.5 (50%). This is a test
workload, not a claim about real citizen traffic. Treat it as measured only after
the test passes in your environment and retain the terminal output as evidence.
Integration test cleanup deletes only its unique namespace, never shared data.
The endpoint reports a separate cumulative hit rate for application traffic.

Live CPU Ollama inference remains bounded by the existing 10-second transport
limit, with one retry on timeout/429/5xx and rules fallback after failure. CI uses
simulated triage; cache tests require Redis but never an LLM API key or model.
