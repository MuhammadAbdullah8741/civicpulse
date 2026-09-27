# Engineering notes

These answers describe this repository. Source references are captured for the
Phase 12 files; recheck line numbers if the referenced code changes.

## 1. Laptop versus CI runner

The laptop is Windows while containers/CI use Linux. The entrypoint normalizes
CRLF before execution (`frontend/Dockerfile:15`); without that,
a shell interpreter can see a carriage return as part of its path or commands.
The developer's Python can differ from the runtime; the pinned Python base
image (`backend/Dockerfile:1`) freezes the container runtime.
Frontend installs differ if dependency resolution is repeated without a lock;
`npm ci` (`frontend/Dockerfile:4`) uses package-lock.json in
the pinned Node builder. The existing runtime apk upgrade intentionally pulls
security fixes, so the same source SHA is not a guarantee of identical bytes;
CD records actual image digests instead.

## 2. CI/CD maturity

The repository implements automated integration, gated publication and an
automated deployment rehearsal: CI checks tests/types/security/manifests,
CD calls it on the merged main result (`.github/workflows/cd.yml:25`),
and deployment needs the publishing job (`.github/workflows/cd.yml:70`).
This is continuous delivery with a disposable deployment test, not demonstrated
continuous deployment to a persistent production service. The next step would
be a persistent staging/production target with environment protection, smoke
checks, monitored promotion and a tested rollback policy. Match the lecture's
exact rung terminology to Lecture 03 slide 32; the slide was not supplied with
the repository, so this answer does not invent its labels. Actual success is
proved by the recorded main CD run, not by merely having workflow files.

## 3. Build once, deploy many

The publisher captures repository digests (`scripts/publish_images.py:75`)
and exposes them as job outputs. Deployment consumes those outputs
(`.github/workflows/cd.yml:77`) and substitutes them into
the production overlay (`scripts/deploy_ci.py:44`).
The deploy job pulls those artifacts; it does not rebuild them. Browser assets
use a relative API path while Nginx substitutes the runtime upstream
(`frontend/docker-entrypoint.sh:15`). Without those decisions,
environment-specific rebuilds could produce untested bytes or bake in a laptop
URL. Separate workflow runs can rebuild a SHA; their digests distinguish them.

## 4. Correctness for probabilistic AI

Correctness includes schema validity, permitted category/priority, bounded
single-line summary, a finite attempt budget, explicit fallback and no obeying
instructions embedded in complaint data. Exact natural-language wording is not
a stable correctness oracle. TriageResult validates output
(`backend/app/providers/triage/base.py:8`); the service
revalidates every provider response (`backend/app/services/triage.py:34`).
The prompt separates untrusted complaint data from instructions
(`backend/app/providers/triage/prompt.py:41`). This reduces
risk; it is not proof that every semantic prompt injection is impossible.
CI chooses simulated mode (`.github/workflows/ci.yml:11`)
and tests malformed output, timeouts, retries and fallback with controlled inputs.

## 5. Measured HPA lag

The 100/s baseline scheduled the higher load at 30 seconds. Desired replicas
first increased at 53.9 seconds: about 23.9 seconds later. Extra ready capacity
appeared at 59.4 seconds: about 29.4 seconds later. The tuned run recorded 63.2
and 68.8 seconds, respectively, giving about 33.2 and 38.8 seconds of lag.
Sampling is roughly five seconds plus API time; container startup adds an
offset, so these are approximate. Metrics collection, reconciliation and pod
startup contribute; no measurement here isolates each contribution. More
pre-existing capacity, smaller startup cost and reviewed metric intervals can
reduce visible lag. CPU request changes also alter the HPA denominator.
Source: docs/evidence/scaling/COMPARISON.md and the two samples.csv files.
Both 100/s runs failed thresholds (847/515 dropped iterations; 0/28 failed HTTP
requests). The later 30/s rollout passed; it is a separate experiment.

## 6. Why VPA is Off

The manifest sets Off (`k8s/vpa/backend-vpa.yaml:12`). VPA
records recommendations while HPA controls replica count. Automatic changes to
CPU requests change the denominator of HPA CPU utilization, so two active
controllers can counteract each other; VPA updates/evictions may also disturb
availability. We manually changed 100m/128Mi to the recorded 163m/262144k target,
then repeated the same offered load. The broad upper bound and short observation
window are not a production capacity recommendation.

## 7. Internal networking and hosted inference

The backend joins edge and internal (`compose.prod.yaml:52`);
PostgreSQL and Redis join only internal, and frontend joins only edge. The
internal network has internal: true (`compose.prod.yaml:187`).
Thus database/cache lack ordinary external egress, while the dual-connected
backend can reach Groq through edge. Membership and absence of published data
ports are checked by scripts/check_production.py. A real frontend-to-database
connection failure, plus backend success, must be captured as runtime evidence.
Kubernetes namespace alone is not a firewall; these Compose isolation claims
do not imply a Kubernetes NetworkPolicy implementation.

## 8. Failure investigation and reflection

The recorded scaling investigation found backend readiness loss and missing HPA
metrics. Restarting the failed local agent restored database/cache and then
backend readiness. A later tuned run still had 28 failed requests and a backend
restart. The prior process exited with code 0; pod events explicitly said the
liveness probe failed and Kubernetes killed the container. Thus this was not
established as an OOM crash. Commands were `kubectl describe pod` and
`kubectl logs POD --previous`; the evidence discussion is in
`docs/evidence/scaling/PROBE-ADJUSTMENT.md`. Liveness tolerance changed separately
from readiness (`k8s/base/backend-probes.yaml:15`). That does
not prove the restart caused all 28 failures.

**Student completion required:** add the actual time spent and what you personally
believed first. The logs establish the technical sequence, but do not establish
that this one investigation took more than an hour or what either partner
thought. If another incident truly took more than an hour, use that incident
with its real command/log evidence instead. Do not invent an experience.

## Database index rationale

The (status, priority) index supports dashboard filtering by status and optionally
priority. The created_at index supports recent-first ordering/pagination; it
does not guarantee constant-cost deep OFFSET pages. Schema and query references:
`backend/alembic/versions/0001_create_complaints.py:58` and
`backend/app/repositories/complaints.py:69`.
