# Phase 9: local Kubernetes

Prerequisite: Phase 8 merged into dev; Docker Desktop running Linux containers.
The supplied scripts target only context `k3d-civicpulse` and namespace `civicpulse`.
They do not push images or modify Git history.

## Install and create

From the repository root in PowerShell:

```powershell
. ./scripts/Install-KubernetesTools.ps1
# Stop Compose containers to release memory; no volumes are deleted.
docker compose stop
k3d cluster create civicpulse --image rancher/k3s:v1.35.8-k3s1 --servers 1 --agents 1 --port "127.0.0.1:8082:80@loadbalancer" --wait
kubectl --context k3d-civicpulse get nodes
kubectl kustomize k8s/overlays/dev > $null
kubectl kustomize k8s/overlays/prod > $null
```

Run cluster-create only once. For an existing stopped cluster use
`k3d cluster start civicpulse`. For new PowerShell sessions prepend
`$env:PATH = "$env:USERPROFILE\Tools\civicpulse;$env:PATH"`.
K3s supplies Traefik, metrics-server and a local-path default storage class.
This downloads Kubernetes infrastructure images; it downloads no Ollama model.

## Deploy

Commit these files first, then:

```powershell
./scripts/Deploy-Kubernetes.ps1
```

The script builds images tagged with the full Git commit, imports them into k3d,
creates a random database password only if the Secret does not already exist,
applies resources, runs Alembic in a Job and waits for readiness.
No passwords are printed, stored in Git, or copied from your Compose `.env`.
PostgreSQL and Redis data here are separate from Compose volumes.
Do not apply `k8s/secret.example.yaml`: it contains placeholders only.
The Secret is excluded from Kustomize output and created by the script instead.

The dev and prod overlays share the same baseline. The prod overlay intentionally
uses `release-required` image tags; deploy it through the script with `-Overlay prod`
for local rehearsal. Registry digests and release image promotion follow in CD.
Do not apply an unrendered prod overlay directly.

## Verify and save real evidence

```powershell
kubectl --context k3d-civicpulse -n civicpulse get pods,pvc,svc,ingress,hpa,pdb
kubectl --context k3d-civicpulse -n civicpulse exec deployment/backend -- id -u
kubectl --context k3d-civicpulse -n civicpulse exec deployment/frontend -- id -u
kubectl --context k3d-civicpulse -n civicpulse exec deployment/backend -- python -m app.seed
$env:FRONTEND_URL = 'http://civicpulse.localhost:8082'
node frontend/scripts/smoke-container.mjs --write
kubectl --context k3d-civicpulse -n civicpulse top pods
```

Expected: backend/frontend each 2 ready, postgres 1 ready, Redis 1 ready;
two bound PVCs; four internal ClusterIP Services (database is headless);
UIDs 10001 and 101; smoke PASS. HPA metrics may need a minute to populate.
Do not claim scaling success based only on an HPA existing. Load/rollout/VPA
measurements are the next phase. Metrics-server must actually return pod usage.

Browser: http://civicpulse.localhost:8082. If Windows cannot resolve this hostname,
add `127.0.0.1 civicpulse.localhost` to the Windows hosts file as administrator.
Do not substitute localhost in the URL: the Ingress matches its configured host.

Save outputs/screenshots in the issue or PR. Avoid dumping Secrets. Troubleshoot:

```powershell
kubectl --context k3d-civicpulse -n civicpulse get events --sort-by=.lastTimestamp
kubectl --context k3d-civicpulse -n civicpulse logs deployment/backend --tail=80
kubectl --context k3d-civicpulse -n civicpulse describe pods
```

## Design and limitations

- Frontend and backend: two replicas, non-root, read-only root, bounded /tmp;
  rolling updates maxSurge 1/maxUnavailable 0, preStop 5 seconds and grace 45 seconds.
- Backend startup/liveness /health; readiness /ready; startup budget 60 seconds.
- StatefulSet postgres with volumeClaimTemplates; Redis AOF with separate PVC.
- PDB minAvailable 1 protects voluntary backend evictions, not host failure.
- HPA v2: CPU target 60%, min 2/max 10, scale-down stabilization 300 seconds.
- Ingress /api routes directly to backend, / routes to frontend. Nginx's optional
  API proxy uses a fully qualified backend DNS name.
- Application logs remain PII-reduced. Trusted ingress client-IP/rate-limit
  handling still needs a dedicated verification; current proxy clients can
  share a rate-limit bucket. Do not claim per-user isolation behind ingress.
- This laptop cluster has no TLS, backups or multi-host availability. The prod
  overlay is a deployment configuration, not proof of production readiness.
- Scaling can exceed laptop capacity; measure within available resources.

Stop without deleting data: `k3d cluster stop civicpulse`.
Deleting the cluster can destroy its local-path persistent data; do not delete
it while gathering assignment evidence.
