from __future__ import annotations

from nicegui import ui


def empty_state(title: str, body: str) -> None:
    with ui.column().classes("afk-card w-full items-center justify-center text-center").style("min-height:220px;padding:32px;"):
        ui.icon("database_off").classes("text-5xl afk-muted")
        ui.label(title).classes("text-xl font-bold afk-title")
        ui.label(body).classes("text-sm afk-muted max-w-xl")


def db_offline(error: str | None = None) -> None:
    with ui.column().classes("afk-card w-full").style("padding:16px;border-color:rgba(239,68,68,.45);"):
        ui.label("PostgreSQL offline").classes("text-lg font-bold").style("color:#EF4444")
        ui.label("Suba o banco com `docker compose up -d` para executar e persistir testes.").classes("text-sm afk-muted")
        if error:
            ui.label(error[:260]).classes("text-xs afk-muted")
