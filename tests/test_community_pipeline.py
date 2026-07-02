from core.algorithm_test_lab import (
    AlgorithmTestRepository,
    AlgorithmTestRunner,
    ensure_default_algorithms,
)
from core.community_pipeline import (
    COMMUNITY_ALGORITHMS,
    build_community_pipeline_context,
    community_pipeline_metrics,
)
from tests.test_algorithm_test_lab import _repository


def test_member_engagement_suite_passes_all_seed_cases():
    repository = _repository()
    ensure_default_algorithms(repository)
    runner = AlgorithmTestRunner(repository)

    definition = repository.get_definition_by_name("member_engagement_score")
    cases = repository.list_cases(definition["id"])
    run = runner.run_suite(definition["id"])

    assert len(cases) == 12
    assert run["status"] == "passed"
    assert run["passed"] == 12
    assert run["failed"] == 0


def test_community_pipeline_metrics_ready_after_both_suites():
    repository = _repository()
    ensure_default_algorithms(repository)
    runner = AlgorithmTestRunner(repository)

    for algorithm_name in COMMUNITY_ALGORITHMS:
        definition = repository.get_definition_by_name(algorithm_name)
        run = runner.run_suite(definition["id"])
        assert run["status"] == "passed"

    metrics = community_pipeline_metrics(repository)
    assert metrics["status"] == "Ready"
    assert metrics["ready_count"] == len(COMMUNITY_ALGORITHMS)
    assert metrics["failed"] == 0


def test_community_pipeline_metrics_use_latest_run_not_history():
    repository = _repository()
    ensure_default_algorithms(repository)
    runner = AlgorithmTestRunner(repository)

    for algorithm_name in COMMUNITY_ALGORITHMS:
        definition = repository.get_definition_by_name(algorithm_name)
        runner.run_suite(definition["id"])

    metrics = community_pipeline_metrics(repository)
    assert metrics["passed"] == metrics["total"]
    assert metrics["failed"] == 0
    for suite in metrics["suites"]:
        assert suite["passed"] == suite["total_cases"]
        assert suite["failed"] == 0


def test_seed_upsert_updates_existing_case_payload():
    repository = _repository()
    ensure_default_algorithms(repository)
    definition = repository.get_definition_by_name("member_engagement_score")
    cases = repository.list_cases(definition["id"])
    visitor_case = next(case for case in cases if case["name"] == "visitante novo sem atividade")
    repository.update_case(
        str(visitor_case["id"]),
        input_payload={"member_id": "stale"},
        expected_output={"tier": "Legend"},
        tags=["stale"],
    )

    ensure_default_algorithms(repository)
    refreshed = next(case for case in repository.list_cases(definition["id"]) if case["name"] == "visitante novo sem atividade")
    assert refreshed["input_payload"]["member_id"] == "m1"
    assert refreshed["expected_output"]["tier"] == "Visitor"


def test_export_community_pipeline_handoff_writes_markdown(tmp_path):
    repository = _repository()
    ensure_default_algorithms(repository)
    runner = AlgorithmTestRunner(repository)
    for algorithm_name in COMMUNITY_ALGORITHMS:
        definition = repository.get_definition_by_name(algorithm_name)
        runner.run_suite(definition["id"])

    from core.community_pipeline import PIPELINE_HANDOFF_FILENAME, export_community_pipeline_handoff

    paths = export_community_pipeline_handoff(repository, tmp_path)
    pipeline_path = tmp_path / PIPELINE_HANDOFF_FILENAME
    assert paths["pipeline"] == str(pipeline_path)
    content = pipeline_path.read_text(encoding="utf-8")
    assert "Community Pipeline Implementation Context" in content
    assert "member_engagement_score" in content
    assert "community_bot_engine" in content


def test_community_pipeline_context_includes_both_algorithms():
    repository = _repository()
    ensure_default_algorithms(repository)
    runner = AlgorithmTestRunner(repository)

    for algorithm_name in COMMUNITY_ALGORITHMS:
        definition = repository.get_definition_by_name(algorithm_name)
        runner.run_suite(definition["id"])

    context = build_community_pipeline_context(repository)

    assert "Contexto Técnico — Community Pipeline" in context
    assert "member_engagement_score" in context
    assert "community_bot_engine" in context
    assert "Score de membro → Bot Engine" in context