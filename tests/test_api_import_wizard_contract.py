import json
from pathlib import Path

from sqlalchemy import create_engine

from core.api_test_lab import ApiTestRepository, import_api_suite_payload
from core.database import build_session_factory, init_db
from ui import api_lab


def _repository() -> ApiTestRepository:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    init_db(engine)
    return ApiTestRepository(build_session_factory(engine))


def test_api_lab_declares_visual_import_wizard_copy_and_example_payload():
    wizard_copy = " ".join(api_lab.API_IMPORT_WIZARD_COPY)

    assert "Paste suite JSON" in wizard_copy
    assert "Validate JSON" in wizard_copy
    assert "Import suite" in wizard_copy
    assert "api_test_suites" in api_lab.API_IMPORT_EXAMPLE
    assert "api_test_cases" in api_lab.API_IMPORT_EXAMPLE
    json.dumps(api_lab.API_IMPORT_EXAMPLE)


def test_api_lab_routes_contract_and_real_execution_through_distinct_runner_paths():
    source = Path(api_lab.__file__).read_text(encoding="utf-8")

    assert ".run_contract_suite(" in source
    assert ".run_real_http_suite(" in source
    assert "Caso HTTP real exige confirmação" in source


def test_home_contract_dry_run_uses_contract_runner():
    source = (Path(__file__).resolve().parents[1] / "ui" / "home.py").read_text(encoding="utf-8")

    assert "def _run_api_contract_dry_run" in source
    start = source.index("def _run_api_contract_dry_run")
    section = source[start : source.index("\n\ndef _project_health_panel", start)]
    assert ".run_contract_suite(" in section
    assert ".run_suite(" not in section


def test_import_api_suite_payload_roundtrip_without_temp_file():
    repository = _repository()
    payload = {
        "api_test_suites": [
            {
                "name": "local_import_pack",
                "provider": "local",
                "description": "Imported from UI payload",
                "docs_url": "https://example.com/docs",
                "tags": ["imported"],
            }
        ],
        "api_test_cases": [
            {
                "name": "imported ping",
                "method": "POST",
                "url": "dry-run://local/ping",
                "headers": {"Content-Type": "application/json"},
                "body": {"ping": True},
                "expected": {"status_code": 200, "json_contains": {"ok": True}},
                "dry_run": True,
                "mock_response": {"status_code": 200, "json": {"ok": True}},
                "timeout_seconds": 5,
                "tags": ["contract"],
                "enabled": True,
            }
        ],
    }

    suite = import_api_suite_payload(repository, payload)
    cases = repository.list_cases(str(suite["id"]))

    assert suite["name"] == "local_import_pack"
    assert len(cases) == 1
    assert cases[0]["name"] == "imported ping"
