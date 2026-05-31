from __future__ import annotations

from nicegui import ui

from core.database import database_status


def render_settings(services) -> None:
    status = database_status(services.engine)
    with ui.grid(columns=2).classes("w-full gap-4"):
        with ui.column().classes("afk-card gap-3").style("padding:18px;"):
            ui.label("Database Status").classes("text-xl font-bold")
            ui.label(f"Online: {status['online']}").classes("afk-muted")
            ui.label(f"Latência: {status['latency_ms']} ms").classes("afk-muted")
            ui.label(f"Registros: {status['record_count']}").classes("afk-muted")
            ui.label(f"Último registro: {status['last_record']}").classes("afk-muted")
            if status["error"]:
                ui.label(str(status["error"])[:500]).classes("text-xs").style("color:#EF4444")
        with ui.column().classes("afk-card gap-3").style("padding:18px;"):
            ui.label("Comandos").classes("text-xl font-bold")
            ui.code("docker compose up -d\npython app.py\npython -m pytest -q", language="bash").classes("w-full")

    with ui.column().classes("afk-card w-full gap-3").style("padding:18px;"):
        ui.label("Local-first MVP").classes("text-xl font-bold")
        ui.label("O Studio não usa LLM, API externa, agentes, voice ou vision nesta V1.").classes("afk-muted")
        ui.label("PostgreSQL Docker é a fonte principal; JSONL é trilha de auditoria local.").classes("afk-muted")
