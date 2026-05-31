from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
from nicegui import ui

from core.database import database_status
from core.repositories import filter_records
from ui.components.alerts import db_offline, empty_state
from ui.components.tables import logs_grid


def render_logs(services) -> None:
    status = database_status(services.engine)
    if not status["online"]:
        db_offline(str(status["error"]))
        empty_state("Logs indisponíveis", "A tabela de logs precisa do PostgreSQL online.")
        return

    all_records = services.repository.list_recent(limit=1000)
    filter_state = {"records": all_records}
    table_container = ui.column().classes("w-full")
    json_container = ui.column().classes("w-full")

    with ui.column().classes("afk-card w-full gap-4").style("padding:18px;"):
        ui.label("Filtros").classes("text-lg font-bold")
        with ui.grid(columns=5).classes("w-full gap-3"):
            source = ui.select(["", "Instagram", "WhatsApp", "Landing Page", "LinkedIn", "Ligação"], value="", label="Origem").classes("w-full")
            classification = ui.select(["", "urgent_lead", "hot_lead", "warm_lead", "cold_lead", "invalid_lead"], value="", label="Classificação").classes("w-full")
            record_status = ui.select(["", "success", "failed"], value="", label="Status").classes("w-full")
            min_score = ui.number("Score mínimo", value=0, min=0, max=100).classes("w-full")
            query = ui.input("Buscar mensagem").classes("w-full")

        def apply_filters() -> None:
            filtered = filter_records(
                all_records,
                source=source.value or None,
                classification=classification.value or None,
                status=record_status.value or None,
                min_score=int(min_score.value or 0),
                query=query.value or None,
            )
            filter_state["records"] = filtered
            table_container.clear()
            with table_container:
                logs_grid(filtered)
            json_container.clear()
            with json_container:
                _json_details(filtered)

        with ui.row().classes("gap-3"):
            ui.button("Aplicar filtros", icon="filter_alt", on_click=apply_filters).classes("afk-primary-btn")
            ui.button("Atualizar", icon="refresh", on_click=lambda: ui.navigate.reload()).classes("afk-ghost-btn")
            ui.button("Exportar CSV", icon="download", on_click=lambda: _export_csv(filter_state["records"])).classes("afk-ghost-btn")
            ui.button("Exportar JSONL", icon="data_object", on_click=lambda: _export_jsonl(filter_state["records"])).classes("afk-ghost-btn")

    with table_container:
        logs_grid(all_records)
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
    path = output_dir / f"lead_logs_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}.csv"
    pd.DataFrame(records).to_csv(path, index=False)
    ui.notify(f"CSV exportado: {path}", type="positive")


def _export_jsonl(records: list[dict[str, object]]) -> None:
    output_dir = Path("exports/logs")
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"lead_logs_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}.jsonl"
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    ui.notify(f"JSONL exportado: {path}", type="positive")
