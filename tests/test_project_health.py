from pathlib import Path

from core.project_health import build_project_health


def test_project_health_reports_ready_when_context_export_files_exist(tmp_path):
    md = tmp_path / "context.md"
    json_path = tmp_path / "context.json"
    html = tmp_path / "context.html"
    zip_path = tmp_path / "context.zip"
    for path in (md, json_path, html, zip_path):
        path.write_text("ok", encoding="utf-8")

    health = build_project_health(
        db_status={"online": True, "latency_ms": 4.2},
        xai_runs=[{"id": "run-1", "status": "success", "suite_name": "live_observability_compact"}],
        context_exports=[
            {
                "id": "export-1",
                "summary": {
                    "readiness": "Ready",
                    "paths": {
                        "markdown": str(md),
                        "json": str(json_path),
                        "html": str(html),
                        "zip": str(zip_path),
                    },
                },
            }
        ],
        events=[
            {"status": "success", "evidence_mode": "real_http"},
            {"status": "blocked", "evidence_mode": "blocked"},
        ],
    )

    assert health["database"]["status"] == "Online"
    assert health["latest_xai_run"]["status"] == "success"
    assert health["latest_context_export"]["status"] == "Ready"
    assert health["latest_context_export"]["missing_paths"] == []
    assert health["failed_events"]["count"] == 0
    assert health["readiness"]["status"] == "Ready"
    assert health["evidence_modes"] == {"real_http": 1, "blocked": 1}


def test_project_health_warns_when_context_export_points_to_missing_file(tmp_path):
    missing = tmp_path / "missing.zip"

    health = build_project_health(
        db_status={"online": True, "latency_ms": 4.2},
        xai_runs=[],
        context_exports=[
            {
                "id": "export-1",
                "summary": {
                    "readiness": "Ready",
                    "paths": {"zip": str(missing)},
                },
            }
        ],
        events=[{"status": "failed", "evidence_mode": "real_http"}],
    )

    assert health["latest_context_export"]["status"] == "Missing files"
    assert health["latest_context_export"]["missing_paths"] == [str(missing)]
    assert health["failed_events"]["count"] == 1
    assert health["readiness"]["status"] == "Needs attention"
