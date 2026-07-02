from pathlib import Path

from fastapi.testclient import TestClient

from core.config import get_settings
from core.report_downloads import register_report_download_routes


def test_download_reports_route_serves_existing_markdown(tmp_path, monkeypatch):
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    sample = reports_dir / "sample.md"
    sample.write_text("# sample", encoding="utf-8")
    monkeypatch.setattr(get_settings(), "reports_dir", reports_dir)

    register_report_download_routes()
    from nicegui import app

    client = TestClient(app)
    response = client.get("/download/reports/sample.md")

    assert response.status_code == 200
    assert "sample" in response.text