from agents.acp_agent import AcpAgent
from core.acp_audit import AcpAuditRepository, build_acp_context
from core.context_builder import build_guided_context_bundle
from core.database import build_engine, build_session_factory, init_db


def _repository(database_url: str) -> AcpAuditRepository:
    engine = build_engine(database_url)
    init_db(engine)
    return AcpAuditRepository(build_session_factory(engine))


def test_acp_agent_persists_session_prompt_and_final_response(tmp_path):
    database_url = f"sqlite+pysqlite:///{tmp_path / 'acp.db'}"
    agent = AcpAgent(database_url=database_url, reports_dir=tmp_path)
    session = agent.new_session(cwd=str(tmp_path.resolve()), mcp_servers=[])

    response = agent.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 10,
            "method": "session/prompt",
            "params": {
                "sessionId": session.session_id,
                "prompt": [{"type": "text", "text": "/token-cost provider=xai model=grok-4.3 users=1 requests=1"}],
            },
        }
    )

    repository = _repository(database_url)
    sessions = repository.list_sessions()
    events = repository.list_events(session_id=session.session_id)

    assert response["result"]["stopReason"] == "end_turn"
    assert sessions[0]["id"] == session.session_id
    assert sessions[0]["cwd"] == str(tmp_path.resolve())
    assert any(event["event_type"] == "session_prompt" for event in events)
    assert any(event["event_type"] == "prompt_response" and event["status"] == "success" for event in events)
    assert repository.metrics()["total_sessions"] == 1
    assert repository.metrics()["successful_prompts"] == 1


def test_acp_permission_path_is_audited_as_blocked(tmp_path):
    database_url = f"sqlite+pysqlite:///{tmp_path / 'acp-permission.db'}"
    agent = AcpAgent(database_url=database_url, reports_dir=tmp_path)
    session = agent.new_session(cwd=str(tmp_path.resolve()), mcp_servers=[])

    response = agent.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 11,
            "method": "session/prompt",
            "params": {"sessionId": session.session_id, "prompt": "/validate-api-suite whatsapp_validation_pack --http-real"},
        }
    )

    repository = _repository(database_url)
    events = repository.list_events(session_id=session.session_id)

    assert response["result"]["stopReason"] == "refusal"
    assert any(event["event_type"] == "permission_requested" and event["evidence_mode"] == "blocked" for event in events)
    assert repository.metrics()["permission_requests"] == 1
    assert repository.metrics()["refused_prompts"] == 1


def test_acp_context_and_guided_builder_include_protocol_evidence(tmp_path):
    database_url = f"sqlite+pysqlite:///{tmp_path / 'acp-context.db'}"
    agent = AcpAgent(database_url=database_url, reports_dir=tmp_path)
    session = agent.new_session(cwd=str(tmp_path.resolve()), mcp_servers=[])
    agent.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 12,
            "method": "session/prompt",
            "params": {"sessionId": session.session_id, "prompt": "/token-cost provider=xai model=grok-4.3 users=1 requests=1"},
        }
    )

    repository = _repository(database_url)
    context = build_acp_context(repository)
    bundle = build_guided_context_bundle(
        source_mode="acp",
        live_context="",
        algorithm_context="",
        api_context="",
        token_context="",
        acp_context=context,
        algorithm_metrics={"total_results": 0, "passed": 0, "failed": 0},
        api_metrics={"total_results": 0, "passed": 0, "failed": 0},
        live_metrics={"total_tests": 0, "success": 0, "failures": 0},
        token_metrics={"total_estimates": 0},
        acp_metrics=repository.metrics(),
    )

    assert "Contexto Técnico - ACP Skill Executor" in context
    assert "/token-cost" in context
    assert bundle["source_mode"] == "acp"
    assert bundle["readiness"]["overall"]["status"] == "Ready"
    assert "ACP Skill Executor" in bundle["context"]
    assert "protocol_trace" in bundle["context"]
    assert bundle["contexts"]["acp"] == context.strip()
