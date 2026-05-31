from __future__ import annotations


def build_demo_dashboard_snapshot(
    *,
    db_status: dict[str, object],
    algorithm_metrics: dict[str, object],
    provider_metrics: dict[str, object],
) -> dict[str, object]:
    db_online = bool(db_status.get("online"))
    algorithm_pass_rate = float(algorithm_metrics.get("pass_rate") or 0)
    provider_total = int(provider_metrics.get("total_tests") or 0)
    provider_success = int(provider_metrics.get("success") or 0)
    provider_failures = int(provider_metrics.get("failures") or 0)
    return {
        "database": {
            "label": "Online" if db_online else "Offline",
            "latency_ms": db_status.get("latency_ms", 0),
            "accent": "#10B981" if db_online else "#EF4444",
        },
        "algorithm": {
            "title": "Algorithm Test Lab",
            "primary_metric": f"{algorithm_pass_rate:g}%",
            "caption": f"{int(algorithm_metrics.get('passed') or 0)} passed / {int(algorithm_metrics.get('failed') or 0)} failed",
            "results": int(algorithm_metrics.get("total_results") or 0),
            "runs": int(algorithm_metrics.get("total_runs") or 0),
            "target": "/algorithm-test-lab",
            "accent": "#10B981" if algorithm_pass_rate >= 90 else "#F59E0B",
        },
        "provider": {
            "title": "API Provider Lab",
            "primary_metric": str(provider_total),
            "caption": f"{provider_success} success / {provider_failures} failed",
            "average_latency_ms": provider_metrics.get("average_latency_ms", 0),
            "target": "/live-dashboard",
            "accent": "#00D4FF",
        },
        "recommended_flow": [
            "Run demo suite",
            "Inspect structured JSON",
            "Generate AI context",
        ],
    }
