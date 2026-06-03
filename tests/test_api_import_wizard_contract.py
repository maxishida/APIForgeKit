import json

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
