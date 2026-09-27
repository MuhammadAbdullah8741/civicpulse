"""Build, scan and publish both application images after the full CI gate."""
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

SYFT_IMAGE = "ghcr.io/anchore/syft:v1.52.0"


def run(*args, **kwargs):
    return subprocess.run(args, check=True, text=True, **kwargs)


def publication_tags(sha, ref, version):
    if not re.fullmatch(r"[0-9a-f]{40}", sha):
        raise ValueError("Expected a full Git commit SHA")
    tags = [sha]
    if version:
        if not re.fullmatch(r"v(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)", version):
            raise ValueError("Expected a stable semantic version")
        if ref != f"refs/tags/{version}":
            raise ValueError("Release tag does not match this workflow ref")
        tags.extend([version, version[1:]])
    elif ref == "refs/heads/main":
        tags.append("latest")
    return tags


def digest_for(repository, references):
    matches = [ref for ref in references if ref.startswith(repository + "@sha256:")]
    if len(matches) != 1 or not re.fullmatch(r".+@sha256:[0-9a-f]{64}", matches[0]):
        raise ValueError(f"Cannot uniquely identify the pushed digest for {repository}")
    return matches[0]


def main():
    # Refuse accidental publication from a student's local shell.
    if os.environ.get("GITHUB_ACTIONS") != "true":
        raise RuntimeError("Publishing runs in GitHub Actions, after the CI gate")
    sha = run("git", "rev-parse", "HEAD", capture_output=True).stdout.strip()
    if sha != os.environ["GITHUB_SHA"]:
        raise RuntimeError("Checkout does not match the tested workflow commit")
    repository = os.environ["GITHUB_REPOSITORY"]
    owner = repository.split("/", 1)[0].lower()
    tags = publication_tags(sha, os.environ["GITHUB_REF"], os.environ.get("RELEASE_TAG", ""))
    output = Path("delivery-artifacts")
    output.mkdir(exist_ok=True)
    names = {name: f"ghcr.io/{owner}/civicpulse-{name}" for name in ("backend", "frontend")}
    images = {name: f"{image}:{sha}" for name, image in names.items()}
    for name, image in images.items():
        run("docker", "build", "--label", f"org.opencontainers.image.source=https://github.com/{repository}",
            "--label", f"org.opencontainers.image.revision={sha}", "-t", image, f"./{name}")
    # Scan these exact local images. No publishing until BOTH have passed.
    run(sys.executable, "scripts/scan_images.py", "--output", str(output / "security"), *images.values())
    for name, image in images.items():
        with tempfile.TemporaryDirectory(prefix="civicpulse-sbom-") as folder:
            run("docker", "save", "--output", str(Path(folder) / "image.tar"), image)
            with (output / f"{name}.spdx.json").open("w", encoding="utf-8") as stream:
                run("docker", "run", "--rm", "--mount", f"type=bind,source={folder},target=/scan,readonly",
                    SYFT_IMAGE, "docker-archive:/scan/image.tar", "-o", "spdx-json", stdout=stream)
        sbom = json.loads((output / f"{name}.spdx.json").read_text())
        if not sbom.get("spdxVersion") or not sbom.get("packages"):
            raise RuntimeError(f"Invalid or empty Syft SBOM for {name}")
    result = {"commit": sha, "source": repository, "tags": tags, "images": {}}
    for name, image in images.items():
        for tag in tags:
            target = f"{names[name]}:{tag}"
            if target != image:
                run("docker", "tag", image, target)
            run("docker", "push", target)
        inspected = json.loads(run("docker", "image", "inspect", image, capture_output=True).stdout)[0]
        immutable = digest_for(names[name], inspected.get("RepoDigests", []))
        result["images"][name] = {"reference": immutable, "sha_tag": image, "local_id": inspected["Id"]}
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as stream:
            stream.write(f"{name}_image={immutable}\n{name}_digest={immutable.split('@')[1]}\n")
    (output / "images.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as stream:
        stream.write(f"## Published images\n\nCommit: `{sha}`\n\n")
        for name, details in result["images"].items():
            stream.write(f"- {name}: `{details['reference']}`\n")
        stream.write("\nSBOMs and scan reports are in the delivery-images artifact.\n")


if __name__ == "__main__":
    main()
