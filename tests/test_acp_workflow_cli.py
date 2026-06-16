import json
import subprocess
import sys
from pathlib import Path

from sqlalchemy import create_engine

from core.database import build_session_factory, init_db
from core.observability import ObservabilityEventInput, ObservabilityRepository
from run_acp_workflow import run_workflow


ROOT = Path(__file__).resolve().parents[1]
VOICE_REQUIRED_EVENT_TYPES = (
    "lead_received",
    "user_message_received",
    "tts_audio_received",
    "transcript_received",
    "agent_response_received",
    "voice_call_completed",
)


def _sqlite_url(path: Path) -> str:
    return f"sqlite+pysqlite:///{path.as_posix()}"


def _seed_voice_evidence(database_url: str) -> None:
    engine = create_engine(database_url)
    init_db(engine)
    repository = ObservabilityRepository(build_session_factory(engine))
    run = repository.start_run("xai", "voice_roundtrip", ["lead_input", "tts", "stt", "agent_response", "voice_status"])
    for event_type in VOICE_REQUIRED_EVENT_TYPES:
        repository.record_event(
            ObservabilityEventInput(
                run_id=str(run["id"]),
                provider="xai",
                module="voice",
                test_name="voice_roundtrip",
                event_type=event_type,
                status="success",
                message=event_type,
                request={"evidence_mode": "real_http"},
                response={"evidence_mode": "real_http"},
            )
        )
    repository.record_voice_test(
        str(run["id"]),
        transcript="Quero orçamento hoje",
        classification="sales_intent",
        metrics={"total_latency_ms": 1000},
        status="success",
    )
    repository.finish_run(str(run["id"]), "success", {"voice_status": "success"})


def test_acp_workflow_cli_runs_skill_sections_in_one_session(tmp_path):
    database_url = _sqlite_url(tmp_path / "workflow.db")
    _seed_voice_evidence(database_url)

    result = subprocess.run(
        [
            sys.executable,
            "run_acp_workflow.py",
            "--database-url",
            database_url,
            "--reports-dir",
            str(tmp_path),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )

    payload = json.loads(result.stdout)

    assert payload["summary"]["session_count"] == 1
    assert payload["summary"]["total_prompts"] == 9
    assert payload["summary"]["passed"] == 9
    assert payload["summary"]["failed"] == 0
    assert [step["skill_section"] for step in payload["steps"]] == [
        "Algorithm Path",
        "API Path",
        "Token Economy Path",
        "Context Readiness Gate",
        "Context Builder Gate",
        "Evidence Contract",
        "Voice Evidence Gate",
        "Stop Conditions",
        "Voice Stop Conditions",
    ]
    assert payload["steps"][0]["response"]["result"]["_meta"]["apiforgekit.command"] == "validate-lead-score"
    assert payload["steps"][1]["response"]["result"]["_meta"]["apiforgekit.command"] == "validate-api-suite"
    assert payload["steps"][2]["response"]["result"]["_meta"]["apiforgekit.command"] == "validate-token-cost"
    assert payload["steps"][3]["response"]["result"]["_meta"]["apiforgekit.command"] == "validate-context-readiness"
    assert payload["steps"][5]["response"]["result"]["_meta"]["apiforgekit.command"] == "export-evidence"
    assert payload["steps"][6]["response"]["result"]["_meta"]["apiforgekit.command"] == "validate-voice-roundtrip"
    assert payload["steps"][6]["actual_result_status"] == "success"
    assert payload["steps"][7]["response"]["result"]["stopReason"] == "refusal"
    assert payload["steps"][7]["permission_requested"] is True
    assert payload["steps"][8]["response"]["result"]["stopReason"] == "refusal"
    assert payload["steps"][8]["permission_requested"] is True


def test_acp_workflow_marks_not_validated_tool_output_as_failed(tmp_path):
    payload = run_workflow(
        [
            "--database-url",
            "sqlite+pysqlite:///:memory:",
            "--reports-dir",
            str(tmp_path),
        ]
    )

    voice_step = next(step for step in payload["steps"] if step["skill_section"] == "Voice Evidence Gate")
    assert payload["summary"]["failed"] == 1
    assert voice_step["actual_stopReason"] == "end_turn"
    assert voice_step["actual_result_status"] == "not_validated"
    assert voice_step["passed"] is False


def test_package_json_exposes_acp_workflow_helper():
    package_json = (ROOT / "package.json").read_text(encoding="utf-8")

    assert '"acp:workflow": "python run_acp_workflow.py"' in package_json


def test_package_json_exposes_local_ui_smoke_helper():
    package_json = (ROOT / "package.json").read_text(encoding="utf-8")

    assert '"ui:smoke:local": "python scripts/ui_smoke_local.py"' in package_json
    assert (ROOT / "scripts" / "ui_smoke_local.py").exists()
