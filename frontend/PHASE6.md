# Phase 6: Frontend CI and container integration

The existing CI workflow now has three jobs: Backend tests, Database integration,
and Frontend checks. Existing backend test commands, coverage threshold, and
repeatable seed assertion are retained. PRs targeting dev/main and pushes to dev
run the workflow. No images are published here.

Frontend checks uses Node 22 to match the Docker builder, installs the lockfile
with npm ci, then runs lint/TypeScript, component/client tests, production build,
and npm audit (high or critical findings fail).

Database integration adds compose.frontend.yaml to the existing Compose stack.
It builds both application images, applies migrations, runs backend integration
coverage and seed checks, checks the live OpenAPI contract, verifies frontend UID
101, and runs a smoke test through nginx on port 8080. The smoke test verifies
HTML and its JavaScript asset, JSON endpoints, X-Cache, creation, persistence,
status transitions and a terminal-state 409. This is an HTTP smoke test, not a
browser interaction test. Existing React tests exercise UI behavior separately.

CI uses an ephemeral database and simulated AI with no hosted keys. The optional
Ollama profile stays off. Failure logs are printed before always-on teardown.
`docker compose down -v` belongs to this isolated CI job; do not run it on the
local development stack if its data should be retained.

## Local verification (from repository root)

```powershell
npm --prefix frontend ci
npm --prefix frontend run lint
npm --prefix frontend test
npm --prefix frontend run build
npm --prefix frontend audit --audit-level=high
docker compose -f compose.yaml -f compose.frontend.yaml up -d --build --wait --wait-timeout 180
docker compose exec -T backend alembic upgrade head
npm --prefix frontend run api:check
node frontend/scripts/smoke-container.mjs
```

Default smoke mode reads only. `node frontend/scripts/smoke-container.mjs --write`
adds one synthetic complaint, moves it to resolved, and verifies rejection of a
terminal transition. That record remains in the local database. CI uses this
mode after the repeatable seed assertion, then deletes its temporary volumes.
FRONTEND_URL overrides the frontend smoke URL; OPENAPI_URL overrides the contract
URL. Both default to loopback. Never target a production instance for write smoke.

## Review and evidence

Create a PR into dev, confirm all three jobs pass and obtain substantive partner
review. Add Frontend checks to dev's required checks once GitHub has recorded its
first run. Retain Backend tests and Database integration as required checks.
If documenting a deliberately failing check, use a separate temporary PR and
capture the actual blocked merge before repairing it; do not invent evidence.

This phase does not complete the remaining backend lint/type gates, image
vulnerability scanning, Kubernetes validation, CD/release publishing, deployment,
autoscaling measurements or final submission evidence. Those remain separate
integration work.

AI assistance: Codex prepared these files from the uploaded dev snapshot
561b9bea5474aaada368743797f2b61ad8da613d. Umar must run verification and review
results before merging. No successful GitHub run is asserted by this document.
