import json
import subprocess
import sys
from pathlib import Path

from acp import schema

from agents.acp_agent import AcpAgent
from agents.acp_protocol import JsonRpcError


def test_initialize_returns_minimal_capabilities():
    response = AcpAgent().handle_request({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})

    assert response["id"] == 1
    payload = schema.InitializeResponse.model_validate(response["result"])
    assert payload.protocol_version == 1
    assert payload.agent_info.name == "apiforgekit-acp-skill-executor"
    assert payload.auth_methods == []
    assert payload.field_meta["apiforgekit.supportsMcpStdio"] is True
    assert response["result"]["agentCapabilities"]["mcpCapabilities"]["http"] is False
    assert response["result"]["agentCapabilities"]["mcpCapabilities"]["sse"] is False


def test_session_new_requires_absolute_cwd():
    agent = AcpAgent()

    response = agent.handle_request({"jsonrpc": "2.0", "id": 2, "method": "session/new", "params": {"cwd": "relative"}})

    assert response["error"]["code"] == JsonRpcError.INVALID_PARAMS
    assert "absolute" in response["error"]["message"]


def test_session_new_registers_mcp_stdio_servers(tmp_path):
    agent = AcpAgent()
    response = agent.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "session/new",
            "params": {
                "cwd": str(tmp_path.resolve()),
                "mcpServers": [{"name": "fake", "command": str(Path("python").resolve()), "args": ["--version"], "env": []}],
            },
        }
    )

    session_id = response["result"]["sessionId"]
    assert session_id in agent.sessions
    assert agent.sessions[session_id].mcp_servers[0]["name"] == "fake"
    assert response["result"]["_meta"]["apiforgekit.sessionId"] == session_id
    schema.NewSessionResponse.model_validate(response["result"])
    notification = next(update for update in agent.outbox if update["params"]["update"]["sessionUpdate"] == "available_commands_update")
    names = [command["name"] for command in notification["params"]["update"]["availableCommands"]]
    assert "validate-api-suite" in names
    assert "validate-lead-score" in names
    assert all(not name.startswith("/") for name in names)
    assert next(command for command in notification["params"]["update"]["availableCommands"] if command["name"] == "validate-algorithm")["input"]["hint"]
    schema.SessionNotification.model_validate(notification["params"])


def test_session_prompt_rejects_paid_http_real_without_permission(tmp_path):
    agent = AcpAgent()
    session = agent.new_session(cwd=str(tmp_path.resolve()), mcp_servers=[])

    response = agent.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "session/prompt",
            "params": {"sessionId": session.session_id, "prompt": "/validate-api-suite whatsapp_validation_pack --http-real"},
        }
    )

    assert response["result"]["stopReason"] == "refusal"
    schema.PromptResponse.model_validate(response["result"])
    assert response["result"]["_meta"]["apiforgekit.permissionRequired"] is True
    assert response["result"]["_meta"]["apiforgekit.command"] == "validate-api-suite"
    assert response["result"]["_meta"]["apiforgekit.blockedCommand"] == "/validate-api-suite whatsapp_validation_pack --http-real"
    request = next(request for request in agent.outbox if request["method"] == "session/request_permission")
    schema.RequestPermissionRequest.model_validate(request["params"])
    message = next(
        update
        for update in agent.outbox
        if update["method"] == "session/update" and update["params"]["update"]["sessionUpdate"] == "agent_message_chunk"
    )
    assert "permissão" in message["params"]["update"]["content"]["text"].lower()


def test_session_prompt_streams_plan_and_result_updates(tmp_path):
    agent = AcpAgent(database_url="sqlite+pysqlite:///:memory:", reports_dir=tmp_path)
    session = agent.new_session(cwd=str(tmp_path.resolve()), mcp_servers=[])

    response = agent.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "session/prompt",
            "params": {"sessionId": session.session_id, "prompt": "/token-cost provider=xai model=grok-4.3 users=1 requests=1"},
        }
    )

    assert response["result"]["stopReason"] == "end_turn"
    assert response["result"]["_meta"]["apiforgekit.sessionId"] == session.session_id
    plans = [update for update in agent.outbox if update["params"]["update"]["sessionUpdate"] == "plan"]
    assert plans[0]["params"]["update"]["entries"][0]["status"] == "pending"
    assert any(entry["status"] == "in_progress" for entry in plans[-1]["params"]["update"]["entries"])
    schema.SessionNotification.model_validate(plans[0]["params"])
    message = next(update for update in agent.outbox if update["params"]["update"]["sessionUpdate"] == "agent_message_chunk")
    assert message["params"]["update"]["content"]["type"] == "text"
    assert "status" in message["params"]["update"]["content"]["text"]
    assert message["params"]["_meta"]["apiforgekit.sessionId"] == session.session_id
    schema.SessionNotification.model_validate(message["params"])


def test_build_context_prompt_streams_context_builder_plan(tmp_path):
    agent = AcpAgent(database_url="sqlite+pysqlite:///:memory:", reports_dir=tmp_path)
    session = agent.new_session(cwd=str(tmp_path.resolve()), mcp_servers=[])

    agent.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 55,
            "method": "session/prompt",
            "params": {"sessionId": session.session_id, "prompt": "/build-context"},
        }
    )

    plan = next(update for update in agent.outbox if update["params"]["update"]["sessionUpdate"] == "plan")
    steps = [entry["content"] for entry in plan["params"]["update"]["entries"]]

    assert "Coletar evidências dos labs" in steps
    assert "Gerar contexto técnico" in steps


def test_session_prompt_accepts_content_blocks_and_validate_lead_score_runs_canonical_plan(tmp_path):
    agent = AcpAgent(database_url="sqlite+pysqlite:///:memory:", reports_dir=tmp_path)
    session = agent.new_session(cwd=str(tmp_path.resolve()), mcp_servers=[])

    response = agent.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 6,
            "method": "session/prompt",
            "params": {"sessionId": session.session_id, "prompt": [{"type": "text", "text": "/validate-lead-score"}]},
        }
    )

    assert response["result"]["stopReason"] == "end_turn"
    schema.PromptResponse.model_validate(response["result"])
    assert "result" not in response["result"]
    assert response["result"]["_meta"]["apiforgekit.command"] == "validate-lead-score"
    assert response["result"]["_meta"]["apiforgekit.algorithm"] == "lead_score"
    assert response["result"]["_meta"]["apiforgekit.runId"]
    assert response["result"]["_meta"]["apiforgekit.evidenceZip"].endswith(".zip")
    assert response["result"]["_meta"]["apiforgekit.contextPath"].endswith("lead_score_context.md")
    message = next(
        update
        for update in agent.outbox
        if update["params"]["update"]["sessionUpdate"] == "agent_message_chunk" and "lead_score_validation" in update["params"]["update"]["content"]["text"]
    )
    result = json.loads(message["params"]["update"]["content"]["text"])
    assert result["mode"] == "lead_score_validation"
    assert result["evidence"]["failed"] == 0
    assert result["exports"]["zip"].endswith(".zip")
    plan = next(update for update in agent.outbox if update["params"]["update"]["sessionUpdate"] == "plan")
    steps = [entry["content"] for entry in plan["params"]["update"]["entries"]]
    assert "Verificar invariantes" in steps
    assert all(entry["status"] == "pending" for entry in plan["params"]["update"]["entries"])
    assert any(update["params"]["update"]["sessionUpdate"] == "tool_call" for update in agent.outbox)
    assert any(
        update["params"]["update"]["sessionUpdate"] == "tool_call_update" and update["params"]["update"]["status"] == "completed"
        for update in agent.outbox
    )


def test_session_prompt_still_accepts_legacy_string_prompt(tmp_path):
    agent = AcpAgent(database_url="sqlite+pysqlite:///:memory:", reports_dir=tmp_path)
    session = agent.new_session(cwd=str(tmp_path.resolve()), mcp_servers=[])

    response = agent.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 7,
            "method": "session/prompt",
            "params": {"sessionId": session.session_id, "prompt": "validate-lead-score"},
        }
    )

    assert response["result"]["stopReason"] == "end_turn"
    assert response["result"]["_meta"]["apiforgekit.command"] == "validate-lead-score"


def test_session_prompt_rejects_unsupported_non_text_content_block(tmp_path):
    agent = AcpAgent(database_url="sqlite+pysqlite:///:memory:", reports_dir=tmp_path)
    session = agent.new_session(cwd=str(tmp_path.resolve()), mcp_servers=[])

    response = agent.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 8,
            "method": "session/prompt",
            "params": {"sessionId": session.session_id, "prompt": [{"type": "image", "data": "..."}]},
        }
    )

    assert response["result"]["stopReason"] == "refusal"
    message = next(update for update in agent.outbox if update["params"]["update"]["sessionUpdate"] == "agent_message_chunk")
    assert "Apenas blocos de texto" in message["params"]["update"]["content"]["text"]


def test_stdio_does_not_emit_response_for_cancel_notification(tmp_path):
    script = (
        "import json, sys\n"
        "from pathlib import Path\n"
        "from agents.acp_agent import AcpAgent\n"
        "agent=AcpAgent(database_url='sqlite+pysqlite:///:memory:', reports_dir=r'" + str(tmp_path) + "')\n"
        "session=agent.new_session(cwd=str(Path.cwd()), mcp_servers=[]).session_id\n"
        "agent.outbox.clear()\n"
        "request={'jsonrpc':'2.0','method':'session/cancel','params':{'sessionId':session}}\n"
        "response=agent.handle_request(request)\n"
        "for notification in agent.outbox:\n"
        "    print(json.dumps(notification, ensure_ascii=False))\n"
        "if response is not None:\n"
        "    print(json.dumps(response, ensure_ascii=False))\n"
    )

    result = subprocess.run([sys.executable, "-c", script], cwd=Path.cwd(), text=True, capture_output=True, check=True)
    lines = [json.loads(line) for line in result.stdout.splitlines() if line.strip()]

    assert lines
    assert all("id" not in line for line in lines)
    assert any(line["method"] == "session/update" for line in lines)
