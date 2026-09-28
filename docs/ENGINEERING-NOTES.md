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

## 2. CI/CD maturity

According to Lecture 03, slide 32, CivicPulse reaches Level 3:
Continuous Delivery. The lecture describes this level as keeping main
ready and producing a build artifact so that software stays deployable.

Our pipeline supports this classification through automated verification
and gated artifact publication. `.github/workflows/cd.yml:3–5` triggers
CD on pushes to main. The workflow invokes the full CI suite at line 25.
The build-and-publication job requires those checks to succeed through
`needs: test` at line 31. It publishes container images and exposes their
immutable references and digests at lines 37–41. This provides tested,
traceable artifacts that can be deployed without rebuilding the source.

We also automate deployment verification. The deployment job depends on
publication at `.github/workflows/cd.yml:70`, consumes its image outputs
at lines 77–78, and creates a temporary Kubernetes cluster at lines 92–93.
The successful main CD run and v1.0.1 release workflow demonstrate that
the pipeline executes successfully.

However, this temporary cluster is a deployment rehearsal rather than a
persistent production service. Therefore, we do not claim Level 4:
Continuous Deployment, which the lecture describes as automatically
shipping changes from main to production.

The next rung is Level 4: Continuous Deployment. To reach it, we would
extend the existing pipeline to deploy the same verified image digests
automatically to a persistent production environment after the checks
pass. This would remove the remaining manual production-deployment step,
reduce release delay and make delivery to users more consistent.

We already implement several practices associated with the lecture's
Level 5: Production-grade, including reviews, security scans, smoke tests
and rollback exercises. These individual practices strengthen our
pipeline, but they do not establish a complete production-grade operating
system with persistent staging, controlled promotion and ongoing
production monitoring.
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

For CivicPulse, correctness means satisfying the triage contract and
producing a defensible classification of the complaint. It does not mean
returning exactly the same natural-language sentence on every live request.

The output must contain an allowed category and priority, a nonblank
single-line summary of at most 140 characters, and confidence between
zero and one. Extra fields are rejected. These constraints are defined
in `backend/app/providers/triage/base.py:8–23`. The service validates
the provider result again before accepting it
(`backend/app/services/triage.py:31–34`).

Structural validity alone does not prove semantic correctness. A valid
JSON object could still classify a burst water pipe incorrectly.
Therefore, live-provider evaluation also considers whether the category,
urgency and factual summary match the reported problem. Confidence is
a provider-supplied score, not a guarantee of accuracy.

Complaint text is treated as untrusted data. The system prompt explicitly
instructs the model to ignore embedded attempts to change its role,
rules or output format (`backend/app/providers/triage/prompt.py:20–34`).
The complaint is placed in a separate user message after contact-detail
redaction (`backend/app/providers/triage/prompt.py:36–42`). These measures
reduce risk but do not establish that all prompt injection is impossible.

Failure behavior is also part of correctness. The service retries once
with jitter only for timeout, HTTP 429 and HTTP 5xx failures
(`backend/app/services/triage.py:14–20` and `29–38`). When a provider
cannot produce an acceptable result, the service uses rules and records
the provider as `rules:fallback`
(`backend/app/services/triage.py:48–49`).

CI remains deterministic by selecting `TRIAGE_PROVIDER=simulated` and
`SIMULATED_MODE=success` in `.github/workflows/ci.yml:10–12`, rather than
depending on a live hosted model. The simulated provider uses fixed
rule-based behavior and supports controlled error and malformed-output
modes (`backend/app/providers/triage/simulated.py:13–28`). Tests can
therefore verify validation, retries and fallback with predictable
inputs and failures, without depending on API availability, account
limits or changing model wording. Passing these tests establishes the
tested software behavior; it does not prove perfect live AI judgment.

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

During the Kubernetes scaling experiment, the backend became unready and the HPA could not obtain CPU metrics. The cause was initially unclear. With AI-assisted guidance, I used pod status, events and previous container logs to investigate. Restarting the local agent restored database/cache availability and backend readiness. A later backend restart was explicitly linked to failed liveness probes. We increased the liveness timeout to five seconds and the failure threshold to six, leaving readiness unchanged. The subsequent rolling-update experiment completed 5,401 requests with no failed requests or dropped iterations. However, this did not erase the earlier load-test failures or prove that every failed request had the same cause. I did not record the investigation time separately, so I cannot reliably state its duration. This experience showed me the importance of checking node health, dependencies and termination events before changing configuration. Next time, I would record investigation timestamps and change one setting at a time to make the results easier to interpret.

Supporting code and recorded evidence for question 8:
`k8s/base/backend-probes.yaml:15` specifies the adjusted liveness timeout;
`docs/evidence/scaling/PROBE-ADJUSTMENT.md` records the interpretation;
`docs/evidence/scaling/rollout/result.json` records the subsequent rollout result.
The actual time spent and initial incorrect belief remain unestablished; this
reflection does not claim to meet those parts of question 8.

## Database index rationale

The (status, priority) index supports dashboard filtering by status and optionally
priority. The created_at index supports recent-first ordering/pagination; it
does not guarantee constant-cost deep OFFSET pages. Schema and query references:
`backend/alembic/versions/0001_create_complaints.py:58` and
`backend/app/repositories/complaints.py:69`.
