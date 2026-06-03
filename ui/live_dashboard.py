from __future__ import annotations

import json
import threading
from datetime import datetime
from html import escape

from nicegui import ui

from core.database import database_status
from core.observability import build_live_context, export_observability_report
from core.xai_live_runner import XaiLiveRunner
from ui.components.alerts import db_offline, empty_state
from ui.components.cards import metric_card
from ui.components.charts import event_status_donut, event_volume_area, latency_timeline, module_event_bar


STATUS_COLORS = {
    "success": "#10B981",
    "running": "#00D4FF",
    "failed": "#EF4444",
    "blocked": "#F59E0B",
    "pending": "#9CA3AF",
}


def render_live_dashboard(services) -> None:
    status = database_status(services.engine)
    runner_state = {"active": False, "last_error": "", "last_result": None}

    if not status["online"]:
        db_offline(str(status["error"]))
        empty_state("Live Dashboard aguardando PostgreSQL", "Suba o banco com npm run db para gravar eventos reais.")
        return

    metrics_container = ui.grid(columns=4).classes("w-full gap-4")
    controls_container = ui.column().classes("afk-card w-full gap-4").style("padding:18px;")
    charts_container = ui.grid(columns=2).classes("w-full gap-4")
    stream_container = ui.column().classes("afk-card w-full gap-3").style("padding:18px;")
    detail_container = ui.column().classes("afk-card w-full gap-3").style("padding:18px;")

    with controls_container:
        with ui.row().classes("w-full items-center justify-between gap-4"):
            with ui.column().classes("gap-1"):
                ui.label("xAI Test Runner").classes("text-xl font-bold afk-title")
                ui.label("Conectividade, chat, streaming e function calling com logs gravados no PostgreSQL.").classes("afk-muted")
            with ui.row().classes("gap-3"):
                ui.button("Executar xAI Compact", icon="play_arrow", on_click=lambda: _start_xai_sequence(services, runner_state)).classes(
                    "afk-primary-btn"
                )
                ui.button("Exportar Relatório", icon="download", on_click=lambda: _export_report(services)).classes("afk-ghost-btn")
        with ui.grid(columns=5).classes("w-full gap-3"):
            status_filter = ui.select(["", "running", "success", "failed", "blocked"], value="", label="Status").classes("w-full")
            module_filter = ui.select(
                ["", "connectivity", "chat", "structured_outputs", "streaming", "function_calling", "agents", "voice"],
                value="",
                label="Módulo",
            ).classes("w-full")
            evidence_filter = ui.select(["", "real_http", "dry_run_contract", "seed_validation", "blocked", "legacy"], value="", label="Evidência").classes("w-full")
            query_filter = ui.input("Buscar evento, payload ou erro").classes("w-full")
            limit_filter = ui.select([50, 100, 200, 500], value=200, label="Eventos").classes("w-full")

    def refresh() -> None:
        metrics = services.observability_repository.metrics()
        events = services.observability_repository.list_events(limit=int(limit_filter.value or 200))
        runs = services.observability_repository.list_runs(limit=25)
        filtered_events = _filter_events(events, status_filter.value or "", module_filter.value or "", evidence_filter.value or "", query_filter.value or "")

        metrics_container.clear()
        with metrics_container:
            metric_card("Total de Testes", metrics["total_tests"], "Runs persistidas", "#00D4FF")
            metric_card("Testes Ativos", metrics["active_tests"] + int(runner_state["active"]), "Runner em execução", "#00D4FF")
            metric_card("Sucesso", metrics["success"], "Runs concluídas", "#10B981")
            metric_card("Falhas", metrics["failures"], "Runs com erro", "#EF4444")
            metric_card("Latência Média", f"{metrics['average_latency_ms']} ms", "Eventos com timing", "#F59E0B")
            metric_card("Tempo Médio", f"{metrics['average_time_ms']} ms", "Duração média observada", "#2563EB")
            metric_card("Requests", metrics["requests"], "Chamadas registradas", "#00D4FF")
            metric_card("Tokens / Custo", f"{metrics['tokens']} / ${metrics['estimated_cost']}", "Telemetria estimada", "#10B981")

        charts_container.clear()
        with charts_container:
            with ui.column().classes("afk-card").style("padding:12px;"):
                ui.plotly(event_status_donut(filtered_events)).classes("w-full")
            with ui.column().classes("afk-card").style("padding:12px;"):
                ui.plotly(module_event_bar(filtered_events)).classes("w-full")
            with ui.column().classes("afk-card").style("padding:12px;"):
                ui.plotly(latency_timeline(filtered_events)).classes("w-full")
            with ui.column().classes("afk-card").style("padding:12px;"):
                ui.plotly(event_volume_area(filtered_events)).classes("w-full")

        stream_container.clear()
        with stream_container:
            _render_event_stream(filtered_events, runner_state)

        detail_container.clear()
        with detail_container:
            _render_json_detail(filtered_events, runs)

    status_filter.on_value_change(lambda _: refresh())
    module_filter.on_value_change(lambda _: refresh())
    evidence_filter.on_value_change(lambda _: refresh())
    query_filter.on_value_change(lambda _: refresh())
    limit_filter.on_value_change(lambda _: refresh())
    refresh()
    ui.timer(2.0, refresh)


def _start_xai_sequence(services, runner_state: dict[str, object]) -> None:
    if runner_state["active"]:
        ui.notify("Uma sequência xAI já está rodando.", type="warning")
        return
    if not database_status(services.engine)["online"]:
        ui.notify("PostgreSQL offline. Suba o banco antes de executar testes reais.", type="negative")
        return

    runner_state["active"] = True
    runner_state["last_error"] = ""
    runner_state["last_result"] = None

    def worker() -> None:
        try:
            runner_state["last_result"] = XaiLiveRunner(services.observability_repository).run_compact_sequence()
        except Exception as exc:  # noqa: BLE001 - surfaced in the live panel
            runner_state["last_error"] = str(exc)
        finally:
            runner_state["active"] = False

    threading.Thread(target=worker, daemon=True).start()
    ui.notify("Sequência xAI iniciada. O Event Stream vai atualizar ao vivo.", type="positive")


def _export_report(services) -> None:
    runs = services.observability_repository.list_runs(limit=50)
    events = services.observability_repository.list_events(limit=500)
    paths = export_observability_report(services.reports_dir, runs, events)
    if runs:
        modes: dict[str, int] = {}
        for event in events:
            mode = str(event.get("evidence_mode") or "unknown")
            modes[mode] = modes.get(mode, 0) + 1
        services.observability_repository.record_context_export(
            runs[0]["id"],
            "multi",
            json.dumps(paths),
            {"events": len(events), "evidence_mode": "mixed", "evidence_modes": modes},
        )
    ui.notify(f"Relatório exportado: {paths['markdown']}", type="positive")


def _filter_events(events: list[dict[str, object]], status: str, module: str, evidence_mode: str, query: str) -> list[dict[str, object]]:
    query_lower = query.lower().strip()
    filtered: list[dict[str, object]] = []
    for event in events:
        if status and event.get("status") != status:
            continue
        if module and event.get("module") != module:
            continue
        if evidence_mode and event.get("evidence_mode") != evidence_mode:
            continue
        if query_lower:
            haystack = json.dumps(event, ensure_ascii=False, default=str).lower()
            if query_lower not in haystack:
                continue
        filtered.append(event)
    return filtered


def _render_event_stream(events: list[dict[str, object]], runner_state: dict[str, object]) -> None:
    with ui.row().classes("w-full items-center justify-between no-wrap"):
        with ui.column().classes("gap-0"):
            ui.label("Live Event Stream").classes("text-xl font-bold afk-title")
            ui.label("Eventos estruturados vindos do runner Python e gravados no PostgreSQL.").classes("afk-muted")
        active_label = "RUNNING" if runner_state["active"] else "IDLE"
        active_color = "#00D4FF" if runner_state["active"] else "#9CA3AF"
        ui.html(f"<span class='afk-badge' style='color:{active_color}'>{active_label}</span>")

    if runner_state["last_error"]:
        ui.html(f"<div style='color:#EF4444;font-size:13px'>{escape(str(runner_state['last_error']))}</div>")

    if not events:
        ui.label("Nenhum evento encontrado para os filtros atuais.").classes("afk-muted")
        return

    for event in reversed(events[:80]):
        color = STATUS_COLORS.get(str(event.get("status")), "#9CA3AF")
        timestamp = _format_time(str(event.get("timestamp") or ""))
        latency = float(event.get("latency_ms") or 0)
        message = escape(str(event.get("message") or ""))
        module = escape(str(event.get("module") or ""))
        test_name = escape(str(event.get("test_name") or ""))
        event_type = escape(str(event.get("event_type") or ""))
        evidence = escape(str(event.get("evidence_mode") or "unknown"))
        ui.html(
            f"""
            <div style="display:grid;grid-template-columns:92px 150px 140px 170px 1fr 100px;gap:12px;align-items:center;
                        border-top:1px solid rgba(255,255,255,.06);padding:10px 0;font-size:13px;">
              <code style="color:#9CA3AF">[{timestamp}]</code>
              <span class="afk-badge" style="color:{color};justify-content:center">{escape(str(event.get("status")))}</span>
              <span class="afk-badge" style="justify-content:center">{evidence}</span>
              <span style="color:#00D4FF;font-weight:700">{module}/{test_name}</span>
              <span><b>{event_type}</b> - {message}</span>
              <span style="color:#9CA3AF;text-align:right">{latency:.2f} ms</span>
            </div>
            """
        )


def _render_json_detail(events: list[dict[str, object]], runs: list[dict[str, object]]) -> None:
    ui.label("JSON Detail + Context Preview").classes("text-xl font-bold afk-title")
    if not events:
        ui.label("Sem JSON para exibir.").classes("afk-muted")
        return
    options = {str(event["id"]): event for event in events}
    selected = ui.select(list(options), value=str(events[0]["id"]), label="Evento").classes("w-full")
    code = ui.code(json.dumps(options[selected.value], ensure_ascii=False, indent=2), language="json").classes("w-full")

    def update_code() -> None:
        code.set_content(json.dumps(options[selected.value], ensure_ascii=False, indent=2))

    selected.on_value_change(lambda _: update_code())
    with ui.expansion("Contexto técnico gerado destes eventos", icon="article").classes("w-full"):
        ui.markdown(build_live_context(runs, events[:100])).classes("w-full")


def _format_time(value: str) -> str:
    try:
        return datetime.fromisoformat(value).strftime("%H:%M:%S")
    except ValueError:
        return "--:--:--"
