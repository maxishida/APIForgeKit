from __future__ import annotations

import json
from datetime import UTC, datetime

from nicegui import ui

from core.context_builder import build_technical_context, export_technical_context
from core.database import database_status
from ui.components.alerts import db_offline


def render_context_builder(services) -> None:
    status = database_status(services.engine)
    records = services.repository.list_recent(limit=100) if status["online"] else []
    if not status["online"]:
        db_offline(str(status["error"]))
    context = build_technical_context(records)

    with ui.grid(columns=2).classes("w-full gap-4"):
        with ui.column().classes("afk-card gap-3").style("padding:18px;"):
            ui.label("Resumo Técnico").classes("text-xl font-bold")
            ui.label(f"Registros analisados: {len(records)}").classes("afk-muted")
            ui.label("Regras, payloads e comportamentos prontos para orientar a implementação Next.js.").classes("afk-muted")
            with ui.row().classes("gap-3"):
                ui.button("Exportar Markdown", icon="download", on_click=lambda: _export(services, records)).classes("afk-primary-btn")
                ui.button("Copiar Contexto", icon="content_copy", on_click=lambda: _copy(context)).classes("afk-ghost-btn")
        with ui.column().classes("afk-card gap-3").style("padding:18px;"):
            ui.label("Arquivos Next.js sugeridos").classes("text-xl font-bold")
            for path in ["/lib/lead-score.ts", "/types/lead.ts", "/app/api/leads/route.ts", "/components/dashboard/LeadScoreChart.tsx"]:
                ui.label(path).classes("afk-neon font-semibold")

    with ui.column().classes("afk-card w-full").style("padding:18px;"):
        ui.markdown(context).classes("w-full")


def _export(services, records: list[dict[str, object]]) -> None:
    path = services.contexts_dir / f"lead_context_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}.md"
    export_technical_context(path, records)
    ui.notify(f"Contexto exportado: {path}", type="positive")


def _copy(context: str) -> None:
    ui.run_javascript(f"navigator.clipboard.writeText({json.dumps(context)})")
    ui.notify("Contexto copiado para a área de transferência.", type="positive")
