import json

from core.lead_algorithm import LeadInput, calculate_lead_score
from core.lead_logger import append_lead_test_log


def test_jsonl_logger_appends_one_valid_record(tmp_path):
    lead_input = LeadInput(
        lead_name="Logger Test",
        source="WhatsApp",
        message="quero comprar agora",
        budget="2000",
        urgency="alta",
        interest="alto",
        has_phone=True,
        has_email=False,
        previous_customer=False,
    )
    output = calculate_lead_score(lead_input)
    log_path = tmp_path / "lead_tests.jsonl"

    append_lead_test_log(log_path, lead_input, output)

    lines = log_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    payload = json.loads(lines[0])
    assert payload["lab"] == "lead_algorithm_lab"
    assert payload["status"] == "success"
    assert payload["input"]["source"] == "WhatsApp"
    assert payload["output"]["status"] == output.status
    assert payload["score"] == output.score
    assert payload["classification"] == output.status
    assert payload["error"] is None
