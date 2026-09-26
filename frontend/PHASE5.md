# Phase 5 — frontend container

Run all Docker commands from the repository root. Compose command prefix:
`docker compose -f compose.yaml -f compose.frontend.yaml`.
The overlay adds frontend without changing shared compose.yaml. Do not replace
compose.yaml with this overlay. Final dev/prod Compose consolidation is still due.

Files: frontend/Dockerfile, .dockerignore, nginx.conf, docker-entrypoint.sh;
compose.frontend.yaml; scripts/measure_frontend_context.py; runtime ADR.

Checks to execute and retain: frontend tests/lint/build; Compose config validation;
frontend build/start; nginx -t; UID=101; /health through port 8080; /api/stats and
/api/meta/providers through the same port; browser submission and dashboard;
frontend cannot resolve database/cache; runtime has no Node/node_modules/src.
Any failing command must be diagnosed; these checks have not been run by the
package author. The existing error-boundary test deliberately logs a test error.

Collect actual source-context sums with python scripts/measure_frontend_context.py.
This matches the supplied allowlist (update the script if ignore rules change),
but is not Docker's tar transfer size. BuildKit logs show actual transfer bytes,
which can be cache-dependent. Do not transmit an unignored context to measure it:
it could contain secrets. Image inspect .Size reports uncompressed bytes; builder
and runtime image layers may share storage, so their sizes are not additive.

Build the builder target under civicpulse-frontend:builder to inspect it separately.
Run all test commands against the runtime image civicpulse-frontend:dev.
Neither measurement guarantees a passing vulnerability scan. Trivy integration
remains a required later gate. No actual size or scan result is invented here.

AI attribution: ChatGPT/Codex supplied the Docker/nginx integration and documents.
Umar must review and execute the checks and record actual results/changes. Existing
frontend source and dependency lockfile are unchanged by this package.
