from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from agents.acp_agent import AcpAgent


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run one APIForgeKit ACP prompt locally and print the response plus streamed updates as JSON."
    )
    parser.add_argument("--database-url", default=None, help="Override DATABASE_URL, useful for sqlite smoke tests.")
    parser.add_argument("--reports-dir", default=None, help="Directory used for generated context and evidence bundles.")
    parser.add_argument("--cwd", default=None, help="Session cwd. Defaults to the current working directory.")
    parser.add_argument("--legacy-string", action="store_true", help="Send prompt as a legacy string instead of ACP ContentBlock[].")
    return parser


def run_prompt(argv: Sequence[str] | None = None) -> dict[str, object]:
    parser = build_parser()
    args, prompt_parts = parser.parse_known_args(argv)
    prompt_text = " ".join(prompt_parts).strip()
    if not prompt_text:
        parser.error("prompt is required, for example: /validate-lead-score")

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

    prompt_payload: object = prompt_text if args.legacy_string else [{"type": "text", "text": prompt_text}]
    response = agent.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "session/prompt",
            "params": {"sessionId": session_id, "prompt": prompt_payload},
        }
    )
    prompt_updates = list(agent.outbox)
    agent.outbox.clear()

    return {
        "initialize": initialize,
        "session": session_response,
        "response": response,
        "updates": setup_updates + prompt_updates,
    }


def main(argv: Sequence[str] | None = None) -> int:
    payload = run_prompt(argv)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
