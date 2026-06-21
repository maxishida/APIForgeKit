from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


ARTIFACT_DIR_NAMES = {"__pycache__", ".pytest_cache"}
EXPORT_SUBDIRS = ("exports/reports", "exports/logs", "exports/contexts", "exports/blueprints")
GENERATED_FILE_PATTERNS = ("logs/*.jsonl", "outputs/*.json")
PRESERVED_NAMES = {".gitkeep"}


def collect_demo_artifacts(root: str | Path) -> dict[str, object]:
    root_path = Path(root).resolve()
    directories: list[str] = []
    files: list[str] = []

    for path in root_path.rglob("*"):
        if _is_inside_excluded_dir(path, root_path):
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

    for pattern in GENERATED_FILE_PATTERNS:
        for path in root_path.glob(pattern):
            if path.is_file() and path.name not in PRESERVED_NAMES:
                files.append(str(path))

    directories = sorted(set(directories))
    files = sorted(set(files))
    return {
        "directories": directories,
        "files": files,
        "directory_count": len(directories),
        "file_count": len(files),
        "total_bytes": sum(Path(file_path).stat().st_size for file_path in files),
    }


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


def _is_inside_excluded_dir(path: Path, root: Path) -> bool:
    parts = set(path.resolve().relative_to(root).parts)
    return ".git" in parts or ".context" in parts


def _is_safe_target(path: Path, root: Path) -> bool:
    try:
        relative = path.resolve().relative_to(root)
    except ValueError:
        return False
    if relative.parts and relative.parts[0] in {".git", ".context"}:
        return False
    if path.name == ".env":
        return False
    if path.is_dir():
        return path.name in ARTIFACT_DIR_NAMES
    if path.name in PRESERVED_NAMES:
        return False
    return _is_generated_file(relative)


def _is_generated_file(relative: Path) -> bool:
    parts = relative.parts
    if len(parts) >= 2 and parts[0] == "exports" and parts[1] in {"reports", "logs", "contexts", "blueprints"}:
        return True
    return (len(parts) == 2 and parts[0] == "logs" and relative.suffix == ".jsonl") or (
        len(parts) == 2 and parts[0] == "outputs" and relative.suffix == ".json"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="List or remove generated artifacts without touching source, test files, .env, .context or database.")
    parser.add_argument("--apply", action="store_true", help="Actually remove generated artifacts. Default is dry-run.")
    parser.add_argument("--root", default=".", help="Project root. Defaults to current directory.")
    parser.add_argument("--verbose", action="store_true", help="Include the full list of generated paths in the JSON output.")
    args = parser.parse_args()
    result = clean_demo_artifacts(args.root, apply=args.apply)
    output = result if args.verbose else _compact_summary(result)
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


def _compact_summary(result: dict[str, object]) -> dict[str, object]:
    return {
        "mode": result["mode"],
        "directory_count": result["directory_count"],
        "file_count": result["file_count"],
        "total_bytes": result["total_bytes"],
    }


if __name__ == "__main__":
    raise SystemExit(main())
