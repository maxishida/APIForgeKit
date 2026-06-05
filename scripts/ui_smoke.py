from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request


SMOKE_PATHS = [
    "/",
    "/tutorial",
    "/token-calculator",
    "/algorithm-test-lab",
    "/api-test-lab",
    "/voice-lab",
    "/context-builder",
    "/logs",
    "/live-dashboard",
]


def check_route(base_url: str, path: str, timeout: float) -> dict[str, object]:
    url = f"{base_url.rstrip('/')}{path}"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:  # noqa: S310 - local smoke harness
            return {"path": path, "status": response.status, "ok": 200 <= response.status < 400, "error": None}
    except urllib.error.HTTPError as exc:
        return {"path": path, "status": exc.code, "ok": False, "error": str(exc)}
    except Exception as exc:  # noqa: BLE001 - CLI smoke should report every failure
        return {"path": path, "status": 0, "ok": False, "error": str(exc)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke test APIForgeKit Studio UI routes.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8080")
    parser.add_argument("--timeout", type=float, default=10.0)
    args = parser.parse_args()

    results = [check_route(args.base_url, path, args.timeout) for path in SMOKE_PATHS]
    print(json.dumps({"base_url": args.base_url, "results": results}, ensure_ascii=False, indent=2))
    return 0 if all(result["ok"] for result in results) else 1


if __name__ == "__main__":
    sys.exit(main())
