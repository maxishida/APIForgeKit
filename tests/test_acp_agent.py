from pathlib import Path

from acp import schema

from agents.acp_agent import AcpAgent
from agents.acp_protocol import JsonRpcError


def test_initialize_returns_minimal_capabilities():
    response = AcpAgent().handle_request({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})

    assert response["id"] == 1
    assert response["result"]["protocolVersion"] == 1
    assert response["result"]["agentCapabilities"]["mcpCapabilities"]["stdio"] is True
    assert response["result"]["agentCapabilities"]["mcpCapabilities"]["http"] is False


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
    notification = next(update for update in agent.outbox if update["params"]["update"]["sessionUpdate"] == "available_commands_update")
    assert notification["params"]["update"]["availableCommands"][0]["name"] == "/validate-api-suite"
    assert any(command["name"] == "/validate-lead-score" for command in notification["params"]["update"]["availableCommands"])
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

    assert response["result"]["stopReason"] == "permission_required"
    assert response["result"]["permission"]["kind"] == "network"
    request = next(request for request in agent.outbox if request["method"] == "session/request_permission")
    schema.RequestPermissionRequest.model_validate(request["params"])


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
    plan = next(update for update in agent.outbox if update["params"]["update"]["sessionUpdate"] == "plan")
    assert plan["params"]["update"]["entries"][0]["status"] == "in_progress"
    schema.SessionNotification.model_validate(plan["params"])
    message = next(update for update in agent.outbox if update["params"]["update"]["sessionUpdate"] == "agent_message_chunk")
    assert message["params"]["update"]["content"]["type"] == "text"
    assert "status" in message["params"]["update"]["content"]["text"]
    assert message["params"]["_meta"]["apiforgekit.sessionId"] == session.session_id
    schema.SessionNotification.model_validate(message["params"])


def test_session_prompt_validate_lead_score_runs_canonical_plan(tmp_path):
    agent = AcpAgent(database_url="sqlite+pysqlite:///:memory:", reports_dir=tmp_path)
    session = agent.new_session(cwd=str(tmp_path.resolve()), mcp_servers=[])

    response = agent.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 6,
            "method": "session/prompt",
            "params": {"sessionId": session.session_id, "prompt": "/validate-lead-score"},
        }
    )

    assert response["result"]["stopReason"] == "end_turn"
    result = response["result"]["result"]
    assert result["mode"] == "lead_score_validation"
    assert result["evidence"]["failed"] == 0
    assert result["exports"]["zip"].endswith(".zip")
    plan = next(update for update in agent.outbox if update["params"]["update"]["sessionUpdate"] == "plan")
    steps = [entry["content"] for entry in plan["params"]["update"]["entries"]]
    assert "Verificar invariantes" in steps
