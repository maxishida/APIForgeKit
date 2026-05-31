from sqlalchemy import create_engine

from core.algorithm_test_lab import (
    AlgorithmTestRepository,
    AlgorithmTestRunner,
    build_algorithm_context,
    ensure_default_algorithms,
    validate_expected_output,
)
from core.database import build_session_factory, init_db


def _repository() -> AlgorithmTestRepository:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    init_db(engine)
    return AlgorithmTestRepository(build_session_factory(engine))


def test_validate_expected_output_reports_passed_and_failed_fields():
    passed = validate_expected_output(
        {"classification": "urgent_lead", "min_score": 81},
        {"classification": "urgent_lead", "status": "urgent_lead", "score": 95},
    )
    failed = validate_expected_output(
        {"classification": "hot_lead", "min_score": 61},
        {"classification": "warm_lead", "status": "warm_lead", "score": 55},
    )

    assert passed["passed"] is True
    assert passed["mismatches"] == []
    assert failed["passed"] is False
    assert failed["mismatches"][0]["field"] == "classification"
    assert failed["mismatches"][1]["field"] == "score"


def test_default_lead_score_suite_runs_all_seed_cases_and_persists_results():
    repository = _repository()
    ensure_default_algorithms(repository)
    runner = AlgorithmTestRunner(repository)

    definition = repository.get_definition_by_name("lead_score")
    cases = repository.list_cases(definition["id"])
    run = runner.run_suite(definition["id"])
    results = repository.list_results(limit=20)

    assert len(cases) == 8
    assert run["status"] == "passed"
    assert run["total_cases"] == 8
    assert run["passed"] == 8
    assert run["failed"] == 0
    assert len(results) == 8
    assert all(result["structured_log"]["algorithm"] == "lead_score" for result in results)
    assert {result["actual_output"]["classification"] for result in results} >= {
        "cold_lead",
        "warm_lead",
        "hot_lead",
        "urgent_lead",
        "invalid_lead",
    }


def test_single_case_execution_records_diff_when_expected_output_is_wrong():
    repository = _repository()
    ensure_default_algorithms(repository)
    runner = AlgorithmTestRunner(repository)

    definition = repository.get_definition_by_name("lead_score")
    case = repository.create_case(
        algorithm_id=definition["id"],
        name="wrong expectation",
        input_payload={
            "lead_name": "Teste",
            "source": "Instagram",
            "message": "Oi",
            "budget": "",
            "urgency": "baixa",
            "interest": "baixo",
            "has_phone": False,
            "has_email": False,
            "previous_customer": False,
        },
        expected_output={"classification": "urgent_lead", "min_score": 81},
        tags=["edge"],
    )

    run = runner.run_single_case(case["id"])
    result = repository.list_results(run_id=run["id"], limit=1)[0]

    assert run["status"] == "failed"
    assert result["status"] == "failed"
    assert result["diff"]["passed"] is False
    assert result["structured_log"]["status"] == "failed"


def test_algorithm_context_includes_rules_results_edge_cases_and_nextjs_files():
    repository = _repository()
    ensure_default_algorithms(repository)
    runner = AlgorithmTestRunner(repository)
    definition = repository.get_definition_by_name("lead_score")
    runner.run_suite(definition["id"])

    context = build_algorithm_context(repository)

    assert "Contexto Técnico - Algorithm Test Lab" in context
    assert "Regras Validadas" in context
    assert "Testes que passaram" in context
    assert "Edge Cases" in context
    assert "Impacto para implementação Next.js" in context
    assert "/lib/lead-score.ts" in context


def test_algorithm_context_export_is_persisted_without_provider_run(tmp_path):
    repository = _repository()
    export_path = tmp_path / "algorithm_context.md"

    record = repository.record_context_export("markdown", str(export_path), {"source": "algorithm_test_lab"})

    assert record["path"] == str(export_path)
