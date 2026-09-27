# Statistics, rate limiting and observability

## Statistics

GET /api/stats executes one grouped PostgreSQL query through repositories/stats.py,
returning total, by_category, by_priority and by_status (including zero counts).
services/stats.py uses a validated Redis read-through cache, TTL 30 seconds,
with X-Cache HIT/MISS. POST and successful status changes invalidate after commit.
A generation token prevents a read that began before invalidation from writing
its stale result back afterwards. A read already in flight may still return its
snapshot; invalidation cannot retroactively change that response.

TTL limits stale data if invalidation is missed. Explicit invalidation makes
ordinary writes visible on the next read. If Redis is down, statistics query
PostgreSQL directly. Invalidation failure logs a warning; a recovered old cache
may remain stale until its original TTL expires. This is a bounded-staleness
cache, not a distributed transaction between PostgreSQL and Redis.

## Distributed rate limiter

POST /api/complaints accepts 10 validated attempts per client IP per 60-second
window, configurable with RATE_LIMIT_REQUESTS and RATE_LIMIT_WINDOW_SECONDS.
The window begins with that IP's first request. Atomic Lua INCR+EXPIRE keeps
counters consistent across processes/pods and prevents immortal counters.
Rejected calls return HTTP 429 plus Retry-After; they never call the model or
insert rows. Invalid bodies return 400 before consuming the counter. A valid
attempt that later fails can still consume quota. Redis failure returns 503 for
POST to protect the hosted quota; statistics remain available without caching.

Only request.client.host is used. The code does not trust arbitrary client
X-Forwarded-For headers. When nginx/Ingress is added, configure narrowly trusted
proxies before claiming per-end-user limits; otherwise proxied clients share the
proxy address's quota. NAT users also share an IP limit. Authentication-based
quotas and edge protection are future work, outside this demo's current contract.

## Metrics and JSON logs

/metrics exposes civicpulse_requests_total, civicpulse_request_duration_seconds,
civicpulse_triage_duration_seconds and civicpulse_triage_fallback_total.
Histograms include bucket/count/sum series. Labels use route templates and a
bounded provider set, never UUIDs, text or IPs. Metrics are per process; run one
Uvicorn worker per container and scrape each replica in Kubernetes.

logging.json configures JSON stdout at Uvicorn startup. Every application log has
a request_id; accepted X-Request-ID values are 1-80 ASCII letters/digits/._-, or a
UUID is generated. Startup/shutdown logs use system. Request IDs propagate into
sync route threads via contextvars. Each final provider failure emits one WARNING
with complaint ID/provider/error class. No complaint bodies, keys, query strings
or exception bodies are intentionally included. Uvicorn's duplicate access log
is disabled; application middleware emits the request record.

## Graceful shutdown

Uvicorn handles SIGTERM: stop accepting connections, drain requests, then trigger
lifespan cleanup. Docker's exec-form command preserves signal delivery. The
35-second graceful timeout allows two ten-second model attempts plus overhead;
Compose waits 45 seconds before SIGKILL. The lifespan disposes cached SQLAlchemy
pools and closes Redis clients without creating unused clients during shutdown.
These are bounded drain settings, not a guarantee under indefinitely stalled
storage. Development --reload remains enabled; production must omit it.

The lifecycle unit test checks cleanup order. A Docker stop/start and logs can
show shutdown completion, but do not by themselves prove zero dropped in-flight
requests. That separate load/rollout demonstration belongs to the Kubernetes phase.

## Test isolation

conftest.py assigns each test fresh Redis namespaces and deletes only those keys.
Tests cannot consume the developer's rate quota or pollute shared triage history.
Concurrent limiter tests use threads and an atomic Redis operation; expiry is
simulated by expiring the test key, never time.sleep. Integration tests delete
only the complaint UUIDs they created.

## References

- https://redis.io/docs/latest/commands/incr/
- https://www.uvicorn.org/server-behavior/
- https://www.uvicorn.org/settings/
- https://prometheus.github.io/client_python/instrumenting/histogram/

Verification of this phase is pending student execution. Retain actual test,
endpoint and shutdown results before closing its Issue.
