"""Demonstrate two rollback methods on the local assignment cluster, preserving data."""
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys

CONTEXT = "k3d-civicpulse"
ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-demo", action="store_true", required=True,
                        help="Explicitly authorize a controlled local backend rolling replacement and rollback")
    parser.parse_args()
    output = ROOT / "docs/evidence/final"
    output.mkdir(parents=True, exist_ok=True)
    log = output / "rollback.txt"
    if log.exists():
        raise SystemExit("rollback.txt already exists; preserve it or rename it before a new run")

    def command(*args):
        result = subprocess.run(args, cwd=ROOT, text=True, capture_output=True)
        with log.open("a", encoding="utf-8") as stream:
            stream.write("$ " + " ".join(args) + "\n" + result.stdout + result.stderr + "\n")
        print(result.stdout, end="")
        if result.returncode:
            print(result.stderr, file=sys.stderr)
            raise SystemExit(f"Failed; inspect {log}. Cluster/data were not deleted.")
        return result.stdout.strip()

    def k(*args):
        return command("kubectl", "--context", CONTEXT, "-n", "civicpulse", *args)

    def wait():
        k("rollout", "status", "deployment/backend", "--timeout=240s")

    if command("git", "status", "--porcelain"):
        raise SystemExit("Commit the phase files first, then deploy that clean commit before this demo")
    sha = command("git", "rev-parse", "HEAD")
    references = {}
    for name in ("backend", "frontend"):
        obj = json.loads(k("get", "deployment", name, "-o", "json"))
        references[name] = next(c["image"] for c in obj["spec"]["template"]["spec"]["containers"] if c["name"] == name)
        if references[name] != f"civicpulse-{name}:{sha}":
            raise SystemExit("Run Deploy-Kubernetes.ps1 from this clean commit first; source and live images must match")
    manifest = command("kubectl", "kustomize", "k8s/overlays/dev")
    for name, image in references.items():
        manifest, count = re.subn(rf"(?m)^([ \t]*(?:-[ \t]+)?image:[ \t]*)civicpulse-{name}:dev[ \t]*$",
                                 lambda match: match[1] + image, manifest)
        if count != 1:
            raise SystemExit("Unexpected overlay image layout")
    previous = output / "rollback-previous-overlay.yaml"
    previous.write_text(manifest + "\n", encoding="utf-8")
    (output / "rollback-images.json").write_text(json.dumps({"source_commit": sha, **references,
        "note": "Controlled same-bytes image-tag change; demonstrates mechanics, not a functional regression."}, indent=2))
    candidate = references["backend"] + "-rollback-demo"
    command("docker", "tag", references["backend"], candidate)
    command("k3d", "image", "import", candidate, "-c", "civicpulse")
    k("set", "image", "deployment/backend", "backend=" + candidate)
    wait()
    k("rollout", "undo", "deployment/backend")
    wait()
    k("set", "image", "deployment/backend", "backend=" + candidate)
    wait()
    k("apply", "-f", str(previous))
    wait()
    current = json.loads(k("get", "deployment", "backend", "-o", "json"))
    actual = next(c["image"] for c in current["spec"]["template"]["spec"]["containers"] if c["name"] == "backend")
    if actual != references["backend"]:
        raise SystemExit("Rollback image verification failed")
    with log.open("a", encoding="utf-8") as stream:
        stream.write("PASS: imperative undo and declarative previous-overlay application restored the recorded image.\n")
    print("PASS: both rollback mechanisms restored the recorded image. Run the Ingress smoke test next.")


if __name__ == "__main__":
    main()
