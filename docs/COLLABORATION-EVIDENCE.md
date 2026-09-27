# Capture missing collaboration evidence only if it does not already exist

Reuse real screenshots/PRs first. These are actual reviewed repository changes,
not simulated screenshots. Work under your own configured Git identity.

## Red CI blocks a PR, then green in the same PR

On feat/final-submission, after the normal verification and commits, create a
temporary deliberately wrong expectation for a real terminal-state rule:

```powershell
@'
from app.schemas import Status
from app.services.status import allowed_transitions


def test_resolved_reports_are_terminal():
    # Deliberately wrong for the documented red-to-green CI demonstration.
    assert allowed_transitions(Status.RESOLVED) == [Status.OPEN]
'@ | Set-Content -Encoding ascii backend/tests/test_ci_gate_evidence.py
git add backend/tests/test_ci_gate_evidence.py
git commit -m "test: demonstrate CI rejection of an invalid terminal-state expectation"
git push -u origin feat/final-submission
```

Open the PR into dev, link its Issue, wait for Backend tests to fail, and capture
both the failed test and the blocked merge button in blocked-ci.png. The Backend
tests check must actually be required by protection; a red check alone does not
prove that merging was blocked. Do not merge the failing revision.

Correct the test in the same branch/PR:

```powershell
@'
from app.schemas import Status
from app.services.status import allowed_transitions


def test_resolved_reports_are_terminal():
    assert allowed_transitions(Status.RESOLVED) == []
'@ | Set-Content -Encoding ascii backend/tests/test_ci_gate_evidence.py
git add backend/tests/test_ci_gate_evidence.py
git commit -m "test: correct terminal-state expectation after CI gate demonstration"
git push
```

Wait for every check to pass and capture fixed-ci.png. The new test raises the
expected backend total from 102 to 103. Partner review should explain the real
state-machine behavior and confirm the failing revision was not merged.

## Real merge conflict on error-recovery UI

Do this after the Phase 12 PR is merged if you still lack genuine conflict
evidence. Link the PRs to an Issue describing both intended recovery messages.
From a clean, updated dev, create both branches at the same base:

```powershell
git switch dev
git pull --ff-only origin dev
git branch feat/error-recovery-warning
git switch -c feat/error-recovery-copy
$path = 'frontend/src/components/ErrorBoundary.tsx'
$text = Get-Content $path -Raw
$text.Replace('Please reload the page to try again.', 'Reload the page; your saved reports remain available.') | Set-Content -Encoding ascii $path
git add frontend/src/components/ErrorBoundary.tsx
git commit -m "fix: explain saved report recovery after a render failure"
git push -u origin feat/error-recovery-copy
```

Open its PR into dev, run CI, obtain substantive partner review and merge. Then
switch to the second branch (which still has the original paragraph):

```powershell
git switch feat/error-recovery-warning
$path = 'frontend/src/components/ErrorBoundary.tsx'
$text = Get-Content $path -Raw
$text.Replace('Please reload the page to try again.', 'Reload the page to recover. Unsaved changes may be lost.') | Set-Content -Encoding ascii $path
git add frontend/src/components/ErrorBoundary.tsx
git commit -m "fix: warn that unsaved changes are lost when reloading"
git fetch origin
git merge origin/dev
```

The conflicting edits target the same actual rendered paragraph. Capture the
conflict markers in VS Code as merge-conflict.png. Resolve that paragraph to:

```tsx
<p>Reload the page. Saved reports remain available; unsaved changes may be lost.</p>
```

Remove all conflict markers, preserving the surrounding component. Then:

```powershell
npm --prefix frontend run lint
npm --prefix frontend test
npm --prefix frontend run build
git diff --check
git add frontend/src/components/ErrorBoundary.tsx
git commit -m "fix: combine report recovery guidance and unsaved-change warning"
git push -u origin feat/error-recovery-warning
```

Open the second PR into dev. Have your partner inspect the combined paragraph,
review CI and approve. Capture resolution and merge as merge-resolution.png.
Explain in 2-4 sentences that one branch clarified saved-report persistence,
the other warned about browser state, and the combined message preserves both.
Only claim this history after performing it. Add the real evidence and PR URLs
through another reviewed documentation PR before final integration into main.
