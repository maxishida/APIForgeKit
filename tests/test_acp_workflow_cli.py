import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_acp_workflow_cli_runs_skill_sections_in_one_session(tmp_path):
    result = subprocess.run(
        [
            sys.executable,
            "run_acp_workflow.py",
            "--database-url",
            "sqlite+pysqlite:///:memory:",
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
    assert payload["summary"]["total_prompts"] == 6
    assert payload["summary"]["passed"] == 6
    assert [step["skill_section"] for step in payload["steps"]] == [
        "Algorithm Path",
        "API Path",
        "Token Economy Path",
        "Context Builder Gate",
        "Evidence Contract",
        "Stop Conditions",
    ]
    assert payload["steps"][0]["response"]["result"]["_meta"]["apiforgekit.command"] == "validate-lead-score"
    assert payload["steps"][1]["response"]["result"]["_meta"]["apiforgekit.command"] == "validate-api-suite"
    assert payload["steps"][4]["response"]["result"]["_meta"]["apiforgekit.command"] == "export-evidence"
    assert payload["steps"][5]["response"]["result"]["stopReason"] == "refusal"
    assert payload["steps"][5]["permission_requested"] is True


def test_package_json_exposes_acp_workflow_helper():
    package_json = (ROOT / "package.json").read_text(encoding="utf-8")

    assert '"acp:workflow": "python run_acp_workflow.py"' in package_json
