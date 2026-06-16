from pathlib import Path

from sqlalchemy import create_engine

from core.database import build_session_factory, init_db
from core.observability import (
    ObservabilityEventInput,
    ObservabilityRepository,
    build_live_context,
    build_report_payload,
    export_observability_report,
)


def test_observability_repository_records_run_events_requests_and_responses():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    init_db(engine)
    repository = ObservabilityRepository(build_session_factory(engine))

    run = repository.start_run("xai", "compact_validation", ["connectivity", "chat"])
    event = repository.record_event(
        ObservabilityEventInput(
            run_id=run["id"],
            provider="xai",
            module="connectivity",
            test_name="auth",
            event_type="request_started",
            status="running",
            message="xAI request started",
            latency_ms=0,
            request={"model": "grok-test"},
        )
    )
    repository.record_api_request(run["id"], event["id"], "xai", "auth", "/v1/chat/completions", {"model": "grok-test"})
    repository.record_api_response(run["id"], event["id"], 200, {"content": "ok"}, {"total_tokens": 3}, 0.001)
    repository.finish_run(run["id"], "success")

    metrics = repository.metrics()
    events = repository.list_events(limit=10)

    assert metrics["total_tests"] == 1
    assert metrics["success"] == 1
    assert metrics["failures"] == 0
    assert metrics["requests"] == 1
    assert metrics["tokens"] == 3
    assert metrics["estimated_cost"] == 0.001
    assert events[0]["message"] == "xAI request started"


def test_observability_repository_lists_context_exports_newest_first(tmp_path):
    engine = create_engine("sqlite+pysqlite:///:memory:")
    init_db(engine)
    repository = ObservabilityRepository(build_session_factory(engine))

    run = repository.start_run("xai", "compact_validation", ["context"])
    older_path = tmp_path / "older.md"
    newer_path = tmp_path / "newer.md"
    repository.record_context_export(run["id"], "markdown", str(older_path), {"source": "first"})
    repository.record_context_export(run["id"], "json", str(newer_path), {"source": "second"})

    exports = repository.list_context_exports(limit=2, run_id=run["id"])

    assert [export["format"] for export in exports] == ["json", "markdown"]
    assert exports[0]["path"] == str(newer_path)
    assert exports[0]["summary"]["source"] == "second"
    assert exports[0]["run_id"] == run["id"]


def test_live_context_and_report_are_built_from_observability_logs():
    run = {"id": "run-1", "provider": "xai", "suite_name": "compact_validation", "status": "success"}
    events = [
        {
            "event_id": "evt-1",
            "provider": "xai",
            "module": "streaming",
            "test_name": "stream",
            "status": "success",
            "message": "Response recebida",
            "latency_ms": 120,
            "request": {"stream": True},
            "response": {"chunks": 3},
            "error": None,
            "recommendation": "Use streaming telemetry.",
        }
    ]

    context = build_live_context([run], events)
    report = build_report_payload([run], events)

    assert "O que foi testado" in context
    assert "streaming" in context
    assert "Response recebida" in context
    assert report["summary"]["total_runs"] == 1
    assert report["summary"]["total_events"] == 1
    assert report["events"][0]["event_id"] == "evt-1"


def test_observability_report_exports_markdown_json_and_html(tmp_path):
    run = {"id": "run-1", "provider": "xai", "suite_name": "compact_validation", "status": "success"}
    event = {
        "event_id": "evt-1",
        "provider": "xai",
        "module": "chat",
        "test_name": "basic",
        "status": "success",
        "message": "Resposta recebida",
        "latency_ms": 90,
        "request": {"model": "grok-test"},
        "response": {"content": "ok"},
        "error": None,
        "recommendation": "Persistir evidências.",
    }

    paths = export_observability_report(tmp_path, [run], [event])

    assert set(paths) == {"json", "markdown", "html"}
    assert "Contexto Técnico" in Path(paths["markdown"]).read_text(encoding="utf-8")
    assert '"total_events": 1' in Path(paths["json"]).read_text(encoding="utf-8")
    assert "<!doctype html>" in Path(paths["html"]).read_text(encoding="utf-8")
