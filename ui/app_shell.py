from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from nicegui import ui
from sqlalchemy.engine import Engine

from core.database import database_status
from core.observability import ObservabilityRepository
from core.repositories import LeadTestRepository


@dataclass
class AppServices:
    engine: Engine
    repository: LeadTestRepository
    observability_repository: ObservabilityRepository
    log_path: object
    contexts_dir: object
    blueprints_dir: object
    reports_dir: object


_services: AppServices | None = None


def set_services(services: AppServices) -> None:
    global _services
    _services = services


def get_services() -> AppServices:
    if _services is None:
        raise RuntimeError("App services have not been configured")
    return _services


NAV_ITEMS = (
    ("Live Dashboard", "/", "monitor_heart"),
    ("Lead Algorithm Lab", "/lead-lab", "science"),
    ("Logs", "/logs", "terminal"),
    ("Context Builder", "/context-builder", "integration_instructions"),
    ("Blueprint Archive", "/blueprint", "account_tree"),
    ("Settings", "/settings", "settings"),
)


def render_shell(active: str, title: str, subtitle: str, content: Callable[[], None]) -> None:
    services = get_services()
    status = database_status(services.engine)
    metrics = (
        services.observability_repository.metrics()
        if status["online"]
        else {"total_tests": 0, "average_latency_ms": 0, "active_tests": 0}
    )
    db_label = "Online" if status["online"] else "Offline"
    db_color = "#10B981" if status["online"] else "#EF4444"

    with ui.left_drawer(value=True).classes("afk-sidebar").style("width:280px;padding:18px;"):
        ui.label("APIForgeKit").classes("text-2xl font-extrabold afk-title")
        ui.label("Studio").classes("text-sm afk-neon font-bold")
        ui.separator().classes("my-4 opacity-20")
        for label, target, icon in NAV_ITEMS:
            link_classes = "afk-link afk-link-active" if active == label else "afk-link"
            with ui.link(target=target).classes(link_classes):
                with ui.row().classes("items-center gap-3 no-wrap"):
                    ui.icon(icon).classes("text-lg")
                    ui.label(label).classes("text-sm font-semibold")
        ui.space()
        with ui.column().classes("afk-card w-full gap-1").style("padding:14px;margin-top:24px;"):
            ui.label("PostgreSQL").classes("text-xs afk-muted uppercase font-bold")
            ui.html(
                f"<span class='afk-badge' style='color:{db_color}'><span style='width:7px;height:7px;border-radius:999px;background:{db_color}'></span>{db_label}</span>"
            )
            ui.label(f"Latência: {status['latency_ms']} ms").classes("text-xs afk-muted")
            ui.label("Versão: V1 NiceGUI").classes("text-xs afk-muted")

    with ui.header(elevated=False).classes("afk-header").style("height:76px;"):
        with ui.row().classes("w-full items-center justify-between no-wrap"):
            with ui.column().classes("gap-0"):
                ui.label(title).classes("text-xl font-extrabold afk-title")
                ui.label(subtitle).classes("text-xs afk-muted")
            with ui.row().classes("items-center gap-3 no-wrap"):
                ui.html(f"<span class='afk-badge' style='color:{db_color}'>DB {db_label}</span>")
                ui.html(f"<span class='afk-badge'>Runs {metrics['total_tests']}</span>")
                ui.html(f"<span class='afk-badge'>Active {metrics['active_tests']}</span>")
                ui.html(f"<span class='afk-badge'>Avg Latency {metrics['average_latency_ms']} ms</span>")
                ui.button("Live Tests", icon="play_arrow", on_click=lambda: ui.navigate.to("/")).classes("afk-primary-btn")

    with ui.column().classes("afk-page w-full gap-6"):
        content()
