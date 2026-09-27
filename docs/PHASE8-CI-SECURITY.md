# Phase 8: Backend static checks and container vulnerability gate

## Changes

Backend tests now installs requirements-dev.txt, runs Ruff across app/tests/alembic,
and runs mypy across app before pytest. Ruff checks imports, undefined names and
selected Python error rules. Mypy checks all function signatures and application
bodies; there is no blanket ignore_errors or ignore_missing_imports. Dynamic
SQL/JSON boundaries retain explicit Any types where appropriate. Redis response
casts document the synchronous decoded client; Lua TTL arguments are serialized
as strings. Triage revalidation uses a separate raw value without changing the
provider contract or fallback behavior. The production application dependency
file and container images do not acquire the development lint/type tools.

The previous frontend and database integration jobs remain. Container security is
a new required job: builds both images without publishing, exports each image to
an archive, and scans it with aquasec/trivy:0.74.0. The scanner reads the exported
image and has no Docker daemon socket mount. A named scanner cache avoids repeat
vulnerability database downloads. Export archives are temporary and removed.

The gate uses --scanners vuln --ignore-unfixed --severity HIGH,CRITICAL --exit-code 1.
Both images are scanned even if the first fails. Scanner/export errors fail the
job. JSON reports are uploaded with if: always() and retained for seven days.
No exclusions or continue-on-error bypass the gate. The scan policy does not claim
that low/moderate or unfixed vulnerabilities are absent. A digest or pinned tag
is reproducibility evidence, not proof of security.

## Local workflow

From the repository root, use the same Python 3.12 container as the backend:

```powershell
docker run --rm --mount "type=bind,source=$($PWD.Path)\backend,target=/app" -w /app python:3.12-slim sh -c "python -m pip install -r requirements-dev.txt && python -m ruff check --no-cache app tests alembic && python -m mypy --cache-dir=/tmp/mypy-cache app && python -m pytest -q -p no:cacheprovider"
docker compose up -d --build --wait --wait-timeout 180
docker compose exec -T backend alembic upgrade head
docker compose exec -T -e RUN_DB_TESTS=1 -e COVERAGE_FILE=/tmp/civicpulse.coverage backend python -m pytest -q -p no:cacheprovider --cov=app --cov-report=term-missing --cov-fail-under=65
npm --prefix frontend run api:check
node frontend/scripts/smoke-container.mjs
python scripts/scan_images.py civicpulse-backend:dev civicpulse-frontend:dev
```

Scan reports default to the system temporary directory's civicpulse-security-reports
folder. image-1-trivy.json corresponds to the first image argument and image-2 to
the second. The first scan downloads the scanner and its vulnerability database;
no Ollama model is involved. To select a report destination use --output PATH.

If the scan is red, inspect VulnerabilityID, PkgName, InstalledVersion and
FixedVersion in its output. Update the affected dependency or base image, rerun
application verification, and rescan. Do not merge by disabling the check. An
unavailable registry or vulnerability database is a scan failure, not a clean bill
of health. The existing base/dependency versions were not preemptively changed;
the real report determines the needed updates.

## Evidence and completion

Retain the actual CI run links and reports. Add Container security to required
checks after its first run, alongside Backend tests, Database integration and
Frontend checks. Review must include the Redis typing/revalidation changes and
scanner failure behavior. Only mark the vulnerability checklist complete when
both images pass. A real blocked/red PR followed by a reviewed fix can form the
required red/green evidence; capture what actually happens.

Prepared static verification: Ruff passed; mypy passed across 34 application files.
Unit/integration tests and Docker scans must be executed by Umar/GitHub. No runtime
or vulnerability result is asserted here. Codex assisted with preparation; Umar
owns execution, review and commits.

Remaining work includes trusted-proxy rate-limit behavior, Kubernetes validation
and deployment, CD/release, autoscaling measurements, rollback demonstration and
final submission documentation. This phase does not claim those are complete.

References:
- https://docs.astral.sh/ruff/configuration/
- https://mypy.readthedocs.io/en/stable/config_file.html
- https://trivy.dev/docs/latest/target/container_image/
- https://github.com/aquasecurity/trivy/releases/tag/v0.74.0
