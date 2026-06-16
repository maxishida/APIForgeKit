from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


ARTIFACT_DIR_NAMES = {"__pycache__", ".pytest_cache"}
EXPORT_SUBDIRS = ("exports/reports", "exports/logs")
PRESERVED_NAMES = {".gitkeep"}


def collect_demo_artifacts(root: str | Path) -> dict[str, list[str]]:
    root_path = Path(root).resolve()
    directories: list[str] = []
    files: list[str] = []

    for path in root_path.rglob("*"):
        if _is_inside_protected_dir(path, root_path):
            continue
        if path.is_dir() and path.name in ARTIFACT_DIR_NAMES:
            directories.append(str(path))

    for relative in EXPORT_SUBDIRS:
        export_dir = root_path / relative
        if not export_dir.exists():
            continue
        for path in export_dir.rglob("*"):
            if path.is_file() and path.name not in PRESERVED_NAMES:
                files.append(str(path))

    return {"directories": sorted(set(directories)), "files": sorted(set(files))}


def clean_demo_artifacts(root: str | Path, *, apply: bool = False) -> dict[str, object]:
    root_path = Path(root).resolve()
    artifacts = collect_demo_artifacts(root_path)
    if apply:
        for file_path in artifacts["files"]:
            path = Path(file_path).resolve()
            if _is_safe_target(path, root_path):
                path.unlink(missing_ok=True)
        for directory_path in sorted(artifacts["directories"], key=len, reverse=True):
            path = Path(directory_path).resolve()
            if _is_safe_target(path, root_path):
                shutil.rmtree(path, ignore_errors=True)
    return {"mode": "apply" if apply else "dry_run", **artifacts}


def _is_inside_protected_dir(path: Path, root: Path) -> bool:
    parts = set(path.resolve().relative_to(root).parts)
    return "tests" in parts or ".git" in parts


def _is_safe_target(path: Path, root: Path) -> bool:
    try:
        relative = path.resolve().relative_to(root)
    except ValueError:
        return False
    if relative.parts and relative.parts[0] in {".git", "tests"}:
        return False
    if path.name == ".env":
        return False
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="List or remove generated demo artifacts without touching source, tests, .env or database.")
    parser.add_argument("--apply", action="store_true", help="Actually remove generated artifacts. Default is dry-run.")
    parser.add_argument("--root", default=".", help="Project root. Defaults to current directory.")
    args = parser.parse_args()
    print(json.dumps(clean_demo_artifacts(args.root, apply=args.apply), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
