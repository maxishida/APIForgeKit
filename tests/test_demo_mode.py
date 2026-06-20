from sqlalchemy import create_engine

from core.algorithm_test_lab import AlgorithmTestRepository
from core.api_test_lab import ApiTestRepository, ensure_default_api_suites
from core.database import build_session_factory, init_db
from core.demo_mode import run_demo_mode
from core.token_usage import TokenUsageRepository


def test_demo_mode_runs_algorithm_api_pack_and_token_estimate():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    init_db(engine)
    session_factory = build_session_factory(engine)

    result = run_demo_mode(
        algorithm_repository=AlgorithmTestRepository(session_factory),
        api_repository=ApiTestRepository(session_factory),
        token_repository=TokenUsageRepository(session_factory),
    )

    assert result["algorithm_run"]["status"] == "passed"
    assert result["api_run"]["status"] == "passed"
    assert result["token_estimate"]["provider"] == "xai"
    assert result["summary"]["demo_ready"] is True


def test_demo_mode_excludes_real_http_cases_from_contract_validation():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    init_db(engine)
    session_factory = build_session_factory(engine)
    api_repository = ApiTestRepository(session_factory)
    ensure_default_api_suites(api_repository)
    suite = api_repository.get_suite_by_name("whatsapp_validation_pack")
    api_repository.create_case(
        suite_id=suite["id"],
        name="real case must not run in demo",
        method="GET",
        url="http://127.0.0.1:9/blocked",
        headers={},
        body={},
        expected={"status_code": 200},
        dry_run=False,
    )

    result = run_demo_mode(
        algorithm_repository=AlgorithmTestRepository(session_factory),
        api_repository=api_repository,
        token_repository=TokenUsageRepository(session_factory),
    )

    assert result["api_run"]["status"] == "passed"
    assert result["api_run"]["total_cases"] == 4
