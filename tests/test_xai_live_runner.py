from sqlalchemy import create_engine

from core.database import build_session_factory, init_db
from core.observability import ObservabilityRepository
from core.xai_live_runner import XaiLiveRunner


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
