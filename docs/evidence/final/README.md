# Final evidence index

These are original user captures copied without image-content changes.

| File | What it proves / limits |
|---|---|
| frontend-submit.png | Successful synthetic report with category, priority, summary, provider and reference |
| frontend-dashboard.png | Complaint list, filters and status controls; pagination is outside this capture |
| frontend-stats.png | Aggregate counts, X-Cache MISS, 0/5 runtime triage hit rate |
| frontend-provider-outcomes.png | Active simulated provider and recent latency/outcome records |
| branch-protection.png | PR plus one approval required; only Backend tests is listed as a required check in this capture |
| cd-success.png | Main CD full suite, scan/SBOM/publication and temporary Kubernetes deployment succeeded |
| review-required.png | Earlier PR blocked for missing approval while CI was green; NOT a failed-CI screenshot |
| initial-backend-check.png | Initial PR backend check passed; NOT the fixed half of a deliberate red-to-green demonstration |
| dashboard-status-examples.png | Additional dashboard with terminal and non-terminal statuses |
| network-isolation.txt | Recorded frontend-to-database failure and backend-to-database success |
| rollback.txt | Recorded imperative and declarative image restoration |
| rollback-images.json | Source and image references used by the controlled rollback |
| rollback-previous-overlay.yaml | Prior manifest used for declarative restoration; no Secret object included |

Still absent: blocked-ci.png, fixed-ci.png, merge-conflict.png and
merge-resolution.png. Capture actual events; do not relabel unrelated screenshots.
After performing the real conflict, add 2–4 sentences explaining the competing
changes, chosen resolution and why it preserves the intended behavior.

The source screenshots remain in the user's screenshots/ folder. The corrected
copies above match paths in docs/submission.json. See ../../SUBMISSION-AUDIT.md.
