# Issue and PR: Complete backend caching, rate limiting and observability

Use this title for the new GitHub Issue:
Complete backend statistics, rate limiting and observability

Paste this checklist into the Issue:

- [ ] Add GET /api/stats with counts by category, priority and status.
- [ ] Cache statistics in Redis for 30 seconds and return X-Cache HIT/MISS.
- [ ] Invalidate statistics after complaint creation and status changes.
- [ ] Prevent stale in-flight reads from repopulating the cache after invalidation.
- [ ] Rate-limit complaint creation using atomic Redis counters per client IP.
- [ ] Return HTTP 429 with Retry-After and handle Redis outages deliberately.
- [ ] Add JSON stdout logs and propagated/generated X-Request-ID.
- [ ] Export request, latency, triage and fallback Prometheus metrics.
- [ ] Configure bounded graceful shutdown and close PostgreSQL/Redis clients.
- [ ] Pass deterministic backend tests with coverage at least 65%.
- [ ] Document cache, rate-limiting, proxy and shutdown trade-offs.
- [ ] Pass GitHub CI and complete substantive partner review.

## PR title

feat: complete backend caching rate limiting and observability

## PR body template

### Why
The complaint API needs aggregate statistics, distributed quota protection and
operational visibility before the frontend and Kubernetes deployment are added.

### Changes
Adds Redis-cached statistics with write invalidation, an atomic per-IP limiter,
request-correlated JSON stdout logs, Prometheus metrics and graceful resource
cleanup. Adds isolated integration/unit tests and documents operational limits.

### Verification
Replace this line with actual test count and coverage after running the suite.
Record stats HIT/MISS, request-ID, metrics and shutdown checks actually performed.

### Related Issue
Replace with the new Issue number. Base branch is dev.

Do not tick checks or claim review/CI success before they occur. The proxy trust
configuration and an in-flight rollout demonstration are deferred to the
frontend/Kubernetes phases and are not claimed by this PR.
