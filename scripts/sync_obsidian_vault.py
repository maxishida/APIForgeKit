from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from core.obsidian_vault import sync_vault, validate_vault  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Sync or validate the APIForgeKit Obsidian operational brain.")
    parser.add_argument("action", choices=("sync", "validate"))
    parser.add_argument("--vault", required=True, type=Path, help="Existing Obsidian vault directory.")
    parser.add_argument("--repo", default=ROOT_DIR, type=Path, help="APIForgeKit repository root.")
    args = parser.parse_args(argv)

    result = (
        sync_vault(vault_path=args.vault, repo_root=args.repo)
        if args.action == "sync"
        else validate_vault(vault_path=args.vault)
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("status") == "ok" or result.get("valid") is True else 2


if __name__ == "__main__":
    raise SystemExit(main())
