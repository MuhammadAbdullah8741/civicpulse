# Phase 11: GHCR publishing, temporary Kubernetes deployment and releases

## What this phase changes

- ci.yml keeps the existing five checks, adds workflow_call and a delivery-validation job.
- cd.yml runs on main pushes (or manual dispatch once installed on the default branch), calls full CI, builds/scans both application images, generates Syft SBOMs, publishes GHCR SHA/latest tags and deploys captured digests to a temporary k3d cluster.
- release.yml runs for v* tags, validates stable semantic version and main ancestry, calls the same delivery pipeline and publishes generated release notes with SBOMs and image references.
- Three delivery Python scripts and standard-library tests support those workflows.
- ADR 0003 records the source SHA versus image digest decision and limitations.

The archive replaces only .github/workflows/ci.yml among existing files. Review
its diff: it should retain all your current checks. It does not replace base
manifests, resource/probe patches, local installers, application files or scaling
evidence. No GitHub token or database credentials are included.

## Prerequisites

Merge the Phase 10 PR into dev first, keeping its failed baseline/tuned results
and successful rollout evidence. Work on a new feat/delivery-workflows branch.
GitHub Actions must be enabled. Default read-only workflow-token permissions
are fine: the YAML requests narrowly scoped permissions per job. No PAT,
account password or live LLM key is needed.

## Local verification (PowerShell, repository root)

```powershell
Set-Location "$env:USERPROFILE\Projects\civicpulse"
python -m unittest discover -s tests/delivery -v
# Stop if a command fails. Expected: 14 tests pass.
docker run --rm --mount "type=bind,source=$($PWD.Path),target=/repo" -w /repo rhysd/actionlint:1.7.7 -color
kubectl kustomize k8s/overlays/prod > $null
git diff --check
git diff -- .github/workflows/ci.yml
git status --short
```

The actionlint image is a small, separate validation tool. These commands do
not publish images, apply manifests, restart local services or rerun load tests.
Do not execute publish_images.py or deploy_ci.py manually; they reject local
execution because their publishing/deployment gate belongs in GitHub Actions.

## Issue

Title: Add gated GHCR publishing, Kubernetes CD and versioned releases

- [ ] Reuse the full CI suite before publishing.
- [ ] Publish backend/frontend SHA tags and main latest tags to GHCR.
- [ ] Generate Syft SPDX SBOMs and capture image digest outputs.
- [ ] Deploy production overlay by digest to a temporary runner cluster.
- [ ] Apply migrations and pass an Ingress smoke test; capture HPA output.
- [ ] Add gated version tags and generated GitHub release notes.
- [ ] Document credentials, immutable deployment references and evidence.
- [ ] Pass PR checks and partner review.
- [ ] Save a successful main CD run and final version release evidence.

Keep the final live-evidence checkbox open until the workflows have actually
run. Code review success alone is not publishing/deployment evidence.

## Suggested commits

```powershell
git add .github/workflows/ci.yml .github/workflows/cd.yml .github/workflows/release.yml scripts/publish_images.py scripts/install_ci_k3d.py scripts/deploy_ci.py
git commit -m "ci: gate GHCR publishing and Kubernetes delivery on full tests"
git add tests/delivery/test_delivery.py
git commit -m "test: verify delivery gates and immutable image selection"
git add docs/PHASE11-DELIVERY.md docs/adr/0003-deploy-by-sha-and-digest.md
git commit -m "docs: explain publishing release and digest deployment"
git push -u origin feat/delivery-workflows
```

## PR

Base: dev. Compare: feat/delivery-workflows.

Title: ci: add gated GHCR publishing and Kubernetes release delivery

Description:

Publishing needs an explicit test gate and a traceable deployment artifact.
This PR reuses the complete CI suite before building/scanning both application
images and generating Syft SBOMs. It publishes SHA tags to GHCR, passes digest
outputs to an ephemeral Kubernetes deployment, runs migrations and checks the
application through Ingress. Version releases use the same gates before release
notes and SBOM assets are published.

Validation: delivery helper tests, actionlint and production Kustomize render.
Live publishing/deployment will be verified on the first main CD run. Earlier
scaling evidence and local manifests remain intact.

Add `Related to #` followed by the actual new Issue number. Since the PR targets
dev, use the Development sidebar to link it if available; do not rely on an
automatic closing keyword to close an issue before live evidence exists.

Ask your partner to review actual changes and validation. Merge after all CI
checks pass and review is approved. The new check is Delivery workflow validation.

## First real CD run

After the final reviewed dev-to-main PR is merged, Actions -> CD must show:
1. Full suite: all six CI jobs green.
2. Build, scan, SBOM and publish: green.
3. Deploy published images to temporary Kubernetes: green.

A merge into dev runs CI only. It will not publish or run CD. Do not create an
early main merge solely to label Phase 11 complete; finish final documentation
and integration fixes, then validate delivery as part of the final release.

Packages appear under the repository owner's GitHub Packages page:
- ghcr.io/muhammadabdullah8741/civicpulse-backend
- ghcr.io/muhammadabdullah8741/civicpulse-frontend

The OCI source label links newly published packages to the repository. Existing
packages may need their Manage Actions access setting to grant this repository
access. A 403 is a permissions/configuration failure, not a reason to hard-code
a token. New GHCR packages may be private; the CI cluster supports private pulls.
Choose package visibility deliberately if instructors need anonymous access.

Download delivery-images and delivery-deployment artifacts, save the successful
run URL, and record the commit and both digest references. Temporary clusters
are deleted; their application URL is not a persistent public deployment.

## Final version release (later, after main CD is green)

Use a new version, normally v1.0.0 for the first release. Do not move an existing
tag. Tag the reviewed main commit only after final verification. Pushing that
tag starts Release: validation -> full delivery -> generated release notes.
It publishes v1.0.0 and 1.0.0 image tags plus SHA; it does not move latest.
Wait for green and inspect the release assets before closing the delivery issue.

## Troubleshooting

- CI failure: fix that failure; publishing/deployment should be skipped.
- GHCR 403: check repository package access and organization Actions policy.
- Trivy finds a newly fixable vulnerability: update the affected dependency or
  base image, rebuild and rerun; never disable the scan to get a green badge.
- k3d download/image pull timeout: rerun once after checking the error. Logs and
  deployment artifacts distinguish network errors from application readiness.
- ImagePullBackOff: inspect the events artifact, package permissions and digest.
- Migration failure: inspect the job log in Actions. Never delete your local PVCs.
- Smoke failure: inspect smoke output and rendered Ingress. The runner uses
  civicpulse.localhost:8082 mapped locally, separate from your laptop.
- Existing release version: create a new version after the fix; keep old assets.

## Validation scope

Local helper tests and syntax validation do not prove that GitHub package
permissions, hosted runners or registry pulls work. Only a successful recorded
CD/Release run provides that evidence. No remote run is claimed in this document.
