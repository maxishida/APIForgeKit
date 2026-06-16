from pathlib import Path

from sqlalchemy import create_engine

from agents.skill_executor import SkillExecutor, SkillExecutorServices
from core.acp_audit import AcpAuditRepository
from core.algorithm_test_lab import AlgorithmTestRepository
from core.api_test_lab import ApiTestRepository
from core.database import build_session_factory, init_db
from core.observability import ObservabilityEventInput, ObservabilityRepository
from core.token_usage import TokenUsageRepository


def _executor(tmp_path):
    engine = create_engine("sqlite+pysqlite:///:memory:")
    init_db(engine)
    session_factory = build_session_factory(engine)
    services = SkillExecutorServices(
        algorithm_repository=AlgorithmTestRepository(session_factory),
        api_repository=ApiTestRepository(session_factory),
        token_repository=TokenUsageRepository(session_factory),
        reports_dir=tmp_path,
        skill_path="SKILL.md",
    )
    return SkillExecutor(services)


def _executor_with_token_repository(tmp_path):
    engine = create_engine("sqlite+pysqlite:///:memory:")
    init_db(engine)
    session_factory = build_session_factory(engine)
    token_repository = TokenUsageRepository(session_factory)
    services = SkillExecutorServices(
        algorithm_repository=AlgorithmTestRepository(session_factory),
        api_repository=ApiTestRepository(session_factory),
        token_repository=token_repository,
        reports_dir=tmp_path,
        skill_path="SKILL.md",
    )
    return SkillExecutor(services), token_repository


def _executor_with_acp(tmp_path):
    engine = create_engine("sqlite+pysqlite:///:memory:")
    init_db(engine)
    session_factory = build_session_factory(engine)
    acp_repository = AcpAuditRepository(session_factory)
    acp_repository.create_session(session_id="session-1", cwd=str(tmp_path), mcp_servers=[])
    acp_repository.record_event(
        session_id="session-1",
        event_type="session_prompt",
        status="received",
        command="/build-context",
        message="Prompt received from test.",
    )
    services = SkillExecutorServices(
        algorithm_repository=AlgorithmTestRepository(session_factory),
        api_repository=ApiTestRepository(session_factory),
        token_repository=TokenUsageRepository(session_factory),
        acp_repository=acp_repository,
        reports_dir=tmp_path,
        skill_path="SKILL.md",
    )
    return SkillExecutor(services)


def _executor_with_observability(tmp_path):
    engine = create_engine("sqlite+pysqlite:///:memory:")
    init_db(engine)
    session_factory = build_session_factory(engine)
    observability_repository = ObservabilityRepository(session_factory)
    services = SkillExecutorServices(
        algorithm_repository=AlgorithmTestRepository(session_factory),
        api_repository=ApiTestRepository(session_factory),
        token_repository=TokenUsageRepository(session_factory),
        observability_repository=observability_repository,
        reports_dir=tmp_path,
        skill_path="SKILL.md",
    )
    return SkillExecutor(services), observability_repository


def test_unknown_command_returns_not_validated_with_safe_suggestions(tmp_path):
    result = _executor(tmp_path).execute("crie o app agora")

    assert result["status"] == "not_validated"
    assert "Ainda não validado" in result["message"]
    assert "/validate-algorithm lead_score" in result["suggested_commands"]
    assert result["errors"] == []


def test_validate_algorithm_runs_lead_score_suite_and_exports_context(tmp_path):
    result = _executor(tmp_path).execute("/validate-algorithm lead_score")

    assert result["status"] == "success"
    assert result["mode"] == "algorithm_validation"
    assert result["run"]["status"] == "passed"
    assert result["evidence"]["passed"] >= 17
    assert result["exports"]["context"].endswith("lead_score_context.md")
    assert result["errors"] == []


def test_validate_lead_score_exports_evidence_bundle(tmp_path):
    result = _executor(tmp_path).execute("/validate-lead-score")

    assert result["status"] == "success"
    assert result["mode"] == "lead_score_validation"
    assert result["evidence"]["algorithm"] == "lead_score"
    assert result["evidence"]["passed"] >= 17
    assert result["evidence"]["run_id"] == result["run"]["id"]
    assert result["evidence"]["invariants"]["all_passed"] is True
    assert result["evidence"]["invariants"]["payload_validated"] >= 17
    assert result["evidence"]["invariants"]["failed"] == 0
    assert result["exports"]["context"].endswith("lead_score_context.md")
    assert result["exports"]["zip"].endswith(".zip")
    assert result["errors"] == []


def test_validate_unknown_algorithm_returns_safe_not_validated(tmp_path):
    result = _executor(tmp_path).execute("/validate-algorithm missing_algorithm")

    assert result["status"] == "not_validated"
    assert "Unknown algorithm" in result["message"]
    assert result["errors"][0]["type"] == "not_validated"


def test_validate_api_suite_runs_whatsapp_pack_without_permission(tmp_path):
    executor = _executor(tmp_path)

    result = executor.execute("/validate-api-suite whatsapp_validation_pack")

    assert result["status"] == "success"
    assert result["mode"] == "generic_api_validation"
    assert result["permission_required"] is False
    assert result["run"]["status"] == "passed"
    assert result["evidence"]["suite"] == "whatsapp_validation_pack"
    assert result["errors"] == []


def test_validate_unknown_api_suite_returns_safe_not_validated(tmp_path):
    result = _executor(tmp_path).execute("/validate-api-suite missing_suite")

    assert result["status"] == "not_validated"
    assert "Unknown suite" in result["message"]
    assert result["errors"][0]["type"] == "not_validated"


def test_token_cost_returns_pricing_source_url(tmp_path):
    result = _executor(tmp_path).execute("/token-cost provider=xai model=grok-4.3 users=10 requests=20 input=1000 output=500 days=30")

    assert result["status"] == "success"
    assert result["mode"] == "token_economy"
    assert result["estimate"]["source_url"] == "https://docs.x.ai/developers/pricing"
    assert result["estimate"]["cost_per_user_usd"] == 1.5
    assert result["record"] is None
    assert result["evidence"]["record_id"] is None
    assert result["errors"] == []


def test_validate_token_cost_alias_returns_estimate_without_breaking_token_cost(tmp_path):
    executor = _executor(tmp_path)

    result = executor.execute("/validate-token-cost provider=xai model=grok-4.3 users=10 requests=20 input=1000 output=500 days=30")
    legacy_result = executor.execute("/token-cost provider=xai model=grok-4.3 users=10 requests=20 input=1000 output=500 days=30")

    assert result["status"] == "success"
    assert result["mode"] == "token_cost_validation"
    assert result["estimate"]["provider"] == "xai"
    assert result["estimate"]["model"] == "grok-4.3"
    assert result["estimate"]["total_tokens"] == legacy_result["estimate"]["total_tokens"]
    assert result["evidence"]["command"] == "/validate-token-cost"
    assert legacy_result["mode"] == "token_economy"


def test_token_cost_save_true_persists_estimate(tmp_path):
    executor, repository = _executor_with_token_repository(tmp_path)

    result = executor.execute("/token-cost provider=xai model=grok-4.3 users=1 requests=1 input=100 output=50 days=1 save=true")

    rows = repository.list_estimates()
    assert result["status"] == "success"
    assert result["record"]["id"] == rows[0]["id"]
    assert result["evidence"]["record_id"] == rows[0]["id"]


def test_token_cost_docs_verified_accepts_pricing_overrides(tmp_path):
    result = _executor(tmp_path).execute(
        "/token-cost provider=xai model=grok-4.3 users=50 requests=15 days=30 input=1400 output=500 cached=200 "
        "pricing_mode=docs_verified pricing_source=https://docs.x.ai/developers/pricing "
        "input_price=1.25 output_price=2.50 cached_price=0.20"
    )

    assert result["estimate"]["pricing_mode"] == "docs_verified"
    assert result["estimate"]["pricing_verified_source_url"] == "https://docs.x.ai/developers/pricing"
    assert result["estimate"]["estimated_cost_usd"] == 62.775
    assert result["record"] is None


def test_token_cost_invalid_numeric_argument_returns_safe_not_validated(tmp_path):
    result = _executor(tmp_path).execute("/token-cost provider=xai model=grok-4.3 users=abc requests=20")

    assert result["status"] == "not_validated"
    assert result["mode"] == "token_economy"
    assert result["errors"][0]["type"] == "invalid_token_cost_args"
    assert "users" in result["message"]


def test_token_cost_unknown_model_returns_safe_not_validated(tmp_path):
    result = _executor(tmp_path).execute("/token-cost provider=xai model=missing users=1 requests=1")

    assert result["status"] == "not_validated"
    assert result["mode"] == "token_economy"
    assert result["errors"][0]["type"] == "invalid_token_cost_args"
    assert "Unsupported provider/model" in result["message"]


def test_build_context_includes_acp_protocol_trace_when_available(tmp_path):
    result = _executor_with_acp(tmp_path).execute("/build-context")

    assert result["status"] == "success"
    assert result["exports"]["context"].endswith(".md")
    context = Path(result["exports"]["context"]).read_text(encoding="utf-8")
    assert "Contexto Técnico - ACP Skill Executor" in context
    assert "protocol_trace" in context
    assert "/build-context" in context


def test_validate_context_readiness_needs_tests_without_evidence(tmp_path):
    result = _executor(tmp_path).execute("/validate-context-readiness")

    assert result["status"] == "not_validated"
    assert result["mode"] == "context_readiness"
    assert result["readiness"]["overall"]["status"] == "Needs tests"
    assert result["exports"]["markdown"].endswith(".md")


def test_validate_context_readiness_ready_after_algorithm_and_api_evidence(tmp_path):
    executor = _executor(tmp_path)
    executor.execute("/validate-lead-score")
    executor.execute("/validate-api-suite whatsapp_validation_pack")

    result = executor.execute("/validate-context-readiness")

    assert result["status"] == "success"
    assert result["mode"] == "context_readiness"
    assert result["readiness"]["source_mode"] == "algorithm_api"
    assert result["readiness"]["overall"]["status"] == "Ready"
    assert result["evidence"]["readiness"] == "Ready"
    assert result["exports"]["zip"].endswith(".zip")


def test_validate_context_readiness_records_exports_when_observability_exists(tmp_path):
    executor, repository = _executor_with_observability(tmp_path)
    run = repository.start_run("xai", "live_observability_compact", ["context"])
    repository.finish_run(run["id"], "success")

    result = executor.execute("/validate-context-readiness")

    exports = repository.list_context_exports(limit=1, run_id=run["id"])
    assert exports
    assert exports[0]["format"] == "multi"
    assert exports[0]["summary"]["source"] == "acp_context_readiness"
    assert exports[0]["summary"]["readiness"] == result["readiness"]["overall"]["status"]
    assert result["exports"]["markdown"] in exports[0]["summary"]["paths"].values()


def test_validate_voice_roundtrip_needs_tests_without_voice_evidence(tmp_path):
    result = _executor_with_observability(tmp_path)[0].execute("/validate-voice-roundtrip")

    assert result["status"] == "not_validated"
    assert result["mode"] == "voice_roundtrip_validation"
    assert result["evidence"]["latest_run"] is None
    assert "npm run voice:run" in result["suggested_commands"]


def test_validate_voice_roundtrip_succeeds_with_latest_voice_evidence(tmp_path):
    executor, repository = _executor_with_observability(tmp_path)
    run = repository.start_run("xai", "voice_roundtrip", ["lead_input", "tts", "stt", "agent_response", "voice_status"])
    for event_type in [
        "lead_received",
        "user_message_received",
        "tts_audio_received",
        "transcript_received",
        "agent_response_received",
        "voice_call_completed",
    ]:
        repository.record_event(
            ObservabilityEventInput(
                run_id=str(run["id"]),
                provider="xai",
                module="voice",
                test_name="voice_roundtrip",
                event_type=event_type,
                status="success",
                message="Status da chamada/voz: concluída" if event_type == "voice_call_completed" else event_type,
                latency_ms=1200 if event_type == "voice_call_completed" else 0,
                request={"evidence_mode": "real_http", "origin": "whatsapp"},
                response={"evidence_mode": "real_http", "classification": "sales_intent"},
            )
        )
    repository.record_voice_test(
        str(run["id"]),
        audio_artifact=str(tmp_path / "voice.mp3"),
        transcript="Quero orçamento hoje",
        classification="sales_intent",
        metrics={"total_latency_ms": 1200},
        status="success",
    )
    repository.finish_run(str(run["id"]), "success", {"voice_status": "success"})

    result = executor.execute("/validate-voice-roundtrip")

    assert result["status"] == "success"
    assert result["mode"] == "voice_roundtrip_validation"
    assert result["evidence"]["latest_run"]["id"] == run["id"]
    assert result["evidence"]["event_count"] == 6
    assert result["evidence"]["missing_event_types"] == []
    assert result["evidence"]["voice_status"] == "success"


def test_validate_voice_roundtrip_finds_voice_evidence_after_many_other_runs(tmp_path):
    executor, repository = _executor_with_observability(tmp_path)
    run = repository.start_run("xai", "voice_roundtrip", ["lead_input", "tts", "stt", "agent_response", "voice_status"])
    for event_type in [
        "lead_received",
        "user_message_received",
        "tts_audio_received",
        "transcript_received",
        "agent_response_received",
        "voice_call_completed",
    ]:
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
    repository.record_voice_test(str(run["id"]), transcript="Quero preço", classification="sales_intent", status="success")
    repository.finish_run(str(run["id"]), "success", {"voice_status": "success"})
    for index in range(120):
        other = repository.start_run("other", f"noise_{index}", ["noise"])
        repository.finish_run(str(other["id"]), "success", {"noise": index})

    result = executor.execute("/validate-voice-roundtrip")

    assert result["status"] == "success"
    assert result["evidence"]["latest_run"]["id"] == run["id"]


def test_validate_voice_roundtrip_fails_when_essential_events_are_missing(tmp_path):
    executor, repository = _executor_with_observability(tmp_path)
    run = repository.start_run("xai", "voice_roundtrip", ["lead_input", "tts", "stt", "agent_response", "voice_status"])
    repository.record_event(
        ObservabilityEventInput(
            run_id=str(run["id"]),
            provider="xai",
            module="voice",
            test_name="voice_roundtrip",
            event_type="voice_call_completed",
            status="success",
            message="Status da chamada/voz: concluída",
            request={"evidence_mode": "real_http"},
            response={"evidence_mode": "real_http"},
        )
    )
    repository.finish_run(str(run["id"]), "success", {"voice_status": "success"})

    result = executor.execute("/validate-voice-roundtrip")

    assert result["status"] == "failed"
    assert "lead_received" in result["evidence"]["missing_event_types"]
    assert result["errors"][0]["type"] == "voice_roundtrip_missing_events"


def test_validate_voice_roundtrip_run_real_requires_permission(tmp_path):
    result = _executor_with_observability(tmp_path)[0].execute("/validate-voice-roundtrip --run-real")

    assert result["status"] == "permission_required"
    assert result["permission"]["kind"] == "network"
    assert result["permission"]["command"] == "/validate-voice-roundtrip --run-real"


def test_export_evidence_creates_bundle_from_current_context(tmp_path):
    executor = _executor(tmp_path)
    executor.execute("/validate-algorithm lead_score")

    result = executor.execute("/export-evidence")

    assert result["status"] == "success"
    assert result["evidence"]["command"] == "/validate-algorithm lead_score"
    assert result["evidence"]["algorithm"] == "lead_score"
    assert result["evidence"]["run_id"]
    assert result["exports"]["zip"].endswith(".zip")
    assert result["exports"]["markdown"].endswith(".md")
    assert result["errors"] == []
