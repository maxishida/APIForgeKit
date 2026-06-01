from __future__ import annotations

import json
from datetime import UTC, datetime

from nicegui import ui

from core.algorithm_test_lab import build_algorithm_context
from core.api_test_lab import build_api_context
from core.database import database_status
from core.observability import build_live_context, export_observability_report
from core.report_bundle import create_report_bundle
from core.token_usage import build_token_usage_context
from ui.components.alerts import db_offline


def render_context_builder(services) -> None:
    status = database_status(services.engine)
    runs = services.observability_repository.list_runs(limit=50) if status["online"] else []
    events = services.observability_repository.list_events(limit=500) if status["online"] else []
    algorithm_metrics = services.algorithm_repository.metrics() if status["online"] else {"total_results": 0, "passed": 0, "failed": 0}
    api_metrics = services.api_test_repository.metrics() if status["online"] else {"total_results": 0, "passed": 0, "failed": 0}
    if not status["online"]:
        db_offline(str(status["error"]))
    api_context = build_live_context(runs, events)
    algorithm_context = build_algorithm_context(services.algorithm_repository) if status["online"] else ""
    generic_api_context = build_api_context(services.api_test_repository) if status["online"] else ""
    token_context = build_token_usage_context(services.token_usage_repository) if status["online"] else ""
    context_parts = [api_context, algorithm_context, generic_api_context, token_context]
    context = "\n\n---\n\n".join(part for part in context_parts if part)

    with ui.grid(columns=2).classes("w-full gap-4"):
        with ui.column().classes("afk-card gap-3").style("padding:18px;"):
            ui.label("Resumo Técnico").classes("text-xl font-bold")
            ui.label(f"Runs analisadas: {len(runs)}").classes("afk-muted")
            ui.label(f"Eventos analisados: {len(events)}").classes("afk-muted")
            ui.label(f"Resultados de algoritmo: {algorithm_metrics['total_results']}").classes("afk-muted")
            ui.label(f"Resultados de API genérica: {api_metrics['total_results']}").classes("afk-muted")
            ui.label("Evidências reais para entender payloads, falhas, custo, latência, regras e limites.").classes("afk-muted")
            with ui.row().classes("gap-3"):
                ui.button("Exportar Relatórios", icon="download", on_click=lambda: _export(services, runs, events, context)).classes("afk-primary-btn")
                ui.button("Copiar Contexto", icon="content_copy", on_click=lambda: _copy(context)).classes("afk-ghost-btn")
        with ui.column().classes("afk-card gap-3").style("padding:18px;"):
            ui.label("Fluxo operacional").classes("text-xl font-bold")
            for step in ["Test Case", "Runner", "Validator", "Structured Log", "PostgreSQL", "Custo", "Contexto técnico"]:
                ui.label(step).classes("afk-neon font-semibold")

    with ui.column().classes("afk-card w-full").style("padding:18px;"):
        ui.markdown(context).classes("w-full")


def _export(services, runs: list[dict[str, object]], events: list[dict[str, object]], context: str) -> None:
    paths = export_observability_report(services.reports_dir, runs, events)
    context_path = services.reports_dir / f"context_builder_{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}.md"
    context_path.write_text(context, encoding="utf-8")
    bundle = create_report_bundle(
        output_dir=services.reports_dir,
        name="context_builder_bundle",
        markdown=context,
        payload={"runs": runs, "events": events, "generated_at": datetime.now(UTC).isoformat()},
    )
    if runs:
        services.observability_repository.record_context_export(
            runs[0]["id"],
            "multi",
            json.dumps({**paths, "context": str(context_path), "bundle": bundle}),
            {"events": len(events), "generated_at": datetime.now(UTC).isoformat()},
        )
    else:
        services.algorithm_repository.record_context_export(
            "markdown",
            str(context_path),
            {"source": "context_builder", "generated_at": datetime.now(UTC).isoformat(), "bundle": bundle},
        )
    ui.notify(f"Contexto exportado: {context_path} | bundle: {bundle['zip']}", type="positive")


def _copy(context: str) -> None:
    ui.run_javascript(f"navigator.clipboard.writeText({json.dumps(context)})")
    ui.notify("Contexto copiado para a área de transferência.", type="positive")
