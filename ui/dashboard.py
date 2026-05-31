from __future__ import annotations

from nicegui import ui

from core.database import database_status
from ui.components.alerts import db_offline, empty_state
from ui.components.cards import metric_card
from ui.components.charts import (
    average_score_area,
    channel_score_bar,
    classification_donut,
    origin_bar,
    score_histogram,
    test_evolution,
)


def render_dashboard(services) -> None:
    status = database_status(services.engine)
    if not status["online"]:
        db_offline(str(status["error"]))
        empty_state("Dashboard aguardando dados", "O banco precisa estar online para carregar métricas persistidas.")
        return

    metrics = services.repository.metrics()
    records = services.repository.list_recent(limit=500)
    classifications = metrics["classifications"]
    hot = classifications.get("hot_lead", 0) + classifications.get("urgent_lead", 0)
    warm = classifications.get("warm_lead", 0)
    cold = classifications.get("cold_lead", 0)
    invalid = classifications.get("invalid_lead", 0)
    conversion = round((hot / metrics["total"]) * 100, 2) if metrics["total"] else 0
    latest = metrics["latest"]["created_at"] if metrics["latest"] else "Sem testes"

    with ui.grid(columns=4).classes("w-full gap-4"):
        metric_card("Total Tests", metrics["total"], "Leads testados", "#00D4FF")
        metric_card("Hot Leads", hot, "Hot + urgent", "#10B981")
        metric_card("Warm Leads", warm, "Em nutrição", "#F59E0B")
        metric_card("Cold / Invalid", cold + invalid, "Baixa prioridade", "#EF4444")
        metric_card("Average Score", metrics["average_score"], "Score médio", "#00D4FF")
        metric_card("Database Status", "Online", f"{status['latency_ms']} ms", "#10B981")
        metric_card("Latest Test", latest, "Último registro", "#2563EB")
        metric_card("Conversão Simulada", f"{conversion}%", "Hot rate", "#10B981")

    with ui.grid(columns=2).classes("w-full gap-4"):
        with ui.column().classes("afk-card").style("padding:12px;"):
            ui.plotly(classification_donut(metrics["classifications"])).classes("w-full")
        with ui.column().classes("afk-card").style("padding:12px;"):
            ui.plotly(score_histogram(records)).classes("w-full")
        with ui.column().classes("afk-card").style("padding:12px;"):
            ui.plotly(origin_bar(metrics["sources"])).classes("w-full")
        with ui.column().classes("afk-card").style("padding:12px;"):
            ui.plotly(channel_score_bar(metrics["channel_average_scores"])).classes("w-full")
        with ui.column().classes("afk-card").style("padding:12px;"):
            ui.plotly(test_evolution(metrics["daily_counts"])).classes("w-full")
        with ui.column().classes("afk-card").style("padding:12px;"):
            ui.plotly(average_score_area(metrics["daily_average_scores"])).classes("w-full")

    with ui.column().classes("afk-card w-full").style("padding:18px;"):
        ui.label("Últimos testes").classes("text-lg font-bold afk-title")
        recent = records[:6]
        if not recent:
            ui.label("Nenhum teste executado ainda.").classes("afk-muted")
        for record in recent:
            with ui.row().classes("w-full items-center justify-between no-wrap").style("border-top:1px solid rgba(255,255,255,.06);padding:10px 0;"):
                ui.label(str(record["lead_name"]) or "Lead sem nome").classes("font-semibold")
                ui.label(str(record["source"])).classes("afk-muted")
                ui.label(str(record["classification"])).classes("afk-neon font-bold")
                ui.label(str(record["score"])).classes("font-bold")
