# CivicPulse operations runbook

## Local development

Run `.\scripts\Start-Local.ps1` in PowerShell at the repository root. Use
`docker compose ps` and `docker compose logs --tail=100 backend` to inspect state.
Readiness is `Invoke-RestMethod http://localhost:8000/ready`. Migrations use
`docker compose exec -T backend python -m alembic upgrade head`; seed uses
`docker compose exec -T backend python -m app.seed` and is idempotent.

Never delete volumes as a routine repair. Existing PostgreSQL volumes keep
existing passwords even if .env is edited. Back up data before intentional
schema/data changes. Development source mounts are absent from production.

## Production Compose rehearsal

After committing changes to a clean working tree:

```powershell
. .\scripts\Prepare-Production.ps1
python scripts/check_production.py
docker compose -f compose.prod.yaml up -d --wait --wait-timeout 300
docker compose -f compose.prod.yaml exec -T backend python -m alembic upgrade head
docker compose -f compose.prod.yaml exec -T backend python -m app.seed
$env:FRONTEND_URL = "http://localhost:8081"
node frontend/scripts/smoke-container.mjs --write
```

The preparation script builds local sha-<commit> images and exports their names
and PostgreSQL/Redis digests into this PowerShell session. It selects simulated
triage for a deterministic rehearsal. This standalone file must not be merged
with the development Compose file. Only frontend port 8081 is published.

## Kubernetes local deployment

Install tools using `. .\scripts\Install-KubernetesTools.ps1`. Existing cluster:
`k3d cluster start civicpulse`. Use explicit context k3d-civicpulse for every
manual command. Deploy a clean committed checkout with
`.\scripts\Deploy-Kubernetes.ps1`. Application: http://civicpulse.localhost:8082.
A hosts entry resolving civicpulse.localhost to 127.0.0.1 is needed on some Windows machines.

```powershell
kubectl --context k3d-civicpulse -n civicpulse get pods,pvc,hpa
kubectl --context k3d-civicpulse -n civicpulse logs deployment/backend --tail=60
kubectl --context k3d-civicpulse -n civicpulse get events --sort-by=.lastTimestamp
```

If a node becomes NotReady, inspect `kubectl get nodes` and Docker container
state first. The observed local agent outage recovered after
`docker restart --timeout 30 k3d-civicpulse-agent-0`, followed by waiting for node
Ready and database/cache/backend rollouts. Restart only a confirmed unhealthy
node; do not recreate the cluster or discard its PVCs. HPA missing metrics can
be a symptom of unready pods/dependencies, not just a metrics-server fault.

## Client identity and rate limits

Application rate limiting resolves X-Forwarded-For only from configured trusted
proxy peers. Compose trusts DNS addresses of its frontend service; Nginx replaces
user-supplied forwarding headers with the socket source. Uvicorn header rewriting
is disabled so the application sees the real peer. Kubernetes trusts the default
k3s pod CIDR 10.42.0.0/16 and assumes all workloads in this local cluster are
trusted. Do not enable Traefik forwardedHeaders.insecure. For another cluster,
configure the actual trusted proxy network and enforce an appropriate network
policy; do not copy this pod-CIDR assumption into a multi-tenant deployment.

The closest untrusted hop determines the quota key. Multiple clients genuinely
sharing a NAT address can still share a quota; this demo has no authenticated
user identity. DNS/header failures retain the socket identity. Redis atomically
stores counters across replicas and returns Retry-After on the eleventh valid
submission inside the default 60-second window. Do not raise limits just to
hide a test failure.

## Triage failure

Inspect /api/meta/providers and the backend's structured triage_fallback warning.
Logs record provider/error class and complaint ID rather than tokens/text.
A 404 model_not_found needs an available model setting; it is not retryable.
Timeouts, 429 and 5xx get one jittered retry. Malformed schema output fails to
rules. Fallback summaries are not cached as successful LLM results. Check the
actual provider field, not just whether a response was returned.

Use simulated mode for CI and a controlled fallback demonstration. To select
Groq locally, edit only the ignored .env, set TRIAGE_PROVIDER=llm and a rotated
key, then recreate the backend. Never print .env or include it in evidence.
Regex contact redaction does not anonymize all complaint text.

## Delivery and release

Main pushes trigger CD: full suite -> build/scan/SBOM/push -> ephemeral Kubernetes
smoke. Package write access exists only in the publishing job. The temporary
cluster uses read access and is deleted afterward. A green CI run on dev does
not prove that CD has run. Record the actual main run URL and image digests.
Release vMAJOR.MINOR.PATCH tags must point to a commit reachable from main.

## Rollback

First capture the current image and rollout history:

```powershell
kubectl --context k3d-civicpulse -n civicpulse get deployment backend -o jsonpath='{.spec.template.spec.containers[0].image}'
kubectl --context k3d-civicpulse -n civicpulse rollout history deployment/backend
```

Imperative recovery: `kubectl --context k3d-civicpulse -n civicpulse rollout undo deployment/backend`,
then `rollout status deployment/backend --timeout=180s` and a smoke test. Select
an explicit revision if the immediately previous revision is not the intended
one. This changes live state and can diverge from the repository.

Declarative recovery: check out the previous reviewed commit in a separate
worktree; render its overlay; substitute both recorded previous image references
(SHA tags or digests) into the rendered manifest, apply it, wait for rollouts and
smoke-test. Record the previous commit and references before changing deployment.
Never deploy latest. Do not reapply a placeholder release-required image tag.
Keep the prior image available to the cluster. Application rollback does not
reverse a database migration; check schema compatibility first.

Use the final verification script's saved rollback overlay for a controlled
local demonstration. The submission checklist gives the exact commands.
