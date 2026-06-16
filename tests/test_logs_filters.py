from ui.logs import _filter_records
from ui.logs import LOG_MODULE_OPTIONS


def test_logs_filter_records_by_evidence_mode():
    records = [
        {"id": "1", "provider": "xai", "module": "chat", "status": "success", "latency_ms": 10, "evidence_mode": "real_http"},
        {"id": "2", "provider": "xai", "module": "voice", "status": "blocked", "latency_ms": 0, "evidence_mode": "blocked"},
    ]

    filtered = _filter_records(
        records,
        provider="",
        module="",
        status="",
        evidence_mode="blocked",
        min_latency=0,
        query="",
    )

    assert [record["id"] for record in filtered] == ["2"]


def test_logs_module_options_include_responses_api():
    assert "responses_api" in LOG_MODULE_OPTIONS
