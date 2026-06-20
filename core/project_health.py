from __future__ import annotations

from pathlib import Path
from typing import Mapping


def build_project_health(
    *,
    db_status: Mapping[str, object],
    xai_runs: list[Mapping[str, object]],
    context_exports: list[Mapping[str, object]],
    events: list[Mapping[str, object]],
) -> dict[str, object]:
    database_online = bool(db_status.get("online"))
    latest_context = _latest_context_export_status(context_exports)
    failed_count = len([event for event in events if event.get("status") == "failed"])
    evidence_modes = _evidence_modes(events)
    readiness = _health_readiness(database_online, latest_context, failed_count)
    return {
        "database": {
            "status": "Online" if database_online else "Offline",
            "latency_ms": float(db_status.get("latency_ms") or 0),
        },
        "latest_xai_run": _latest_xai_run(xai_runs),
        "latest_context_export": latest_context,
        "failed_events": {"count": failed_count},
        "evidence_modes": evidence_modes,
        "readiness": readiness,
    }


def _latest_xai_run(runs: list[Mapping[str, object]]) -> dict[str, object]:
    if not runs:
        return {"status": "No runs", "id": "", "suite_name": ""}
    run = runs[0]
    return {
        "status": str(run.get("status") or "unknown"),
        "id": str(run.get("id") or ""),
        "suite_name": str(run.get("suite_name") or ""),
    }


def _latest_context_export_status(exports: list[Mapping[str, object]]) -> dict[str, object]:
    if not exports:
        return {"status": "No exports", "id": "", "missing_paths": [], "path_count": 0}
    export = exports[0]
    summary = export.get("summary") if isinstance(export.get("summary"), Mapping) else {}
    paths = summary.get("paths") if isinstance(summary.get("paths"), Mapping) else {}
    missing = [str(path) for path in paths.values() if path and not Path(str(path)).exists()]
    return {
        "status": "Missing files" if missing else str(summary.get("readiness") or "Ready"),
        "id": str(export.get("id") or ""),
        "missing_paths": missing,
        "path_count": len(paths),
    }


def _evidence_modes(events: list[Mapping[str, object]]) -> dict[str, int]:
    modes: dict[str, int] = {}
    for event in events:
        mode = str(event.get("evidence_mode") or "unknown")
        modes[mode] = modes.get(mode, 0) + 1
    return modes


def _health_readiness(database_online: bool, context: Mapping[str, object], failed_count: int) -> dict[str, object]:
    if not database_online:
        return {"status": "Offline", "message": "PostgreSQL offline."}
    if context.get("status") == "Missing files" or failed_count > 0:
        return {"status": "Needs attention", "message": "Revise falhas ou exports ausentes antes de demo."}
    if context.get("status") == "No exports":
        return {"status": "Needs tests", "message": "Gere um Context Builder export antes de implementar."}
    if context.get("status") == "Ready":
        return {"status": "Ready", "message": "Harness operacional para validação evidence-first."}
    return {"status": str(context.get("status") or "Needs tests"), "message": "Revise readiness antes de implementar."}
