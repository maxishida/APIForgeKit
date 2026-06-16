from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from agents.acp_agent import AcpAgent


SKILL_WORKFLOW_PROMPTS = (
    ("Algorithm Path", "/validate-lead-score", "end_turn"),
    ("API Path", "/validate-api-suite whatsapp_validation_pack", "end_turn"),
    ("Token Economy Path", "/validate-token-cost provider=xai model=grok-4.3 users=10 requests=20 input=1000 output=500 days=30", "end_turn"),
    ("Context Readiness Gate", "/validate-context-readiness", "end_turn"),
    ("Context Builder Gate", "/build-context", "end_turn"),
    ("Evidence Contract", "/export-evidence", "end_turn"),
    ("Voice Evidence Gate", "/validate-voice-roundtrip", "end_turn"),
    ("Stop Conditions", "/validate-api-suite whatsapp_validation_pack --http-real", "refusal"),
    ("Voice Stop Conditions", "/validate-voice-roundtrip --run-real", "refusal"),
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the APIForgeKit ACP workflow smoke in one session, following SKILL.md sections."
    )
    parser.add_argument("--database-url", default=None, help="Override DATABASE_URL, useful for sqlite smoke tests.")
    parser.add_argument("--reports-dir", default=None, help="Directory used for generated context and evidence bundles.")
    parser.add_argument("--cwd", default=None, help="Session cwd. Defaults to the current working directory.")
    return parser


def run_workflow(argv: Sequence[str] | None = None) -> dict[str, object]:
    args = build_parser().parse_args(argv)
    cwd = Path(args.cwd).resolve() if args.cwd else Path.cwd().resolve()
    agent = AcpAgent(database_url=args.database_url, reports_dir=args.reports_dir)

    initialize = agent.handle_request({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
    session_response = agent.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "session/new",
            "params": {"cwd": str(cwd), "mcpServers": []},
        }
    )
    session_id = str(session_response["result"]["sessionId"])
    setup_updates = list(agent.outbox)
    agent.outbox.clear()

    steps = []
    for index, (section, prompt_text, expected_stop) in enumerate(SKILL_WORKFLOW_PROMPTS, start=1):
        response = agent.handle_request(
            {
                "jsonrpc": "2.0",
                "id": index + 2,
                "method": "session/prompt",
                "params": {"sessionId": session_id, "prompt": [{"type": "text", "text": prompt_text}]},
            }
        )
        updates = list(agent.outbox)
        agent.outbox.clear()
        actual_stop = str(response.get("result", {}).get("stopReason", ""))
        actual_result_status = _extract_tool_result_status(updates)
        permission_requested = any(update.get("method") == "session/request_permission" for update in updates)
        if expected_stop == "refusal":
            passed = actual_stop == expected_stop and permission_requested
        else:
            passed = actual_stop == expected_stop and actual_result_status == "success"
        steps.append(
            {
                "skill_section": section,
                "prompt": prompt_text,
                "expected_stopReason": expected_stop,
                "actual_stopReason": actual_stop,
                "actual_result_status": actual_result_status,
                "passed": passed,
                "permission_requested": permission_requested,
                "response": response,
                "updates": updates,
            }
        )

    passed = sum(1 for step in steps if step["passed"])
    return {
        "initialize": initialize,
        "session": session_response,
        "setup_updates": setup_updates,
        "summary": {
            "session_count": 1,
            "total_prompts": len(steps),
            "passed": passed,
            "failed": len(steps) - passed,
        },
        "steps": steps,
    }


def main(argv: Sequence[str] | None = None) -> int:
    payload = run_workflow(argv)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if int(payload["summary"]["failed"]) == 0 else 1


def _extract_tool_result_status(updates: list[dict[str, object]]) -> str:
    for update in reversed(updates):
        params = update.get("params") if isinstance(update, dict) else {}
        update_payload = params.get("update") if isinstance(params, dict) else {}
        if not isinstance(update_payload, dict):
            continue
        if update_payload.get("sessionUpdate") != "tool_call_update":
            continue
        raw_output = update_payload.get("rawOutput")
        if isinstance(raw_output, dict):
            return str(raw_output.get("status") or "")
    return ""


if __name__ == "__main__":
    raise SystemExit(main())
