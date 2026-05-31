from sqlalchemy import create_engine

from core.database import build_session_factory, init_db
from core.lead_algorithm import LeadInput, calculate_lead_score
from core.repositories import LeadTestRepository, filter_records


def test_repository_saves_and_lists_lead_tests():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    init_db(engine)
    repository = LeadTestRepository(build_session_factory(engine))
    lead_input = LeadInput(
        lead_name="Repository Test",
        source="Ligação",
        message="quero comprar agora",
        budget="3000",
        urgency="alta",
        interest="alto",
        has_phone=True,
        has_email=True,
        previous_customer=False,
    )
    output = calculate_lead_score(lead_input)

    row = repository.create_from_result(lead_input, output)
    records = repository.list_recent()

    assert row.id == output.lead_id
    assert len(records) == 1
    assert records[0]["lead_name"] == "Repository Test"
    assert records[0]["classification"] == output.status
    assert records[0]["raw_input"]["source"] == "Ligação"
    assert records[0]["raw_output"]["score"] == output.score


def test_filter_records_applies_status_source_score_and_message_query():
    records = [
        {"source": "WhatsApp", "classification": "urgent_lead", "status": "success", "score": 90, "message": "comprar agora"},
        {"source": "LinkedIn", "classification": "cold_lead", "status": "success", "score": 20, "message": "pesquisa futura"},
    ]

    filtered = filter_records(records, source="WhatsApp", min_score=80, query="agora")

    assert filtered == [records[0]]
