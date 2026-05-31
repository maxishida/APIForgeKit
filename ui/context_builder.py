from __future__ import annotations

import json
from datetime import UTC, datetime

from nicegui import ui

from core.database import database_status
from core.observability import build_live_context, export_observability_report
from ui.components.alerts import db_offline


def render_context_builder(services) -> None:
    status = database_status(services.engine)
    runs = services.observability_repository.list_runs(limit=50) if status["online"] else []
    events = services.observability_repository.list_events(limit=500) if status["online"] else []
    if not status["online"]:
        db_offline(str(status["error"]))
    context = build_live_context(runs, events)

    with ui.grid(columns=2).classes("w-full gap-4"):
        with ui.column().classes("afk-card gap-3").style("padding:18px;"):
            ui.label("Resumo Técnico").classes("text-xl font-bold")
            ui.label(f"Runs analisadas: {len(runs)}").classes("afk-muted")
            ui.label(f"Eventos analisados: {len(events)}").classes("afk-muted")
            ui.label("Evidências reais para entender payloads, falhas, latência e limites da API.").classes("afk-muted")
            with ui.row().classes("gap-3"):
                ui.button("Exportar Relatórios", icon="download", on_click=lambda: _export(services, runs, events)).classes("afk-primary-btn")
                ui.button("Copiar Contexto", icon="content_copy", on_click=lambda: _copy(context)).classes("afk-ghost-btn")
        with ui.column().classes("afk-card gap-3").style("padding:18px;"):
            ui.label("Fluxo operacional").classes("text-xl font-bold")
            for step in ["Teste real", "Logs estruturados", "Evidências", "Contexto técnico", "Decisão de implementação"]:
                ui.label(step).classes("afk-neon font-semibold")

    with ui.column().classes("afk-card w-full").style("padding:18px;"):
        ui.markdown(context).classes("w-full")


def _export(services, runs: list[dict[str, object]], events: list[dict[str, object]]) -> None:
    paths = export_observability_report(services.reports_dir, runs, events)
    if runs:
        services.observability_repository.record_context_export(
            runs[0]["id"],
            "multi",
            json.dumps(paths),
            {"events": len(events), "generated_at": datetime.now(UTC).isoformat()},
        )
    ui.notify(f"Relatórios exportados: {paths['markdown']}", type="positive")


def _copy(context: str) -> None:
    ui.run_javascript(f"navigator.clipboard.writeText({json.dumps(context)})")
    ui.notify("Contexto copiado para a área de transferência.", type="positive")
