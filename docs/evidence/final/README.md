# Final evidence index

Screenshots are original captures. Their descriptions below distinguish what
is visible from what requires checking the linked GitHub pages.

| File | Evidence and limitations |
|---|---|
| frontend-submit.png | Successful synthetic complaint submission and triage result |
| frontend-dashboard.png | Complaint list, filters and status controls |
| dashboard-status-examples.png | Additional complaint status examples |
| frontend-stats.png | Aggregate counts and displayed cache information |
| frontend-provider-outcomes.png | Provider, latency and recent outcomes |
| CivicPulse-API.png | Swagger API documentation |
| branch-protection.png | Required PR approval and Backend tests check in the captured settings |
| review-required.png | Merge blocked by missing approval while checks were green |
| initial-backend-check.png | Initial successful backend check |
| ci-failure-log.png | Deliberately incorrect test expectation and its actual failure |
| blocked-ci.png | Required CI failed and merging was blocked; approval was also missing |
| fixed-ci.png | Corrected job rows are green; overall page still displays Checks pending |
| merge-conflict.png | Actual content conflict in ErrorBoundary.tsx |
| merge-resolution.png | Resolution merge commit and clean working tree |
| cd-success.png | Successful main CD workflow |
| RELEASE.CHECK.png | Successful v1.0.1 release workflow |
| pr2.checks.png | PR 2 checks |
| pr8.checks.png | PR 8 checks |
| pr20.checks.png | PR 20 checks |
| pr22.checks.png | PR 22 checks |
| pr35.checks.png | PR 35 checks |
| issue-pr-comments.png | Issues overview; actual partner reviews must be checked on the PR pages |
| Groq-useage-limit.png | Groq usage dashboard, not numerical account rate limits |
| Groq-useage-limit-2.png | Groq request activity, not numerical account rate limits |
| backend-context-size.txt | Sum of file sizes before and after ignore exclusions, not Docker image size |
| kubernetes-persistence.txt | Database pod replacement with unchanged complaint count and row fingerprint |
| network-isolation.txt | Frontend cannot connect to PostgreSQL; backend connectivity succeeds |
| rollback.txt | Recorded imperative and declarative rollback verification |
| rollback-images.json | Image references used for rollback |
| rollback-previous-overlay.yaml | Previous manifest used for declarative restoration |

## Merge-conflict resolution

One branch explained that saved reports remain available after a page reload.
The other warned that unsaved changes may be lost.
The resolution retained both messages because they describe different data
states and together provide complete recovery guidance.

## Remaining evidence limitations

The fixed-CI screenshot shows successful job rows but not a completed overall
workflow status. A final completed-check capture would strengthen this evidence.
The Issues overview does not itself establish partner review comments.
The Groq captures establish usage, not numerical account rate limits.

## Video - pending

The video is being edited. When complete, record its accessible unlisted URL,
actual duration and whether both partners speak in docs/submission.json.
The assignment limits the video to 300 seconds.

Until then, leave demo_video_url empty, demo_duration_seconds at 0 and
both_partners_speak false.

## Audit status

docs/SUBMISSION-AUDIT.md describes an earlier snapshot and is retained as
historical evidence. This index records the updated evidence inventory.
Credential rotation remains unconfirmed; credentials_rotated remains false.
