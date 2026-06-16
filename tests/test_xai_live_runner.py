from sqlalchemy import create_engine

from core.database import build_session_factory, init_db
from core.models import ApiRequest
from core.observability import ObservabilityRepository
from core.xai_live_runner import XaiLiveRunner


class FakeResponse:
    def __init__(self, status_code: int, payload: dict[str, object]):
        self.status_code = status_code
        self._payload = payload
        self.text = str(payload)

    def json(self) -> dict[str, object]:
        return self._payload


def test_xai_live_runner_records_missing_key_as_failed_event(monkeypatch):
    monkeypatch.delenv("XAI_API_KEY", raising=False)
    engine = create_engine("sqlite+pysqlite:///:memory:")
    init_db(engine)
    repository = ObservabilityRepository(build_session_factory(engine))

    runner = XaiLiveRunner(repository, load_env=False)
    run = runner.run_compact_sequence(stop_on_failure=True)
    events = repository.list_events(limit=20)

    assert run["status"] == "failed"
    assert any(event["test_name"] == "readiness" for event in events)
    assert any(event["status"] == "failed" for event in events)
    assert "XAI_API_KEY" in events[0]["message"]


def test_xai_live_runner_records_responses_api_basic_endpoint(monkeypatch):
    monkeypatch.setenv("XAI_API_KEY", "xai-test-secret")
    engine = create_engine("sqlite+pysqlite:///:memory:")
    init_db(engine)
    session_factory = build_session_factory(engine)
    repository = ObservabilityRepository(session_factory)
    captured: dict[str, object] = {}

    def fake_post(url: str, **kwargs: object) -> FakeResponse:
        captured["url"] = url
        captured["json"] = kwargs["json"]
        return FakeResponse(
            200,
            {
                "id": "resp_123",
                "output": [
                    {
                        "type": "message",
                        "content": [{"type": "output_text", "text": "api-lab-ok"}],
                    }
                ],
                "usage": {"input_tokens": 4, "output_tokens": 3, "total_tokens": 7},
            },
        )

    runner = XaiLiveRunner(repository, load_env=False, http_post=fake_post)
    run = repository.start_run("xai", "test", ["responses_api"])
    runner._run_responses_basic(run["id"])

    events = repository.list_events(limit=20, run_id=run["id"])
    with session_factory() as session:
        api_request = session.query(ApiRequest).one()

    assert captured["url"] == "https://api.x.ai/v1/responses"
    assert captured["json"]["store"] is False
    assert api_request.endpoint == "https://api.x.ai/v1/responses"
    assert any(event["module"] == "responses_api" and event["test_name"] == "basic" for event in events)
    started_event = [event for event in events if event["event_type"] == "request_started"][0]
    assert started_event["request"]["endpoint"] == "https://api.x.ai/v1/responses"
    success_event = [event for event in events if event["status"] == "success"][0]
    assert success_event["response"]["response_id"] == "resp_123"
    assert success_event["response"]["output_text_preview"] == "api-lab-ok"
    assert success_event["tokens"]["total_tokens"] == 7


def test_xai_live_runner_records_responses_api_failure_with_redacted_error(monkeypatch):
    monkeypatch.setenv("XAI_API_KEY", "xai-test-secret")
    engine = create_engine("sqlite+pysqlite:///:memory:")
    init_db(engine)
    repository = ObservabilityRepository(build_session_factory(engine))

    def fake_post(url: str, **kwargs: object) -> FakeResponse:
        raise RuntimeError("upstream rejected key xai-test-secret")

    runner = XaiLiveRunner(repository, load_env=False, http_post=fake_post)
    run = runner.run_compact_sequence(stop_on_failure=True)
    events = repository.list_events(limit=20, run_id=run["id"])

    failed = [event for event in events if event["module"] == "responses_api" and event["status"] == "failed"][0]
    assert run["status"] == "failed"
    assert "xai-test-secret" not in (failed["error"] or "")
    assert "[REDACTED_XAI_API_KEY]" in (failed["error"] or "")
