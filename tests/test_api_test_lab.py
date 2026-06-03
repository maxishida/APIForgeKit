import json
from pathlib import Path

from sqlalchemy import create_engine

from core.api_test_lab import (
    ApiTestRepository,
    ApiTestRunner,
    build_api_context,
    ensure_default_api_suites,
    export_api_suite,
    import_api_suite,
    validate_api_response,
)
from core.database import build_session_factory, init_db


def _repository() -> ApiTestRepository:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    init_db(engine)
    return ApiTestRepository(build_session_factory(engine))


def test_validate_api_response_supports_status_json_contains_and_text_search():
    result = validate_api_response(
        expected={
            "status_code": 200,
            "json_contains": {"ok": True, "data": {"lead_status": "qualified"}},
            "body_contains": "qualified",
        },
        actual={
            "status_code": 200,
            "json": {"ok": True, "data": {"lead_status": "qualified", "score": 88}},
            "text": json.dumps({"ok": True, "data": {"lead_status": "qualified"}}),
        },
    )

    assert result["passed"] is True
    assert result["mismatches"] == []


def test_default_whatsapp_suite_runs_in_dry_run_mode_and_persists_results():
    repository = _repository()
    ensure_default_api_suites(repository)
    suite = repository.get_suite_by_name("whatsapp_validation_pack")

    run = ApiTestRunner(repository).run_suite(suite["id"])
    results = repository.list_results(run_id=run["id"])

    assert run["status"] == "passed"
    assert run["total_cases"] >= 4
    assert run["passed"] == run["total_cases"]
    assert all(result["structured_log"]["provider"] == "whatsapp" for result in results)
    assert all(result["structured_log"]["evidence_mode"] == "dry_run_contract" for result in results)
    assert all(result["request"]["evidence_mode"] == "dry_run_contract" for result in results)
    assert {result["structured_log"]["test_name"] for result in results} >= {
        "valid outbound text payload",
        "missing phone should fail contract",
    }


def test_real_http_case_records_real_http_evidence_mode_when_request_fails():
    repository = _repository()
    suite = repository.create_suite(
        name="real_http_failure",
        provider="local",
        description="Real HTTP failure suite",
        docs_url="https://example.com/docs",
        tags=["real_http"],
    )
    case = repository.create_case(
        suite_id=suite["id"],
        name="unreachable endpoint",
        method="POST",
        url="http://127.0.0.1:9/unreachable",
        headers={},
        body={"ok": True},
        expected={"status_code": 200},
        dry_run=False,
        mock_response={},
        timeout_seconds=1,
        tags=["real_http"],
    )

    run = ApiTestRunner(repository).run_single_case(case["id"])
    result = repository.list_results(run_id=run["id"])[0]

    assert run["status"] == "failed"
    assert result["structured_log"]["evidence_mode"] == "real_http"
    assert result["request"]["evidence_mode"] == "real_http"
    assert result["structured_log"]["error"]


def test_api_suite_export_and_import_roundtrip(tmp_path):
    repository = _repository()
    ensure_default_api_suites(repository)
    suite = repository.get_suite_by_name("whatsapp_validation_pack")

    export_path = export_api_suite(repository, suite["id"], tmp_path)
    imported_repository = _repository()
    imported = import_api_suite(imported_repository, Path(export_path))

    assert imported["name"] == "whatsapp_validation_pack"
    assert len(imported_repository.list_cases(imported["id"])) == len(repository.list_cases(suite["id"]))
    assert "api_test_suites" in Path(export_path).read_text(encoding="utf-8")


def test_api_runner_records_failed_diff_for_wrong_expectation():
    repository = _repository()
    suite = repository.create_suite(
        name="contract_failure",
        provider="demo",
        description="Failure suite",
        docs_url="https://example.com/docs",
        tags=["test"],
    )
    case = repository.create_case(
        suite_id=suite["id"],
        name="wrong expectation",
        method="POST",
        url="dry-run://contract-test",
        headers={},
        body={"ok": True},
        expected={"status_code": 201, "json_contains": {"ok": False}},
        dry_run=True,
        mock_response={"status_code": 200, "json": {"ok": True}, "text": "{\"ok\": true}"},
        tags=["negative"],
    )

    run = ApiTestRunner(repository).run_single_case(case["id"])
    result = repository.list_results(run_id=run["id"])[0]

    assert run["status"] == "failed"
    assert result["status"] == "failed"
    assert result["diff"]["mismatches"][0]["field"] == "status_code"


def test_api_context_includes_payloads_failures_and_recommendations():
    repository = _repository()
    ensure_default_api_suites(repository)
    suite = repository.get_suite_by_name("whatsapp_validation_pack")
    ApiTestRunner(repository).run_suite(suite["id"])

    context = build_api_context(repository)

    assert "Contexto Técnico - Generic API Test Lab" in context
    assert "whatsapp_validation_pack" in context
    assert "Payloads validados" in context
    assert "missing phone should fail contract" in context
