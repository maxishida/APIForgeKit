from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.ui_smoke import SMOKE_PATHS, check_route


def main() -> int:
    parser = argparse.ArgumentParser(description="Start APIForgeKit Studio when needed and smoke test UI routes.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8080")
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--startup-timeout", type=float, default=30.0)
    args = parser.parse_args()

    process: subprocess.Popen[bytes] | None = None
    started_process = False
    try:
        if not check_route(args.base_url, "/", 1.5)["ok"]:
            process = subprocess.Popen(
                [sys.executable, "app.py"],
                cwd=ROOT,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            started_process = True
            _wait_for_ui(args.base_url, args.startup_timeout)

        results = [check_route(args.base_url, path, args.timeout) for path in SMOKE_PATHS]
        print(
            json.dumps(
                {"base_url": args.base_url, "started_process": started_process, "results": results},
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0 if all(result["ok"] for result in results) else 1
    finally:
        if process is not None:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()


def _wait_for_ui(base_url: str, startup_timeout: float) -> None:
    deadline = time.monotonic() + startup_timeout
    while time.monotonic() < deadline:
        if check_route(base_url, "/", 1.5)["ok"]:
            return
        time.sleep(0.5)
    raise RuntimeError(f"UI did not become ready at {base_url} within {startup_timeout} seconds")


if __name__ == "__main__":
    raise SystemExit(main())
