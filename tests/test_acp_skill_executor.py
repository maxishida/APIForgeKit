from sqlalchemy import create_engine

from agents.skill_executor import SkillExecutor, SkillExecutorServices
from core.algorithm_test_lab import AlgorithmTestRepository
from core.api_test_lab import ApiTestRepository
from core.database import build_session_factory, init_db
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


def test_unknown_command_returns_not_validated_with_safe_suggestions(tmp_path):
    result = _executor(tmp_path).execute("crie o app agora")

    assert result["status"] == "not_validated"
    assert "Ainda não validado" in result["message"]
    assert "/validate-algorithm lead_score" in result["suggested_commands"]


def test_validate_algorithm_runs_lead_score_suite_and_exports_context(tmp_path):
    result = _executor(tmp_path).execute("/validate-algorithm lead_score")

    assert result["status"] == "success"
    assert result["mode"] == "algorithm_validation"
    assert result["run"]["status"] == "passed"
    assert result["evidence"]["passed"] == 8
    assert result["exports"]["context"].endswith("lead_score_context.md")


def test_validate_unknown_algorithm_returns_safe_not_validated(tmp_path):
    result = _executor(tmp_path).execute("/validate-algorithm missing_algorithm")

    assert result["status"] == "not_validated"
    assert "Unknown algorithm" in result["message"]


def test_validate_api_suite_runs_whatsapp_pack_without_permission(tmp_path):
    executor = _executor(tmp_path)

    result = executor.execute("/validate-api-suite whatsapp_validation_pack")

    assert result["status"] == "success"
    assert result["mode"] == "generic_api_validation"
    assert result["permission_required"] is False
    assert result["run"]["status"] == "passed"
    assert result["evidence"]["suite"] == "whatsapp_validation_pack"


def test_validate_unknown_api_suite_returns_safe_not_validated(tmp_path):
    result = _executor(tmp_path).execute("/validate-api-suite missing_suite")

    assert result["status"] == "not_validated"
    assert "Unknown suite" in result["message"]


def test_token_cost_returns_pricing_source_url(tmp_path):
    result = _executor(tmp_path).execute("/token-cost provider=xai model=grok-4.3 users=10 requests=20 input=1000 output=500 days=30")

    assert result["status"] == "success"
    assert result["mode"] == "token_economy"
    assert result["estimate"]["source_url"] == "https://docs.x.ai/developers/models"
    assert result["estimate"]["cost_per_user_usd"] == 1.5


def test_export_evidence_creates_bundle_from_current_context(tmp_path):
    executor = _executor(tmp_path)
    executor.execute("/validate-algorithm lead_score")

    result = executor.execute("/export-evidence")

    assert result["status"] == "success"
    assert result["exports"]["zip"].endswith(".zip")
    assert result["exports"]["markdown"].endswith(".md")
