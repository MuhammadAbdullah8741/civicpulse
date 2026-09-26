# Phase 4 — statistics and triage visibility

Requires GET /api/stats and GET /api/meta/providers on the merged backend.
The statistics endpoint returns total, by_category, by_priority and by_status.
The client reads X-Cache from the real HTTP response; it never guesses HIT from
repeat clicks. Missing or unexpected values display UNKNOWN. Statistics TTL is
30 seconds; triage-result cache TTL is a separate value provided by metadata.
The displayed hit rate is the backend fraction multiplied by 100, not a browser
measurement. Provider history shows latency, fallback, cache use and local time.

Requests run together with independent error handling. If one endpoint fails,
the other panel remains usable. Errors clear only when a refresh begins. The
refresh control is disabled while pending, and unmounted/stale completions are
ignored. Zero totals show zero, not missing data. Stats refresh is manual to make
HIT/MISS demonstrations clear; the complaint dashboard still polls independently.

The OpenAPI snapshot and generated types now cover the two new endpoints.
Run npm run api:check against the backend to confirm contracts before merging.
Do not replace backend files to force a match; inspect any mismatch first.

Checks: npm ci; npm run lint; npm test (expected 33); npm run build; npm audit;
npm run api:check. Application checks must be executed by Umar. Tests mock API
responses and do not require API keys or inference downloads.

Manual: open Statistics, note counts and X-Cache, click Refresh within 30 seconds
without intervening writes to observe HIT. Submit a synthetic complaint, return
to Statistics and verify updated counts. Another statistics reader can consume
the first MISS, so a HIT after a write alone is not proof of failed invalidation.
The backend integration test is the deterministic invalidation check.

AI attribution: ChatGPT/Codex supplied files and proposed tests; Umar reviews,
runs, and records actual modifications and results. No fabricated verification.
