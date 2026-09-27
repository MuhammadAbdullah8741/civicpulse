"""Mechanical submission checks, not a grader. --strict requires external evidence too."""
import argparse
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = ["README.md", "docs/RUNBOOK.md", "docs/ENGINEERING-NOTES.md", "docs/AI-USAGE.md",
            "docs/FINAL-SUBMISSION.md", "docs/submission.json", "scripts/Start-Local.ps1",
            ".github/workflows/ci.yml", ".github/workflows/cd.yml", ".github/workflows/release.yml",
            "docs/adr/0001-provider-interface.md", "docs/adr/0002-frontend-runtime-config.md",
            "docs/adr/0003-deploy-by-sha-and-digest.md", "docs/adr/0004-pii-and-data-governance.md",
            "docs/evidence/scaling/COMPARISON.md", "docs/evidence/scaling/rollout/result.json"]
TOKEN = r"(gsk_[A-Za-z0-9]{30,}|gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,}|-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----)"


def git(*args):
    return subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--history", action="store_true", help="Also scan all reachable commits for common token formats and secret filenames")
    args = parser.parse_args()
    errors, pending = [], []
    for name in REQUIRED:
        if not (ROOT / name).is_file() or (ROOT / name).stat().st_size == 0:
            errors.append("Missing/empty file: " + name)
    config = {}
    try:
        config = json.loads((ROOT / "docs/submission.json").read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        errors.append("docs/submission.json is missing or invalid JSON")
    notes = ROOT / "docs/ENGINEERING-NOTES.md"
    if notes.exists() and "**Student completion required:**" in notes.read_text():
        pending.append("Complete the personal failure reflection in Engineering Notes question 8")
    for key in ("cd_run_url", "release_url", "demo_video_url"):
        if not str(config.get(key, "")).startswith("https://"):
            pending.append("Record a real " + key)
    for key in ("branch_protection", "blocked_ci", "fixed_ci", "merge_conflict", "merge_resolution",
                "frontend_submit", "frontend_dashboard", "frontend_stats", "network_isolation", "rollback"):
        name = config.get("evidence", {}).get(key)
        if not name or not (ROOT / name).is_file():
            pending.append("Add actual evidence: " + key)
    prs = config.get("reviewed_issue_pr_urls", [])
    if len(set(prs)) < 5 or any("/pull/" not in str(url) for url in prs):
        pending.append("List at least five distinct reviewed, Issue-linked merged PR URLs")
    if config.get("credentials_rotated") is not True:
        pending.append("Confirm rotation of credentials previously shared in chat")
    if config.get("demo_duration_seconds", 0) not in range(1, 301) or config.get("both_partners_speak") is not True:
        pending.append("Record a <=300-second demo with both partners speaking")
    try:
        result = json.loads((ROOT / "docs/evidence/scaling/rollout/result.json").read_text())
        if any(result.get(key) != 0 for key in ("load_exit_code", "rollout_exit_code", "failed_request_rate", "dropped_iterations")):
            errors.append("Rolling-update result is not passing")
    except (OSError, ValueError):
        errors.append("Cannot read rolling-update result")
    tracked = git("ls-files")
    if tracked.returncode:
        pending.append("Run from the real Git checkout to check commits and tracked files")
    else:
        for name in tracked.stdout.splitlines():
            p = Path(name)
            if (p.name == ".env" or p.name.startswith(".env.") and p.name != ".env.example"
                    or p.suffix in {".pem", ".key"}):
                errors.append("Tracked secret-like filename: " + name)
        scan = git("grep", "-I", "-l", "-E", TOKEN, "--", ".", ":(exclude)scripts/check_submission.py")
        if scan.returncode == 0:
            errors.append("Possible token/private key in tracked files; inspect locally: " + ", ".join(scan.stdout.splitlines()))
        elif scan.returncode != 1:
            errors.append("Tracked-file secret scan could not finish")
        count = git("rev-list", "--count", "--no-merges", "HEAD")
        if count.returncode == 0 and int(count.stdout.strip()) < 35:
            errors.append("Fewer than 35 non-merge commits")
        counts = git("shortlog", "-sn", "--no-merges", "HEAD")
        print("Contribution counts (review aliases and substantive work manually):\n" + counts.stdout)
        authors = config.get("partner_git_authors", [])
        if len(authors) != 2 or not all(authors):
            pending.append("Set two partner_git_authors entries, each a list of actual Git author aliases")
        else:
            rows = [line.strip().split(None, 1) for line in counts.stdout.splitlines() if line.strip()]
            total = sum(int(row[0]) for row in rows)
            for aliases in authors:
                own = sum(int(row[0]) for row in rows if row[1] in aliases)
                if not total or own / total < 0.35:
                    errors.append("Partner below 35% of non-merge commits: " + ", ".join(aliases))
        if args.history:
            commits = git("rev-list", "--all")
            if commits.returncode:
                errors.append("Cannot enumerate Git history")
            for commit in commits.stdout.splitlines():
                names = git("ls-tree", "-r", "--name-only", commit)
                secret_names = [n for n in names.stdout.splitlines() if Path(n).name == ".env" or
                                (Path(n).name.startswith(".env.") and Path(n).name != ".env.example") or
                                Path(n).suffix in {".pem", ".key"}]
                scan = git("grep", "-I", "-l", "-E", TOKEN, commit, "--", ".", ":(exclude)scripts/check_submission.py")
                if secret_names or scan.returncode == 0:
                    errors.append(f"Possible historic secret at {commit[:12]}; inspect locally, rotate and document")
                    break
                if scan.returncode not in (0, 1) or names.returncode:
                    errors.append("History scan could not finish")
                    break
            print("History scan checks common token patterns/filenames, not every possible credential.")
    for message in errors:
        print("FAIL:", message)
    for message in pending:
        print("PENDING:", message)
    print(f"Result: {len(errors)} failures; {len(pending)} pending evidence items.")
    return 1 if errors or (args.strict and pending) else 0


if __name__ == "__main__":
    raise SystemExit(main())
