# CivicPulse final submission audit

Audited: user-supplied `civicpulse (2).zip` against Assignment 01, sections 2–5.
Snapshot HEAD: `7d549eb0bdecec7d46d4cc7912ab0e0ba6793c2f`;
branch: `docs/submission-evidence`. This is a code/document/evidence audit,
not a mark prediction or an independent rerun of the live deployment.

## Result

The core implementation is substantially present. Submission is NOT complete.
The original checker produced 1 failure and 12 pending items. The failure was
caused by missing author aliases, not an actual below-threshold contribution.
This correction pack fixes those aliases, copies original screenshots to the
expected paths, embeds app screenshots in README, and updates the evidence index.
It does not create missing CI/conflict/video evidence or assert release success.

## Verification and its limits

- Fresh audit run: 76 backend tests passed, 26 service-dependent tests skipped;
  14 delivery-helper tests passed. No live PostgreSQL/Redis, Docker builds,
  Kubernetes deployment or frontend build was rerun in this audit.
- Prior user output: full 102 backend tests passed, coverage 92.34%; live API
  contract and Ingress/Compose smoke checks passed. These are historical runs.
- Supplied CD screenshot shows success for main commit 7d549eb: full suite,
  image build/scan/SBOM/publication and ephemeral Kubernetes deployment.
- Git common-token/secret-filename history scan reported no matches. This is
  NOT a guarantee that history contains no possible secret.
- The uploaded ZIP itself includes a local `.env`. It was excluded from the
  audit working copy and correction ZIP. It is not tracked by the supplied
  Git history scan. Do NOT publicly submit the original whole-folder ZIP.
- PR URLs are recorded, but a local ZIP cannot prove live approvals, substantive
  partner review comments, Issue links, package access or examiner access.

## Rubric review

| Area | Present and supported | Remaining qualification |
|---|---|---|
| A: Collaboration | Feature/dev/main history; many merged PR commits; 71 non-merge commits | Required-check settings incomplete in screenshot; deliberate CI failure/fix and real merge conflict evidence missing; verify each listed PR's Issue and substantive partner comment |
| B: Frontend | React 18/TS, Submit/Dashboard/Stats, OpenAPI-checked client, error boundary, relative /api, tests, runtime proxy | Screenshots fixed by this pack; dashboard screenshot does not show pagination, demonstrate it in video or supplementary capture |
| C: Backend | Routes/services/repositories/providers; validation/status table, health/readiness, metrics/logging, shutdown cleanup; tests | Brief says 'ten endpoints' but its API table lists nine method/path operations; implemented nine listed operations, do not invent a tenth |
| D: Data | Alembic schema, constraints, indexes, seed >=30, named volumes/PVC | Compose persistence is documented; direct before/after row-preservation evidence for PostgreSQL pod deletion not found |
| E: Cache | Stats TTL30/invalidation/X-Cache, Redis distributed limiter/Retry-After, AOF volume | Snapshot's stats screenshot is a valid 0/5 runtime measurement, not the separate controlled 50% benchmark |
| F: AI | Four provider implementations, 10s whole-attempt timeout, one retry on timeout/429/5xx, validated JSON, fallback, content-hash cache, injection tests, PII ADR | Exact account/model rate limits not recorded in docs/TRIAGE.md; video must show triage and fallback |
| G: Docker | Both multi-stage/non-root/pinned bases, ignores, dev mounts, production prebuilt images, two networks, 3 named volumes (Ollama profiled) | Backend before/after build-context measurement missing; frontend runtime measured 70.48 MiB, above approximate 60 MB guidance (builder455.75 MiB); no need to fake smaller numbers |
| H: Kubernetes | Namespace, 2 FE/BE replicas, PostgreSQL StatefulSet/PVC, Redis PVC, Ingress/services, probes/resources, PDB, HPA and VPA Off | Preserve failed load-test results; current manifests and records present, not a fresh live-cluster audit |
| I: CI/CD | Three gated workflows, Trivy/kubeconform, GHCR/SBOM/digest outputs, successful main CD | v1.0.1 release success not supplied; deliberate red/blocked/green proof still absent; require all six relevant PR checks |
| J: Docs/demo | README/diagram/badges/quickstart/API; 4 ADRs; runbook; AI disclosure; eight notes headings | Video absent; Q2 needs lecture-specific rung; Q8 does not establish >1h or initial wrong belief; stale pending statements remain in earlier phase documents |

## Contributions

Non-merge history in this ZIP:
- Umar: umarsidiqui04 = 30 / 71 = 42.25%.
- Abdullah: M Abdullah24 + M.Abdullah16 + Muhammad Abdullah1 = 41 / 71 =57.75%.
Both exceed 35% after combining the previously confirmed aliases.
Plain `git shortlog -sn HEAD` including merges reports Umar39 and Abdullah50
combined (89 total); both also exceed35%. Save the actual command output for
submission. Counts alone do not prove substantive contribution or review.

## Exact remaining metadata

`docs/submission.json`:
- release_url: empty. Fill only after actual v1.0.1 release success.
- demo_video_url: empty.
- demo_duration_seconds: 0. Replace with actual final recording length <=300.
- both_partners_speak: false. Set true only after both are audible in recording.
- credentials_rotated: false; user expressly declined rotation. Keep truthful.
  This is a custom-checker pending item. The manual's explicit mandatory
  rotation/deduction condition is a secret in Git history; none was identified
  by this limited scan. Chat exposure remains a real security concern.
- cd_run_url: filled with run36337677592; screenshot supports main CD success.
- Five PR URLs are filled: #2,#8,#20,#22,#35. Verify merged status, linked Issue
  AND substantive partner comment for each; an approval icon alone is not the
  rubric's full review-comment evidence.
- partner_git_authors: corrected in this pack; preserve all three Abdullah aliases.

Expected checker AFTER this pack, before further work: 0 failures / 8 pending:
release URL, demo URL, blocked CI, fixed CI, merge conflict, merge resolution,
credential rotation, demo duration/both-speaker confirmation. A clean checker
would still not certify all rubric details below.

## Remaining evidence and settings, in order

1. GitHub main protection: the supplied screenshot lists only Backend tests.
   Add these six exact PR check names and save protection: Backend tests,
   Database integration, Frontend checks, Container security, Kubernetes
   manifests, Delivery workflow validation. Require PR + >=1 approval and
   prevent bypass/direct pushes under the applicable protection settings.
   Capture the saved configuration including selected checks and bypass controls.
   Current screenshot does not establish those controls or all six checks.
2. Deliberate CI demonstration: a separate Issue-linked PR with an intentionally
   wrong test; capture red required check AND blocked merge; fix in SAME PR,
   capture green, obtain review and merge. Do not merge the failing revision.
   Supplied initial-backend-check.png and review-required.png are not substitutes.
3. Real code merge conflict: two different edits to the same code line on
   branches from a common base; capture actual conflict markers, resolve,
   validate, commit and review/merge. Capture resolution/merge and add 2–4
   sentences explaining the chosen version. No such event was found in this ZIP.
4. Release: verify v1.0.1 workflow and actual GitHub release page; record URL.
   Main CD success does not alone prove tag-release success. No force-moving tags.
5. Verify the five listed PRs and package URLs/access as described above.
6. Record the full demonstration below, upload unlisted/accessible to examiners,
   fill actual metadata, then submit evidence through a reviewed PR into main.

## Documentation tasks the checker misses

- docs/ENGINEERING-NOTES.md question2 still says to match Lecture03 slide32.
  Supply the exact lecture rung/next rung; lecture slides were not available.
- Question8 now has prose, so checker considers the placeholder removed, but
  actual >1h investigation duration and initial wrong belief are not established.
  Do not invent either. This pack restores technical evidence references only.
- docs/TRIAGE.md 'Exact account limits must be recorded' remains unfinished:
  record the date/model/RPM/TPM/etc actually shown for the team's Groq account,
  with its limits-page reference, never a key.
- Earlier documents have historical pending wording: docs/AI-USAGE.md,
  docs/BACKEND-OPERATIONS.md and docs/TRIAGE.md. Add a dated final verification
  note referring to102tests/92.34% and actual mainCD; leave unverified release
  and reviews explicitly unverified. docs/DATABASE-NOTES.md 'Remaining work'
  refers to APIs/readiness already implemented; mark that paragraph historical.
- Backend .dockerignore exists but before/after numeric context evidence is
  absent. Measure on the actual laptop; do not reuse frontend numbers.
- Frontend context evidence is114.82MiB before /0.21MiB after; builder455.75MiB,
  runtime70.48MiB uncompressed. These are recorded facts, not placeholder values.
- Root LICENSE file shown in the reference layout is absent. No license is chosen
  automatically because that is an ownership/licensing decision, not a filename fix.
- Keep intentional templates: .env.example, k8s/secret.example.yaml placeholder
  secrets and release-required image references rendered by deployment scripts.
  Replacing those with real credentials is wrong. Instructional example commands
  in phase guides are not all unfinished application placeholders.

## Video: corrected scope from the manual

My earlier spoken script was incomplete. A <=5-minute, both-partners video must
cover clean clone -> running system, AI triage, fallback, failed frontend-to-DB
network access, HPA scaling, and BOTH rollback mechanisms executing on video.
Existing screenshots/logs supplement the video; merely reading them does not
meet an explicit on-video command demonstration. Do not claim a simulated
response came from Groq. Existing chat evidence contains a successful live Groq
call and an earlier live llm:ollama result; re-downloading Ollama is not needed
for the minimum >=3 working provider rubric.

Suggested timing (prepare honest recordings, shorten waiting with labelled cuts):
0:00–0:40 clean clone and one-command startup with seed; 0:40–1:35 submission,
dashboard and stats;1:35–2:10 hosted triage and controlled provider-failure fallback;
2:10–2:35 real failing frontend DB connection plus successful backend control;
2:35–3:10 HPA scale-out capture/chart and honest lag results;3:10–4:40 both
imperative and declarative rollback commands and readiness/application recovery;
4:40–5:00 successful delivery/release and brief closing. Both partners speak.
Brief section2.3 also asks persistence demonstration: retain a before/after
record/count across Compose down/up (NO -v) and PostgreSQL pod replacement
(NO PVC deletion), and include clear evidence or short video cuts.

## Scope boundaries / optional bonus

No separate login-based customer/admin apps are required by the supplied brief;
Submit and operations Dashboard/Stats satisfy its view structure. Role-based
access control is not implemented and should not be claimed.
No Cosign signing/verification, ArgoCD/Flux, Grafana dashboard or OpenTelemetry
bonus is established. Digest deployment exists, but the combined digest+Cosign
bonus is not fully implemented. Intro mentions signed images while detailed
rubric places Cosign in bonus: disclose absence, do not claim signed images.
The zero-failure 30/s rollout evidence exists, with the honest same-bytes/new-tag
limitation. It is not proof of unlimited capacity; 100/s threshold failures remain.

## Packaging and final check

This correction ZIP contains documentation and copied original screenshots only;
no .env, .git, node_modules, runtime secrets, fabricated evidence or app code.
Extract into repository root on docs/submission-evidence, review git diff, and
stage explicitly README.md and changed docs. Preserve unrelated local changes.
After recording missing evidence, run `python scripts/check_submission.py
--strict --history`. Credential rotation remains pending under the user's choice.
Submit on time with an honest limitations statement rather than filling false
URLs or marking unperformed work complete. Do not submit the original ZIP with
its local environment file.
