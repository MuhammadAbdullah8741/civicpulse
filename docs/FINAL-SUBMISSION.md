# Final verification and submission

This is the final implementation/documentation phase. Mark completion only from
real local/CI output. Do not invent screenshots, contribution counts or passing
results. The final checker is a mechanical aid, not the assignment grader.

## 1. Apply and verify Phase 12

Merge the Phase 11 PR into dev after checks/review. Keep the delivery Issue open
for live CD evidence. Create Issue "Complete final integration, documentation and submission evidence".
Create feat/final-submission from updated dev, then extract the final ZIP into
the repository root. It contains complete replacement files, not patch fragments.

In PowerShell at C:\Users\hp\Projects\civicpulse:

```powershell
python -m unittest discover -s tests/delivery -v
python scripts/check_submission.py
kubectl kustomize k8s/overlays/dev > $null
kubectl kustomize k8s/overlays/prod > $null
git diff --check
```

PENDING evidence lines are expected before you supply actual screenshots/URLs.
FAIL lines require fixing. The code archive itself has no Git history, so only
the student's checkout can verify tracked secrets and contribution counts.

For full PostgreSQL/Redis regression tests, use Compose. If the local Kubernetes
cluster is using the laptop's memory, stop it temporarily (do not delete it):

```powershell
k3d cluster stop civicpulse
.\scripts\Start-Local.ps1
docker compose exec -T -e RUN_DB_TESTS=1 -e COVERAGE_FILE=/tmp/civicpulse.coverage backend python -m pytest -q -p no:cacheprovider --cov=app --cov-report=term-missing --cov-fail-under=65
npm --prefix frontend run api:check
$env:FRONTEND_URL = "http://localhost:8080"
node frontend/scripts/smoke-container.mjs --write
```

Expected: all backend tests pass (102 in this snapshot), coverage >=65%, contract
check passes, and both smoke PASS lines. If any fails, stop and fix it before
committing. Frontend source was unchanged in Phase 12; the PR still runs its
full tests/build/audit. Capture three application screenshots using synthetic
data and save them under docs/evidence/final/ with the names in submission.json.

## 2. Commit the reviewed changes

```powershell
git add backend/app/services/client_ip.py backend/app/routes/complaints.py backend/tests/test_client_ip.py compose.yaml compose.prod.yaml k8s/base/config.yaml
git commit -m "fix: resolve rate-limit clients through trusted proxies"
git add scripts/Start-Local.ps1 scripts/check_submission.py scripts/verify_rollback.py
git commit -m "feat: add final verification and rollback tools"
git add README.md docs/RUNBOOK.md docs/ENGINEERING-NOTES.md docs/AI-USAGE.md docs/FINAL-SUBMISSION.md docs/COLLABORATION-EVIDENCE.md docs/submission.json docs/evidence/final/
git commit -m "docs: complete project operations and submission guidance"
```

Do not commit .env, registry tokens or screenshots that expose credentials.

## 3. Production network isolation evidence

Use a clean committed working tree and keep this PowerShell window open:

```powershell
. .\scripts\Prepare-Production.ps1
python scripts/check_production.py
docker compose -f compose.prod.yaml up -d --wait --wait-timeout 300
docker compose -f compose.prod.yaml exec -T backend python -m alembic upgrade head
$dbId = docker compose -f compose.prod.yaml ps -q database
$dbInspect = docker inspect $dbId | ConvertFrom-Json
$dbIp = $dbInspect[0].NetworkSettings.Networks.'civicpulse-prod_internal'.IPAddress
if (-not $dbIp) { throw 'Could not resolve the production database container IP.' }
$frontendId = docker compose -f compose.prod.yaml ps -q frontend
$probeImage = "${env:BACKEND_IMAGE_REPOSITORY}:${env:IMAGE_TAG}"
@'
import socket
import sys
try:
    connection = socket.create_connection((sys.argv[1], 5432), timeout=3)
except OSError:
    print("PASS: frontend network namespace cannot reach database TCP port")
else:
    connection.close()
    raise SystemExit("FAIL: frontend network namespace can reach database")
'@ | docker run --rm -i --network "container:$frontendId" --entrypoint python $probeImage - $dbIp
if ($LASTEXITCODE -ne 0) { throw 'Isolation verification failed.' }
docker compose -f compose.prod.yaml exec -T backend python -c "import socket; s=socket.create_connection(('database',5432),3); s.close(); print('PASS: backend reaches database')"
if ($LASTEXITCODE -ne 0) { throw 'FAIL: backend could not reach database.' }
@("PASS: frontend database TCP connection blocked", "PASS: backend database TCP connection succeeded", "Database address tested: $dbIp", "Commit: $(git rev-parse HEAD)") | Set-Content -Encoding utf8 docs/evidence/final/network-isolation.txt
```

The temporary probe uses the already-built backend image's Python in the
frontend container's network namespace. It tests the database's actual IP,
not merely whether its DNS name resolves. This changes no application data.
Commit the new evidence before the clean-tree rollback demo:

```powershell
git add docs/evidence/final/network-isolation.txt
git commit -m "docs: record production network isolation evidence"
docker compose -f compose.prod.yaml stop
docker compose stop
k3d cluster start civicpulse
.\scripts\Deploy-Kubernetes.ps1
```

If Kubernetes API connectivity fails after restart, inspect the mapped API port
with `docker port k3d-civicpulse-serverlb 6443/tcp`. Restore the known local
kubeconfig endpoint if necessary; do not create a second cluster.

## 4. Rollback evidence (both required mechanisms)

This demo rolls the local backend to a new tag containing the SAME bytes,
undoes it, repeats the change and reapplies the previous rendered overlay. It
does not simulate a functional code regression or delete database volumes.
The script requires current live images to match the clean current commit.

```powershell
python scripts/verify_rollback.py --run-demo
$env:FRONTEND_URL = "http://civicpulse.localhost:8082"
node frontend/scripts/smoke-container.mjs --write
```

Record the run on video. It saves rollback.txt, rollback-images.json and the
previous overlay in docs/evidence/final/. If it fails, inspect that log and the
live rollout; preserve failed evidence outside the checkout before retrying.
Do not repeatedly run it to overwrite a success. There is no need to repeat the
long HPA/VPA experiments: those measured results are already committed.

## 5. Collaboration evidence and remaining human inputs

Reuse real existing evidence where available. Exact red/green and merge-conflict
commands are in [COLLABORATION-EVIDENCE.md](COLLABORATION-EVIDENCE.md). Otherwise these tasks remain:

- main branch protection: PRs, CI and >=1 approval required; capture settings.
- >=5 merged Issue-linked PRs with substantive partner review: record URLs.
- >=35 meaningful commits; neither partner below 35%. Run `git shortlog -sn --no-merges HEAD`.
  Enter each person's actual author aliases as one list in partner_git_authors.
  Do not reattribute old work or add empty commits to change percentages.
- A deliberately failing test must block a real PR merge, then pass after its
  correction in that same PR. Capture both states. Do this before final release,
  not by disabling checks or leaving a broken test on dev/main.
- A deliberate merge conflict must involve real code. Use two reviewed changes
  to the same existing line from the same base, integrate both intended results,
  and test the resolution. Capture actual markers/resolution/merge and write
  2-4 sentences explaining the chosen result. Do not fabricate terminal evidence.
- Fill in the personal reflection in Engineering Notes question 8 and check the
  course slide's exact CI/CD maturity terminology for question 2.
- Credentials previously pasted in chat must be rotated. Mark credentials_rotated
  true only after revoking the old Groq key and rotating the exposed database
  credential consistently with its existing database; editing .env alone does
  not change an initialized PostgreSQL password. Never paste the replacements.

Use `python scripts/check_submission.py --history` to scan reachable commits for
common secret patterns/filenames without printing secret values. This is not a
complete secret detector. If a leak is found, rotate first and document the
incident; do not rewrite shared Git history without coordinating with your partner.

## 6. Review and final main merge

Commit actual evidence and metadata, push feat/final-submission and open a PR
into dev titled "docs: finalize integration verification and submission evidence".
Link the Phase 12 Issue. All six CI checks and partner approval must pass.
Merge into dev. Then open a reviewed PR from dev into main; never push directly
to main. Keep required checks enabled. Use title "release: integrate CivicPulse assignment".

After merging into main, Actions -> CD must complete full suite, publishing and
Kubernetes deployment successfully. Download delivery-images and
delivery-deployment artifacts. Save the run URL, verify both GHCR packages and
SHA tags, and keep SBOMs/digests for submission. A green dev CI is not a CD run.
The temporary runner cluster is deleted and is not a public hosting URL.

## 7. Tag and verify the release

Only after main CD is green and the submitted code is final:

```powershell
git fetch origin
git switch main
git pull --ff-only origin main
git tag --list v1.0.0
```

If v1.0.0 does not already exist:

```powershell
git tag -a v1.0.0 -m "CivicPulse assignment release"
git push origin v1.0.0
```

If it exists, use the next unused version; never force-move it. Wait for Release
validation, full delivery, and release-note publication. Verify attached SBOMs,
images.json and version tags. A release failure is not a completed assignment.
Record the actual release URL and successful CD URL in submission metadata.
Documentation-only evidence updates still go through a feature PR; never amend
published code or invent URLs to make the checker green.

## 8. Five-minute demonstration and submission

Suggested timing (both people speak):
- 0:00-0:40: partner A explains problem/architecture and shows the clean-clone
  quickstart command. Prepare downloads beforehand; disclose any recording cuts.
- 0:40-1:30: partner B submits a synthetic report, shows AI/provider, dashboard
  state transition/conflict and stats cache. Demonstrate a controlled fallback.
- 1:30-2:10: partner A shows production network isolation and data persistence.
- 2:10-3:05: partner B explains the HPA/VPA chart, lag and failed load thresholds.
- 3:05-4:15: both explain the imperative and declarative rollback recording,
  including the previous image reference and smoke result.
- 4:15-5:00: show green CD, SHA/digest tags, SBOMs and release; state limitations.

Record actual duration and both_partners_speak in docs/submission.json, plus the
unlisted video URL. Use `python scripts/check_submission.py --strict --history`.
Resolve FAIL and PENDING items, then submit repository URL, successful CD run URL,
both GHCR links, video link, actual shortlog output, HPA watch capture and chart.
Keep instructors' access working if the repository/packages are private.
