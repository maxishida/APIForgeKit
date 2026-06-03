import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_acp_prompt_cli_runs_content_block_prompt_and_prints_updates(tmp_path):
    result = subprocess.run(
        [
            sys.executable,
            "run_acp_prompt.py",
            "/token-cost provider=xai model=grok-4.3 users=1 requests=1 input=100 output=50 days=1",
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

    assert payload["response"]["result"]["stopReason"] == "end_turn"
    assert payload["response"]["result"]["_meta"]["apiforgekit.command"] == "token-cost"
    assert any(update["method"] == "session/update" for update in payload["updates"])
    message = next(update for update in payload["updates"] if update["params"]["update"]["sessionUpdate"] == "agent_message_chunk")
    assert "pricing_mode" in message["params"]["update"]["content"]["text"]


def test_acp_prompt_cli_permission_path_is_schema_safe(tmp_path):
    result = subprocess.run(
        [
            sys.executable,
            "run_acp_prompt.py",
            "/validate-api-suite whatsapp_validation_pack --http-real",
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

    assert payload["response"]["result"]["stopReason"] == "refusal"
    assert payload["response"]["result"]["_meta"]["apiforgekit.permissionRequired"] is True
    assert any(update["method"] == "session/request_permission" for update in payload["updates"])
