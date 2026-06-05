from __future__ import annotations

import argparse
import json
import sys

from core.config import get_settings
from core.database import build_engine, build_session_factory, init_db
from core.observability import ObservabilityRepository, build_live_context, export_observability_report
from core.xai_voice_runner import VoiceLeadInput, XaiVoiceRunner


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a real xAI Voice Lab roundtrip and persist observability logs.")
    parser.add_argument("--lead-name", default="Lead Voice QA")
    parser.add_argument("--origin", default="WhatsApp")
    parser.add_argument("--previous-page", default="/pricing")
    parser.add_argument("--message", default="Hello, I want to buy today through WhatsApp. My budget is five hundred dollars.")
    parser.add_argument("--voice-id", default="eve")
    parser.add_argument("--tts-language", default="en")
    parser.add_argument("--stt-language", default="en")
    parser.add_argument("--export-report", action="store_true")
    args = parser.parse_args()

    settings = get_settings()
    engine = build_engine(settings.database_url)
    init_db(engine)
    repository = ObservabilityRepository(build_session_factory(engine))
    runner = XaiVoiceRunner(repository, output_dir=settings.reports_dir / "voice")
    run = runner.run_roundtrip(
        VoiceLeadInput(
            lead_name=args.lead_name,
            origin=args.origin,
            previous_page=args.previous_page,
            user_message=args.message,
            voice_id=args.voice_id,
            tts_language=args.tts_language,
            stt_language=args.stt_language,
        )
    )
    events = repository.list_events(limit=50, run_id=str(run["id"]))
    payload: dict[str, object] = {
        "run": run,
        "event_count": len(events),
        "events": [
            {
                "event_type": event.get("event_type"),
                "status": event.get("status"),
                "latency_ms": event.get("latency_ms"),
                "message": event.get("message"),
                "error": event.get("error"),
            }
            for event in events
        ],
        "context_preview": build_live_context([run], events)[:1200],
    }
    if args.export_report:
        paths = export_observability_report(settings.reports_dir, [run], events)
        for format_name, path in paths.items():
            repository.record_context_export(str(run["id"]), format_name, path, {"source": "run_xai_voice", "events": len(events)})
        payload["exports"] = paths
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if run.get("status") == "success" else 1


if __name__ == "__main__":
    sys.exit(main())
