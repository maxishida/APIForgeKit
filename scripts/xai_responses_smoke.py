from __future__ import annotations

import json
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.config import get_settings
from core.database import build_engine, build_session_factory, init_db
from core.observability import ObservabilityRepository
from core.xai_live_runner import XaiLiveRunner


def main() -> int:
    load_dotenv(".env")
    settings = get_settings()
    engine = build_engine(settings.database_url)
    session_factory = build_session_factory(engine)
    init_db(engine)
    repo = ObservabilityRepository(session_factory)
    runner = XaiLiveRunner(repo)
    run = repo.start_run("xai", "responses_api_smoke", ["responses_api"])
    run_id = str(run["id"])

    try:
        runner._run_responses_basic(run_id)
        events = repo.list_events(limit=10, run_id=run_id)
        started = next(event for event in events if event["event_type"] == "request_started")
        success = next(event for event in events if event["status"] == "success")
        repo.finish_run(run_id, "success", {"module": success["module"], "test_name": success["test_name"]})
        response = success.get("response") or {}
        tokens = success.get("tokens") or response.get("tokens") or {}
        print(
            json.dumps(
                {
                    "run_id": run_id,
                    "status": success["status"],
                    "module": success["module"],
                    "test_name": success["test_name"],
                    "endpoint": (started.get("request") or {}).get("endpoint"),
                    "latency_ms": success.get("latency_ms"),
                    "output_text_preview": response.get("output_text_preview"),
                    "total_tokens": tokens.get("total_tokens"),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    except Exception as exc:
        repo.finish_run(run_id, "failed", {"error_type": type(exc).__name__})
        print(
            json.dumps(
                {
                    "run_id": run_id,
                    "status": "failed",
                    "error_type": type(exc).__name__,
                    "error": str(exc)[:240],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
