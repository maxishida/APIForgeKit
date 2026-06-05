from core.demo_dashboard import build_demo_dashboard_snapshot


def test_demo_dashboard_snapshot_separates_algorithm_and_provider_tracks():
    snapshot = build_demo_dashboard_snapshot(
        db_status={"online": True, "latency_ms": 4.2},
        algorithm_metrics={"total_runs": 2, "total_results": 16, "passed": 15, "failed": 1, "pass_rate": 93.75},
        provider_metrics={"total_tests": 3, "success": 2, "failures": 1, "average_latency_ms": 820.5},
    )

    assert snapshot["database"]["label"] == "Online"
    assert snapshot["algorithm"]["title"] == "Algorithm Test Lab"
    assert snapshot["algorithm"]["primary_metric"] == "93.75%"
    assert snapshot["provider"]["title"] == "API Provider Lab"
    assert snapshot["provider"]["primary_metric"] == "3"
    assert snapshot["recommended_flow"] == [
        "Abrir Tutorial",
        "Rodar Algorithm Suite",
        "Rodar API Contract Dry-run",
        "Ver Dashboard",
        "Abrir Logs",
        "Gerar Context Builder",
        "Baixar Evidence Pack",
        "Usar contexto com IA",
    ]


def test_demo_dashboard_snapshot_handles_empty_metrics():
    snapshot = build_demo_dashboard_snapshot(
        db_status={"online": False, "latency_ms": 0},
        algorithm_metrics={},
        provider_metrics={},
    )

    assert snapshot["database"]["label"] == "Offline"
    assert snapshot["algorithm"]["primary_metric"] == "0%"
    assert snapshot["provider"]["primary_metric"] == "0"
