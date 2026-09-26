# Production Compose rehearsal

Development uses `compose.yaml`: builds both application images and mounts backend
source for hot reload. The earlier compose.frontend.yaml overlay remains compatible
but is no longer needed to start the complete development application.

Production uses ONLY `compose.prod.yaml`. Do not combine it with compose.yaml:
merging would reintroduce build settings, source mounts and backend host ports.
The project is civicpulse-prod and the local frontend URL is http://localhost:8081.
Development remains civicpulse on port 8080, with separate database/Redis volumes.
This is a local deployment rehearsal; it is not an internet deployment with TLS.

## Images and configuration

Commit the phase files, then dot-source scripts/Prepare-Production.ps1 from
PowerShell. It requires a clean Git working tree, sets IMAGE_TAG=sha-<full commit>,
resolves installed PostgreSQL 16 and Redis 7 images to registry digests, and builds
backend/frontend images with that commit tag. An absent data image is pulled.
Application images are built before deployment; the production file has no build
keys. Tags identify the source commit by convention; registries can still overwrite
tags. CD will later publish and record image digests for stronger artifact identity.
A clean working tree does not include ignored files; Docker ignore files must
continue excluding environment files, credentials and generated dependency folders.

The script sets TRIAGE_PROVIDER=simulated for reproducible smoke tests without AI
API charges. .env supplies the existing POSTGRES_DB/USER/PASSWORD. It is not edited
or committed by this phase. Shell environment values override .env. Keep using the
same PowerShell session for subsequent commands. In a new session, re-run the
preparation script, or restore the recorded non-secret image variables.

Required deployment variables:
- IMAGE_TAG: sha- followed by the full 40-character Git commit.
- POSTGRES_IMAGE and REDIS_IMAGE: registry image references ending in @sha256:digest.
- POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD: supplied from the ignored .env.
- BACKEND_IMAGE_REPOSITORY / FRONTEND_IMAGE_REPOSITORY: default local names;
  use published GHCR repository names in a later deployment.
- FRONTEND_PORT: defaults to 8081, bound to host loopback.

Optional hosted settings remain GROQ_API_KEY, GROQ_MODEL and TRIAGE_PROVIDER=llm.
The backend joins edge for outbound hosted requests and internal for DB/Redis.
The frontend joins edge only; DB/Redis join only the internal network. Backend,
DB and Redis have no published host ports. Application filesystems are read-only
with writable /tmp, dropped capabilities and no-new-privileges. Image users remain
10001 (backend) and 101 (frontend). PostgreSQL and Redis retain their official
image startup behavior and write only their named data volumes.

The optional local-ai profile retains Ollama and its persistent model volume.
It is not activated by the default production commands, and no model is downloaded.
Production model storage is separate from development storage. Selecting Ollama
would require starting that profile and provisioning its model first.

## Lifecycle

1. Validate with python scripts/check_production.py.
2. Start database/cache with --wait.
3. Run `docker compose -f compose.prod.yaml run --rm --no-deps backend alembic upgrade head`.
4. Start the full stack with --wait. There is no reload process.
5. Verify /ready inside backend, then run the frontend smoke script with
   FRONTEND_URL=http://127.0.0.1:8081. The --write variant creates a synthetic record.
6. To stop safely, `docker compose -f compose.prod.yaml down` retains volumes.
   Do not use -v when you need data preserved.

Migration is an explicit pre-start operation. For a future release with an
incompatible migration, plan a database backup and compatibility strategy;
reverting an application image does not automatically reverse a schema migration.

## Remaining integration decisions

The backend explicitly ignores forwarded headers in this rehearsal. With the
current rate limiter, requests through nginx therefore share the proxy's client
identity. Trusted-proxy/client-IP handling must be completed and tested before
claiming per-client production rate limiting. Do not enable trust for arbitrary
forwarded headers just to bypass that issue.

Image scanning, immutable registry publication, Kubernetes deployment/autoscaling,
TLS/authentication for public use and rollback evidence remain separate work.
Digest pinning is reproducibility, not proof that an image has no vulnerabilities.

AI assistance: Codex prepared the configuration and scripts from the uploaded
project files. Umar runs and reviews actual builds, checks and PR evidence.
