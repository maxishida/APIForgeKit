from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
from nicegui import ui

from core.database import database_status
from ui.components.alerts import db_offline, empty_state
from ui.components.tables import observability_grid


def render_logs(services) -> None:
    status = database_status(services.engine)
    if not status["online"]:
        db_offline(str(status["error"]))
        empty_state("Logs indisponíveis", "A tabela de logs precisa do PostgreSQL online.")
        return

    all_records = services.observability_repository.list_events(limit=1000)
    filter_state = {"records": all_records}
    table_container = ui.column().classes("w-full")
    json_container = ui.column().classes("w-full")

    with ui.column().classes("afk-card w-full gap-4").style("padding:18px;"):
        ui.label("Filtros").classes("text-lg font-bold")
        with ui.grid(columns=6).classes("w-full gap-3"):
            provider = ui.select(["", "xai"], value="", label="Provider").classes("w-full")
            module = ui.select(["", "connectivity", "chat", "structured_outputs", "streaming", "function_calling", "agents", "voice"], value="", label="Módulo").classes("w-full")
            record_status = ui.select(["", "running", "success", "failed", "blocked"], value="", label="Status").classes("w-full")
            evidence_mode = ui.select(["", "real_http", "dry_run_contract", "seed_validation", "blocked", "legacy"], value="", label="Evidência").classes("w-full")
            min_latency = ui.number("Latência mínima", value=0, min=0).classes("w-full")
            query = ui.input("Buscar JSON").classes("w-full")

        def apply_filters() -> None:
            refreshed = services.observability_repository.list_events(limit=1000)
            filtered = _filter_records(
                refreshed,
                provider=provider.value or "",
                module=module.value or "",
                status=record_status.value or "",
                evidence_mode=evidence_mode.value or "",
                min_latency=float(min_latency.value or 0),
                query=query.value or "",
            )
            filter_state["records"] = filtered
            table_container.clear()
            with table_container:
                observability_grid(filtered)
            json_container.clear()
            with json_container:
                _json_details(filtered)

        with ui.row().classes("gap-3"):
            ui.button("Aplicar filtros", icon="filter_alt", on_click=apply_filters).classes("afk-primary-btn")
            ui.button("Atualizar", icon="refresh", on_click=lambda: ui.navigate.reload()).classes("afk-ghost-btn")
            ui.button("Exportar CSV", icon="download", on_click=lambda: _export_csv(filter_state["records"])).classes("afk-ghost-btn")
            ui.button("Exportar JSONL", icon="data_object", on_click=lambda: _export_jsonl(filter_state["records"])).classes("afk-ghost-btn")

    with table_container:
        observability_grid(all_records)
    with json_container:
        _json_details(all_records)


def _json_details(records: list[dict[str, object]]) -> None:
    with ui.column().classes("afk-card w-full gap-3").style("padding:18px;"):
        ui.label("JSON completo").classes("text-lg font-bold")
        if not records:
            ui.label("Nenhum registro para exibir.").classes("afk-muted")
            return
        options = {str(row["id"]): row for row in records}
        selected = ui.select(list(options), value=str(records[0]["id"]), label="Selecionar registro").classes("w-full")
        code = ui.code(json.dumps(options[selected.value], ensure_ascii=False, indent=2), language="json").classes("w-full")

        def update_code() -> None:
            code.set_content(json.dumps(options[selected.value], ensure_ascii=False, indent=2))

        selected.on_value_change(lambda _: update_code())


def _export_csv(records: list[dict[str, object]]) -> None:
    output_dir = Path("exports/logs")
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"observability_logs_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}.csv"
    pd.DataFrame(records).to_csv(path, index=False)
    ui.notify(f"CSV exportado: {path}", type="positive")


def _export_jsonl(records: list[dict[str, object]]) -> None:
    output_dir = Path("exports/logs")
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"observability_logs_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}.jsonl"
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    ui.notify(f"JSONL exportado: {path}", type="positive")


def _filter_records(
    records: list[dict[str, object]],
    *,
    provider: str,
    module: str,
    status: str,
    min_latency: float,
    query: str,
    evidence_mode: str = "",
) -> list[dict[str, object]]:
    query_lower = query.lower().strip()
    filtered: list[dict[str, object]] = []
    for record in records:
        if provider and record.get("provider") != provider:
            continue
        if module and record.get("module") != module:
            continue
        if status and record.get("status") != status:
            continue
        if evidence_mode and _record_evidence_mode(record) != evidence_mode:
            continue
        if float(record.get("latency_ms") or 0) < min_latency:
            continue
        if query_lower and query_lower not in json.dumps(record, ensure_ascii=False, default=str).lower():
            continue
        filtered.append(record)
    return filtered


def _record_evidence_mode(record: dict[str, object]) -> str:
    if record.get("evidence_mode"):
        return str(record["evidence_mode"])
    request = record.get("request") if isinstance(record.get("request"), dict) else {}
    response = record.get("response") if isinstance(record.get("response"), dict) else {}
    if request and request.get("evidence_mode"):
        return str(request["evidence_mode"])
    if response and response.get("evidence_mode"):
        return str(response["evidence_mode"])
    if record.get("status") == "blocked":
        return "blocked"
    return "real_http" if record.get("provider") else "unknown"
