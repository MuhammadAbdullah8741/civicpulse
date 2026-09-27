"""Install the pinned Linux amd64 k3d binary after official checksum verification."""
import hashlib
import os
from pathlib import Path
import platform
import re
import urllib.request

VERSION = "v5.8.3"
BASE = f"https://github.com/k3d-io/k3d/releases/download/{VERSION}"


def main():
    if os.environ.get("GITHUB_ACTIONS") != "true" or platform.system() != "Linux":
        raise RuntimeError("This installer is for the Linux CI runner; use Install-KubernetesTools.ps1 locally")
    name = "k3d-linux-amd64"
    with urllib.request.urlopen(f"{BASE}/checksums.txt", timeout=60) as response:
        checksum_text = response.read().decode()
    matches = re.findall(r"^([0-9a-fA-F]{64})\s+\*?(?:_dist/)?k3d-linux-amd64\s*$", checksum_text, re.M)
    if len(matches) != 1:
        raise RuntimeError("Official k3d checksum entry not found uniquely")
    with urllib.request.urlopen(f"{BASE}/{name}", timeout=120) as response:
        content = response.read()
    if hashlib.sha256(content).hexdigest() != matches[0].lower():
        raise RuntimeError("k3d checksum verification failed")
    directory = Path(os.environ["RUNNER_TEMP"]) / "civicpulse-tools"
    directory.mkdir(exist_ok=True)
    target = directory / "k3d"
    target.write_bytes(content)
    target.chmod(0o755)
    with open(os.environ["GITHUB_PATH"], "a", encoding="utf-8") as stream:
        stream.write(str(directory) + "\n")
    print(f"Verified and installed k3d {VERSION}")


if __name__ == "__main__":
    main()
