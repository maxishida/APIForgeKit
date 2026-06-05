from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine, select

from core.database import build_session_factory, init_db
from core.models import VoiceTest
from core.observability import ObservabilityRepository
from core.xai_voice_runner import VoiceLeadInput, XaiVoiceRunner


class FakeResponse:
    def __init__(self, *, status_code: int = 200, content: bytes = b"", payload: dict[str, object] | None = None):
        self.status_code = status_code
        self.content = content
        self._payload = payload or {}
        self.text = str(self._payload)

    def json(self) -> dict[str, object]:
        return self._payload


def _repository():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    init_db(engine)
    session_factory = build_session_factory(engine)
    return engine, session_factory, ObservabilityRepository(session_factory)


def test_voice_runner_records_roundtrip_events_and_voice_test(tmp_path):
    engine, session_factory, repository = _repository()
    calls: list[dict[str, object]] = []

    def fake_post(url: str, **kwargs):
        calls.append({"url": url, "kwargs": kwargs})
        if url.endswith("/tts"):
            return FakeResponse(content=b"synthetic-mp3")
        if url.endswith("/stt"):
            return FakeResponse(
                payload={
                    "text": "I want to buy today through WhatsApp.",
                    "language": "en",
                    "duration": 1.2,
                    "words": [{"text": "buy", "start": 0.1, "end": 0.3}],
                }
            )
        raise AssertionError(url)

    runner = XaiVoiceRunner(
        repository,
        output_dir=tmp_path,
        api_key="xai-test-key",
        http_post=fake_post,
        agent_responder=lambda transcript, lead: "Enviar para atendimento humano agora.",
        load_env=False,
    )

    run = runner.run_roundtrip(
        VoiceLeadInput(
            lead_name="Lead QA",
            user_message="I want to buy today through WhatsApp.",
            origin="WhatsApp",
            previous_page="/pricing",
        )
    )
    events = repository.list_events(limit=50, run_id=str(run["id"]))
    event_types = {event["event_type"] for event in events}

    assert run["status"] == "success"
    assert calls[0]["url"] == "https://api.x.ai/v1/tts"
    assert calls[1]["url"] == "https://api.x.ai/v1/stt"
    assert (Path(tmp_path) / f"xai_voice_{run['id']}.mp3").exists()
    assert {
        "lead_received",
        "user_message_received",
        "tts_request_started",
        "tts_audio_received",
        "stt_request_started",
        "transcript_received",
        "agent_response_request_started",
        "agent_response_received",
        "voice_call_completed",
    }.issubset(event_types)
    transcript_event = next(event for event in events if event["event_type"] == "transcript_received")
    assert transcript_event["response"]["transcript"] == "I want to buy today through WhatsApp."
    assert transcript_event["request"]["origin"] == "WhatsApp"
    assert transcript_event["request"]["previous_page"] == "/pricing"

    with session_factory() as session:
        voice_row = session.scalars(select(VoiceTest)).one()
    assert voice_row.status == "success"
    assert voice_row.classification == "sales_intent"
    assert voice_row.transcript == "I want to buy today through WhatsApp."


def test_voice_runner_records_missing_key_as_blocked(tmp_path, monkeypatch):
    monkeypatch.delenv("XAI_API_KEY", raising=False)
    _, _, repository = _repository()
    runner = XaiVoiceRunner(repository, output_dir=tmp_path, load_env=False)

    run = runner.run_roundtrip(VoiceLeadInput(lead_name="Lead", user_message="Comprar hoje", origin="WhatsApp"))
    events = repository.list_events(limit=20, run_id=str(run["id"]))

    assert run["status"] == "blocked"
    assert any(event["event_type"] == "api_error" for event in events)
    assert any(event["status"] == "blocked" for event in events)
    assert any(event["evidence_mode"] == "blocked" for event in events)
    assert "XAI_API_KEY" in events[0]["message"] or "XAI_API_KEY" in (events[0]["error"] or "")


def test_voice_runner_records_api_error_without_secret(tmp_path):
    _, _, repository = _repository()

    def failing_post(url: str, **kwargs):
        return FakeResponse(status_code=401, payload={"error": "bad key xai-secret-value"})

    runner = XaiVoiceRunner(
        repository,
        output_dir=tmp_path,
        api_key="xai-secret-value",
        http_post=failing_post,
        agent_responder=lambda transcript, lead: "not reached",
        load_env=False,
    )

    run = runner.run_roundtrip(VoiceLeadInput(lead_name="Lead", user_message="Comprar hoje", origin="WhatsApp"))
    events = repository.list_events(limit=20, run_id=str(run["id"]))

    assert run["status"] == "failed"
    error_event = next(event for event in events if event["event_type"] == "api_error")
    assert "xai-secret-value" not in (error_event["error"] or "")
    assert "xai-secret-value" not in str(error_event["response"])
