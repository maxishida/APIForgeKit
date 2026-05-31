from __future__ import annotations

from nicegui import ui

from core.algorithm_test_lab import AlgorithmTestRunner, ensure_default_algorithms
from core.database import database_status
from core.demo_dashboard import build_demo_dashboard_snapshot
from ui.components.alerts import db_offline
from ui.components.cards import metric_card


def render_home(services) -> None:
    status = database_status(services.engine)
    if status["online"]:
        ensure_default_algorithms(services.algorithm_repository)
    else:
        db_offline(str(status["error"]))

    algorithm_metrics = services.algorithm_repository.metrics() if status["online"] else {}
    provider_metrics = services.observability_repository.metrics() if status["online"] else {}
    snapshot = build_demo_dashboard_snapshot(
        db_status=status,
        algorithm_metrics=algorithm_metrics,
        provider_metrics=provider_metrics,
    )

    with ui.grid(columns=4).classes("w-full gap-4"):
        metric_card("PostgreSQL", snapshot["database"]["label"], f"{snapshot['database']['latency_ms']} ms", snapshot["database"]["accent"])
        metric_card("Algorithm Pass Rate", snapshot["algorithm"]["primary_metric"], snapshot["algorithm"]["caption"], snapshot["algorithm"]["accent"])
        metric_card("Algorithm Results", snapshot["algorithm"]["results"], f"{snapshot['algorithm']['runs']} runs", "#2563EB")
        metric_card("API Provider Runs", snapshot["provider"]["primary_metric"], snapshot["provider"]["caption"], "#00D4FF")

    with ui.grid(columns=2).classes("w-full gap-4"):
        _track_card(
            title="Algorithm Test Lab",
            badge="Pure Python",
            caption="Valide lógica determinística com expected vs actual antes de pedir implementação para IA.",
            primary_label="Run Demo Suite",
            primary_icon="playlist_play",
            primary_action=lambda: _run_algorithm_demo(services),
            secondary_label="Open Lab",
            secondary_target="/algorithm-test-lab",
            accent="#10B981",
        )
        _track_card(
            title="API Provider Lab",
            badge="Live APIs",
            caption="Capture payload, response, latency and errors from provider tests like xAI.",
            primary_label="Open Provider Lab",
            primary_icon="monitor_heart",
            primary_action=lambda: ui.navigate.to("/live-dashboard"),
            secondary_label="View Logs",
            secondary_target="/logs",
            accent="#00D4FF",
        )

    with ui.column().classes("afk-card w-full gap-4").style("padding:18px;"):
        ui.label("Demo Flow").classes("text-xl font-bold afk-title")
        with ui.grid(columns=3).classes("w-full gap-3"):
            for index, step in enumerate(snapshot["recommended_flow"], start=1):
                ui.html(
                    f"""
                    <div style="border:1px solid rgba(0,212,255,.18);border-radius:8px;padding:16px;background:rgba(15,23,42,.58);">
                      <div style="color:#00D4FF;font-weight:800;font-size:13px;">STEP {index}</div>
                      <div style="color:#F9FAFB;font-weight:800;font-size:20px;margin-top:8px;">{step}</div>
                    </div>
                    """
                )
        with ui.row().classes("gap-3"):
            ui.button("Generate AI Context", icon="integration_instructions", on_click=lambda: ui.navigate.to("/context-builder")).classes("afk-primary-btn")
            ui.button("Open Source Tutorial", icon="article", on_click=lambda: ui.navigate.to("/tutorial")).classes("afk-ghost-btn")


def _track_card(
    *,
    title: str,
    badge: str,
    caption: str,
    primary_label: str,
    primary_icon: str,
    primary_action,
    secondary_label: str,
    secondary_target: str,
    accent: str,
) -> None:
    with ui.column().classes("afk-card gap-4").style("padding:20px;min-height:260px;"):
        with ui.row().classes("w-full items-center justify-between no-wrap"):
            ui.label(title).classes("text-2xl font-extrabold afk-title")
            ui.html(f"<span class='afk-badge' style='color:{accent}'>{badge}</span>")
        ui.label(caption).classes("afk-muted").style("font-size:14px;line-height:1.55;")
        ui.space()
        with ui.row().classes("gap-3"):
            ui.button(primary_label, icon=primary_icon, on_click=primary_action).classes("afk-primary-btn")
            ui.button(secondary_label, icon="open_in_new", on_click=lambda: ui.navigate.to(secondary_target)).classes("afk-ghost-btn")


def _run_algorithm_demo(services) -> None:
    status = database_status(services.engine)
    if not status["online"]:
        ui.notify("PostgreSQL offline. Rode npm run db antes da demo.", type="negative")
        return
    ensure_default_algorithms(services.algorithm_repository)
    definition = services.algorithm_repository.get_definition_by_name("lead_score")
    run = AlgorithmTestRunner(services.algorithm_repository).run_suite(str(definition["id"]))
    ui.notify(f"Demo suite: {run['passed']} passed / {run['failed']} failed.", type="positive" if run["failed"] == 0 else "warning")
    ui.navigate.to("/algorithm-test-lab")
