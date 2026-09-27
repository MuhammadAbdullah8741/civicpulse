"""Deploy the published digests to the disposable CI cluster, never the local cluster."""
import base64
import json
import os
from pathlib import Path
import re
import secrets
import subprocess

CONTEXT = "k3d-civicpulse-ci"


def kubectl(*args, **kwargs):
    return subprocess.run(["kubectl", "--context", CONTEXT, *args], check=True, text=True, **kwargs)


def apply_object(value):
    # Secret values travel via stdin, never command-line arguments or evidence files.
    kubectl("apply", "-f", "-", input=json.dumps(value))


def render_images(manifest, backend, frontend, migration=False):
    for value in (backend, frontend):
        if not re.fullmatch(r"ghcr\.io/[a-z0-9._/-]+@sha256:[0-9a-f]{64}", value):
            raise ValueError("Deployment requires a GHCR image digest, never latest or a mutable tag")
    for name, replacement in (("backend", backend), ("frontend", frontend)):
        if migration and name == "frontend":
            continue
        pattern = rf"(?m)^([ \t]*(?:-[ \t]+)?image:[ \t]*)civicpulse-{name}:[^\s]+[ \t]*$"
        manifest, count = re.subn(pattern, lambda match: match[1] + replacement, manifest)
        if count != 1:
            raise ValueError(f"Expected exactly one {name} image, found {count}; review the manifest")
    return manifest


def main():
    if os.environ.get("GITHUB_ACTIONS") != "true":
        raise RuntimeError("This command is restricted to the disposable GitHub Actions deployment")
    output = Path("delivery-evidence")
    output.mkdir(exist_ok=True)
    backend, frontend = os.environ["BACKEND_IMAGE"], os.environ["FRONTEND_IMAGE"]
    rendered = subprocess.run(["kubectl", "kustomize", "k8s/overlays/prod"],
                              check=True, text=True, capture_output=True).stdout
    manifest = render_images(rendered, backend, frontend)
    migration = render_images(Path("k8s/jobs/migrate.yaml").read_text(), backend, frontend, migration=True)
    # Only this throwaway cluster receives the short-lived registry token.
    kubectl("apply", "-f", "k8s/base/namespace.yaml")
    auth = base64.b64encode(f"{os.environ['GITHUB_ACTOR']}:{os.environ['REGISTRY_TOKEN']}".encode()).decode()
    registry_config = json.dumps({"auths": {"ghcr.io": {"auth": auth}}})
    apply_object({"apiVersion": "v1", "kind": "Secret", "metadata": {
        "name": "ghcr-pull", "namespace": "civicpulse"}, "type": "kubernetes.io/dockerconfigjson",
        "stringData": {".dockerconfigjson": registry_config}})
    apply_object({"apiVersion": "v1", "kind": "ServiceAccount", "metadata": {
        "name": "default", "namespace": "civicpulse"}, "imagePullSecrets": [{"name": "ghcr-pull"}]})
    apply_object({"apiVersion": "v1", "kind": "Secret", "metadata": {
        "name": "civicpulse-secrets", "namespace": "civicpulse"}, "type": "Opaque",
        "stringData": {"POSTGRES_PASSWORD": secrets.token_hex(32), "GROQ_API_KEY": ""}})
    (output / "production-rendered.yaml").write_text(manifest, encoding="utf-8")
    (output / "migration-rendered.yaml").write_text(migration, encoding="utf-8")
    kubectl("apply", "-f", "-", input=manifest)
    for resource in ("statefulset/database", "deployment/cache"):
        kubectl("-n", "civicpulse", "rollout", "status", resource, "--timeout=600s")
    kubectl("apply", "-f", "-", input=migration)
    try:
        kubectl("-n", "civicpulse", "wait", "--for=condition=complete", "job/civicpulse-migrate", "--timeout=300s")
    finally:
        kubectl("-n", "civicpulse", "logs", "job/civicpulse-migrate")
    for resource in ("deployment/backend", "deployment/frontend"):
        kubectl("-n", "civicpulse", "rollout", "status", resource, "--timeout=600s")
    kubectl("-n", "kube-system", "rollout", "status", "deployment/traefik", "--timeout=300s")
    kubectl("-n", "kube-system", "rollout", "status", "deployment/metrics-server", "--timeout=180s")
    kubectl("-n", "civicpulse", "exec", "deployment/backend", "--", "python", "-m", "app.seed")
    pods = kubectl("-n", "civicpulse", "get", "pods", "-o", "json", capture_output=True).stdout
    (output / "pods.json").write_text(pods, encoding="utf-8")
    (output / "deployed-images.json").write_text(json.dumps({
        "commit": os.environ["GITHUB_SHA"], "backend": backend, "frontend": frontend
    }, indent=2) + "\n", encoding="utf-8")
    with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as stream:
        stream.write("## Kubernetes deployment\n\nProduction overlay deployed by digest to k3d-civicpulse-ci. "
                     "The following Ingress smoke step determines end-to-end success.\n")


if __name__ == "__main__":
    main()
