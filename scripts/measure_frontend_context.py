"""Report source payload bytes for this phase's explicit Docker allowlist.
Not tar transfer size or compressed image size. Does not read file contents.
"""
from pathlib import Path

root = Path(__file__).resolve().parents[1] / "frontend"
allowed = {"package.json", "package-lock.json", "index.html", "tsconfig.json",
           "vite.config.ts", "nginx.conf", "docker-entrypoint.sh"}
excluded_parts = {"node_modules", ".git", ".venv", "__pycache__", "fixtures"}
before = after = count_before = count_after = 0
for path in root.rglob("*"):
    if path.is_symlink() or not path.is_file():
        continue
    relative = path.relative_to(root)
    size = path.stat().st_size
    before += size
    count_before += 1
    permitted = relative.as_posix() in allowed or relative.parts[0] == "src"
    blocked = any(part in excluded_parts or part == ".env" or part.startswith(".env.")
                  for part in relative.parts) or path.suffix == ".pyc"
    if permitted and not blocked:
        after += size
        count_after += 1
print(f"Before ignore: {count_before} files, {before} bytes ({before / 1048576:.2f} MiB)")
print(f"After allowlist: {count_after} files, {after} bytes ({after / 1048576:.2f} MiB)")
print("Measurement: sum of source payload file sizes; Dockerfile/control and tar overhead not included in after count.")
