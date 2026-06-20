import json
from pathlib import Path

import pytest
from sqlalchemy import create_engine

from core.api_test_lab import (
    ApiTestRepository,
    ApiTestRunner,
    build_api_context,
    ensure_default_api_suites,
    export_api_suite,
    import_api_suite,
    validate_real_http_url,
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

    run = ApiTestRunner(repository).run_single_case(case["id"], allow_real_http=True)
    result = repository.list_results(run_id=run["id"])[0]

    assert run["status"] == "failed"
    assert result["structured_log"]["evidence_mode"] == "real_http"
    assert result["request"]["evidence_mode"] == "real_http"
    assert result["structured_log"]["error"]


def test_real_http_url_guard_blocks_private_targets_by_default():
    try:
        validate_real_http_url("http://127.0.0.1:8080/internal")
    except ValueError as exc:
        assert "rede local/privada" in str(exc)
    else:  # pragma: no cover - contract failure should be explicit
        raise AssertionError("Private HTTP target should be blocked by default")


def test_real_http_url_guard_allows_private_targets_with_explicit_opt_in():
    validate_real_http_url("http://127.0.0.1:8080/internal", allow_private_network=True)


def test_contract_suite_excludes_real_http_cases_without_network_permission():
    repository = _repository()
    suite = repository.create_suite(
        name="mixed_execution_modes",
        provider="local",
        description="Mixed contract and real HTTP cases",
        docs_url="https://example.com/docs",
    )
    repository.create_case(
        suite_id=suite["id"],
        name="dry-run case",
        method="POST",
        url="dry-run://local/validate",
        headers={},
        body={"ok": True},
        expected={"status_code": 200},
        dry_run=True,
        mock_response={"status_code": 200, "json": {"ok": True}},
    )
    repository.create_case(
        suite_id=suite["id"],
        name="real-http case",
        method="GET",
        url="http://127.0.0.1:9/should-not-run",
        headers={},
        body={},
        expected={"status_code": 200},
        dry_run=False,
    )

    run = ApiTestRunner(repository).run_contract_suite(suite["id"])
    results = repository.list_results(run_id=run["id"])

    assert run["status"] == "passed"
    assert run["total_cases"] == 1
    assert len(results) == 1
    assert results[0]["structured_log"]["evidence_mode"] == "dry_run_contract"


def test_generic_suite_defaults_to_contract_only_execution():
    repository = _repository()
    suite = repository.create_suite(
        name="safe_default_execution",
        provider="local",
        description="Default suite execution must stay local.",
        docs_url="https://example.com/docs",
    )
    repository.create_case(
        suite_id=suite["id"],
        name="contract case",
        method="POST",
        url="dry-run://local/validate",
        headers={},
        body={"ok": True},
        expected={"status_code": 200},
        dry_run=True,
        mock_response={"status_code": 200, "json": {"ok": True}},
    )
    repository.create_case(
        suite_id=suite["id"],
        name="real case",
        method="GET",
        url="http://127.0.0.1:9/should-not-run",
        headers={},
        body={},
        expected={"status_code": 200},
        dry_run=False,
    )

    run = ApiTestRunner(repository).run_suite(suite["id"])

    assert run["status"] == "passed"
    assert run["total_cases"] == 1


def test_contract_suite_rejects_a_suite_without_dry_run_cases():
    repository = _repository()
    suite = repository.create_suite(
        name="real_only_execution",
        provider="local",
        description="Suite requiring explicit HTTP authorization.",
        docs_url="https://example.com/docs",
    )
    repository.create_case(
        suite_id=suite["id"],
        name="real case",
        method="GET",
        url="http://127.0.0.1:9/should-not-run",
        headers={},
        body={},
        expected={"status_code": 200},
        dry_run=False,
    )

    with pytest.raises(ValueError, match="No test cases match"):
        ApiTestRunner(repository).run_contract_suite(suite["id"])


def test_real_http_single_case_is_blocked_without_explicit_authorization():
    repository = _repository()
    suite = repository.create_suite(
        name="single_real_http",
        provider="local",
        description="Single real HTTP case",
        docs_url="https://example.com/docs",
    )
    case = repository.create_case(
        suite_id=suite["id"],
        name="private endpoint",
        method="GET",
        url="http://127.0.0.1:9/should-not-run",
        headers={},
        body={},
        expected={"status_code": 200},
        dry_run=False,
    )

    run = ApiTestRunner(repository).run_single_case(case["id"], allow_real_http=False)
    result = repository.list_results(run_id=run["id"])[0]

    assert run["status"] == "failed"
    assert result["structured_log"]["evidence_mode"] == "blocked"
    assert "explicit authorization" in (result["structured_log"]["error"] or "")


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


def test_api_suite_export_replaces_secret_headers_with_safe_placeholder(tmp_path):
    repository = _repository()
    suite = repository.create_suite(
        name="secret_export_suite",
        provider="custom",
        description="Suite with a secret header",
        docs_url="https://example.com/docs",
    )
    repository.create_case(
        suite_id=suite["id"],
        name="secret header",
        method="GET",
        url="dry-run://custom/validate",
        headers={"Authorization": "Bearer super-secret-token", "Content-Type": "application/json"},
        body={},
        expected={"status_code": 200},
        dry_run=True,
        mock_response={"status_code": 200, "json": {}},
    )

    export_path = export_api_suite(repository, suite["id"], tmp_path)
    payload = json.loads(Path(export_path).read_text(encoding="utf-8"))
    headers = payload["api_test_cases"][0]["headers"]

    assert "super-secret-token" not in Path(export_path).read_text(encoding="utf-8")
    assert headers["Authorization"] == "{{REDACTED_SECRET}}"
    assert headers["Content-Type"] == "application/json"


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
