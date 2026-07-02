from sqlalchemy import create_engine

from core.algorithm_test_lab import (
    AlgorithmTestRepository,
    AlgorithmTestRunner,
    build_algorithm_context,
    ensure_default_algorithms,
    export_algorithm_suite,
    import_algorithm_suite,
    run_algorithm,
    summarize_algorithm_invariants,
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
    filtered_results = repository.list_results(algorithm_id=definition["id"], limit=20)

    assert len(cases) >= 17
    assert run["status"] == "passed"
    assert run["total_cases"] == len(cases)
    assert run["passed"] == len(cases)
    assert run["failed"] == 0
    assert len(results) == len(cases)
    assert len(filtered_results) == len(cases)
    assert all(result["algorithm_id"] == definition["id"] for result in filtered_results)
    assert all(result["structured_log"]["algorithm"] == "lead_score" for result in results)
    assert all(result["structured_log"]["invariants"]["payload_validated"] is True for result in results)
    assert all(result["structured_log"]["invariants"]["score_clamped"] is True for result in results)
    assert all(result["structured_log"]["invariants"]["deterministic"] is True for result in results)
    assert {result["actual_output"]["classification"] for result in results} >= {
        "cold_lead",
        "warm_lead",
        "hot_lead",
        "urgent_lead",
        "invalid_lead",
    }
    summary = summarize_algorithm_invariants(results)
    assert summary["all_passed"] is True
    assert summary["total"] == len(results)
    assert summary["payload_validated"] == len(results)
    assert summary["deterministic"] == len(results)
    assert summary["score_clamped"] == len(results)
    assert summary["failed"] == 0


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


def test_run_algorithm_coerces_boolean_strings_before_scoring():
    actual = run_algorithm(
        "lead_score",
        {
            "source": "LinkedIn",
            "message": "Mensagem longa sem intenção forte",
            "urgency": "baixa",
            "interest": "baixo",
            "has_phone": "false",
            "has_email": "false",
            "previous_customer": "false",
        },
    )

    assert actual["score"] == 0
    assert actual["classification"] == "cold_lead"
    assert any("sem telefone" in reason for reason in actual["reasons"])


def test_single_case_execution_records_validation_error_without_crashing():
    repository = _repository()
    ensure_default_algorithms(repository)
    runner = AlgorithmTestRunner(repository)

    definition = repository.get_definition_by_name("lead_score")
    case = repository.create_case(
        algorithm_id=definition["id"],
        name="invalid boolean input",
        input_payload={
            "source": "LinkedIn",
            "message": "Mensagem longa sem intenção forte",
            "urgency": "baixa",
            "interest": "baixo",
            "has_phone": "talvez",
            "has_email": False,
            "previous_customer": False,
        },
        expected_output={"classification": "cold_lead"},
        tags=["validation"],
    )

    run = runner.run_single_case(case["id"])
    result = repository.list_results(run_id=run["id"], limit=1)[0]

    assert run["status"] == "failed"
    assert result["status"] == "failed"
    assert result["structured_log"]["error"]
    assert result["structured_log"]["invariants"]["payload_validated"] is False
    assert result["diff"]["mismatches"][0]["field"] == "input_payload"


def test_community_bot_engine_suite_passes_all_seed_cases():
    repository = _repository()
    ensure_default_algorithms(repository)
    runner = AlgorithmTestRunner(repository)

    definition = repository.get_definition_by_name("community_bot_engine")
    cases = repository.list_cases(definition["id"])
    run = runner.run_suite(definition["id"])
    results = repository.list_results(algorithm_id=definition["id"], limit=30)

    assert len(cases) == 15
    assert run["status"] == "passed"
    assert run["passed"] == 15
    assert run["failed"] == 0
    summary = summarize_algorithm_invariants(results)
    assert summary["all_passed"] is True


def test_algorithm_context_includes_rules_results_edge_cases_and_nextjs_files():
    repository = _repository()
    ensure_default_algorithms(repository)
    runner = AlgorithmTestRunner(repository)
    definition = repository.get_definition_by_name("lead_score")
    runner.run_suite(definition["id"])

    context = build_algorithm_context(repository, algorithm_name="lead_score")

    assert "Contexto Técnico - Algorithm Test Lab" in context
    assert "Nome: `lead_score`" in context
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


def test_algorithm_suite_export_and_import_roundtrip(tmp_path):
    repository = _repository()
    ensure_default_algorithms(repository)
    definition = repository.get_definition_by_name("lead_score")

    export_path = export_algorithm_suite(repository, definition["id"], tmp_path)
    imported_repository = _repository()
    imported = import_algorithm_suite(imported_repository, export_path)

    assert imported["name"] == "lead_score"
    assert len(imported_repository.list_cases(imported["id"])) == len(repository.list_cases(definition["id"]))
