# Phase 10: measured HPA, VPA and rolling updates

Use after Phase 9 is merged into dev. The existing k3d-civicpulse cluster must
be running, with two ready backend replicas, seeded complaints, working Ingress
and metrics-server. Python on Windows runs these scripts; no pip installs needed.
All Kubernetes calls explicitly select context k3d-civicpulse. No Git commands
that change history are executed by the scripts.

## 1. Install recommender and load generator

```powershell
python scripts/scaling_experiment.py install-vpa
```

Vendored VPA 1.4.2 manifests are sourced from the upstream commit recorded in
k8s/vpa/vendor/SOURCE.md. Only the recommender Deployment is installed, plus
upstream CRDs/RBAC; no updater or admission-controller Deployment is installed.
The backend VPA uses updateMode Off and does not automatically change resources.
The load generator uses grafana/k6:0.57.0 on the existing Docker network. It
accesses the Traefik Ingress with Host civicpulse.localhost, so it does not rely
on Windows hosts-file DNS. It performs read-only complaint-list requests;
TRIAGE_PROVIDER remains simulated and no model is downloaded.

## 2. Original requests and scale-out

```powershell
python scripts/scaling_experiment.py run --name baseline --rate 200 --require-scale-out
```

About 9 minutes: 30 seconds at 5 requests/sec, 180 seconds at 200 requests/sec,
then observation without generated requests through 540 seconds. Five-minute
HPA scale-down stabilization is intentionally retained. Do not edit minReplicas,
CPU targets, or run CPU-burning commands inside the app to manufacture scaling.
The script records the original requests, actual replicas/CPU, HPA watch output,
k6 metrics, VPA bounds and targets, and an SVG chart in:
`docs/evidence/scaling/baseline/`.

A failed request or dropped iteration causes the k6 gate to fail. No scale-out
also fails this baseline gate. Keep unsuccessful runs. If no scaling occurs,
review CPU and request metrics, then rerun under a NEW name at an appropriate
higher rate. If failures occur, inspect bottlenecks and try a lower rate. Use
the same successful rate in the later tuned run. Never relabel failed runs.

The CPU HPA may take longer than the observation window to return to two ready
replicas. Wait rather than force a baseline. Every experiment checks this.

## 3. Record VPA and apply its recorded target

Open baseline/vpa-describe.txt. It must contain Target, Lower Bound and Upper
Bound for backend. If not, allow a longer observation window and collect a new
run; do not invent recommendations.

```powershell
python scripts/scaling_experiment.py apply-vpa --name baseline
```

This reads the recorded recommendation, changes backend requests live, writes
`k8s/base/backend-vpa-requests.yaml`, and adds that patch to base/kustomization.yaml.
It refuses targets above current limits; review capacity before raising limits.
The before/after requests and full recommendation are saved in requests-change.json.
These source changes must be committed after validation.

## 4. Repeat the same workload

After backend returns to two ready replicas:

```powershell
python scripts/scaling_experiment.py run --name tuned --rate 200
python scripts/scaling_experiment.py compare --before baseline --after tuned
```

If a different baseline name/rate was needed, use that name/rate consistently.
No scale-out in the tuned run can be a real result; report it, do not fake it.
Review COMPARISON.md, both result.json files and both replicas-load.svg charts.
The chart's right axis is offered request rate, not achieved throughput. Dropped
iterations and actual HTTP request totals are separately recorded in k6 summaries.
Timing is relative to container launch; interpret the small startup/sampling
uncertainty honestly. VPA estimates from these short runs are provisional.

## 5. Image-triggered rolling update under load

Wait for two ready replicas, then:

```powershell
python scripts/scaling_experiment.py run --name rollout --mode rollout
```

About 3.5 minutes at 30 requests/sec. At 30 seconds the runner issues kubectl set
image and waits for rollout completion while requests continue. The new tag
points to identical application bytes: this tests image-triggered rolling-update
mechanics, not a new application feature. Both image references are recorded.
Success requires completed rollout, nonzero requests, zero request failures,
no dropped iterations and all HTTP checks passing. Claim zero observed failures
only for this measured window if result.json and k6.log confirm it.

## 6. Final checks

```powershell
kubectl kustomize k8s/overlays/dev > $null
kubectl kustomize k8s/overlays/prod > $null
$env:FRONTEND_URL = 'http://civicpulse.localhost:8082'
node frontend/scripts/smoke-container.mjs --write
git diff --check
```

Do not run Deploy-Kubernetes.ps1 during an experiment: it reapplies replicas and
rebuilds images, invalidating the comparison. The measurement scripts do not
need a clean worktree because they are intended to record an experiment before
its evidence and resource changes are committed. They record current HEAD and
actual deployed configurations for traceability.

## Evidence checklist

- Original resource requests and VPA Target/Lower/Upper bounds.
- Baseline scale-out in hpa-watch.txt and samples.csv.
- Chart of replicas/ready replicas versus offered load.
- Same-load before/after comparison and 3-5 sentences interpreting observed lag.
- Requests changed in committed Kubernetes manifests.
- Rollout logs, image references, and k6 metrics with zero observed failures.
- Note that HPA and automatic VPA can conflict through the CPU request denominator.
- CI passing and partner review; no fabricated evidence.

If interrupted, inspect `docker ps --filter name=civicpulse-load` and stop only
that experiment container. Keep the cluster and database PVCs intact.
