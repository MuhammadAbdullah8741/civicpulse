# Final evidence index

The existing scaling JSON/CSV/logs and SVG charts are real recorded runs.
The files listed below must be captured from the team's actual environment.
Do not substitute generated screenshots or claim that a blank checklist passed.

| File | Capture |
|---|---|
| branch-protection.png | main protection requiring PR, CI and partner approval |
| blocked-ci.png | Deliberately failing test in a real PR and blocked merge button |
| fixed-ci.png | Same PR after fixing the test, with green checks |
| merge-conflict.png | Real code conflict and its markers |
| merge-resolution.png | Reviewed resolution and resulting merge |
| frontend-submit.png | Synthetic submitted complaint with triage/provider visible |
| frontend-dashboard.png | Filters, pagination and status actions |
| frontend-stats.png | Counts, X-Cache state and provider outcomes |
| network-isolation.txt | Frontend database connection attempt fails; backend check succeeds |
| rollback.txt | Both imperative rollback and declarative previous-overlay application |

Save screenshots here under these filenames, or update the paths in
../../submission.json to match real evidence already saved elsewhere.
Also record five Issue-linked, reviewed merged PR URLs in that JSON.

Add 2-4 sentences below describing the real merge conflict: the two intended
changes, the chosen combined result, and why it preserves behavior. This must
be written after observing your actual conflict; no conflict is claimed here.
