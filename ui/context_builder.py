from __future__ import annotations

import json
from html import escape

from nicegui import ui

from core.algorithm_test_lab import build_algorithm_context
from core.api_test_lab import build_api_context
from core.context_builder import SOURCE_MODE_LABELS, build_guided_context_bundle, export_guided_context_bundle
from core.database import database_status
from core.observability import build_live_context
from core.token_usage import build_token_usage_context
from ui.components.alerts import db_offline
from ui.components.cards import metric_card


def render_context_builder(services) -> None:
    status = database_status(services.engine)
    if not status["online"]:
        db_offline(str(status["error"]))

    source_options = {label: mode for mode, label in SOURCE_MODE_LABELS.items()}
    selected_source = ui.select(
        list(source_options),
        value="Algorithm + API",
        label="Fonte do contexto",
    ).classes("w-full")

    summary_container = ui.grid(columns=4).classes("w-full gap-4")
    workflow_container = ui.column().classes("afk-card w-full gap-3").style("padding:18px;")
    preview_container = ui.column().classes("afk-card w-full gap-4").style("padding:18px;")

    def build_bundle() -> dict[str, object]:
        runs = services.observability_repository.list_runs(limit=50) if status["online"] else []
        events = services.observability_repository.list_events(limit=500) if status["online"] else []
        algorithm_metrics = services.algorithm_repository.metrics() if status["online"] else _empty_metrics()
        api_metrics = services.api_test_repository.metrics() if status["online"] else _empty_metrics()
        live_metrics = services.observability_repository.metrics() if status["online"] else {"total_tests": 0, "success": 0, "failures": 0}
        token_estimates = services.token_usage_repository.list_estimates(limit=50) if status["online"] else []
        token_modes: dict[str, int] = {}
        for estimate in token_estimates:
            summary = estimate.get("summary") if isinstance(estimate.get("summary"), dict) else {}
            mode = str(summary.get("pricing_mode") or "seeded_estimate")
            token_modes[mode] = token_modes.get(mode, 0) + 1
        token_metrics = {"total_estimates": len(token_estimates), "evidence_modes": token_modes}
        return build_guided_context_bundle(
            source_mode=source_options[str(selected_source.value)],
            live_context=build_live_context(runs, events),
            algorithm_context=build_algorithm_context(services.algorithm_repository, algorithm_name="lead_score") if status["online"] else "",
            api_context=build_api_context(services.api_test_repository) if status["online"] else "",
            token_context=build_token_usage_context(services.token_usage_repository) if status["online"] else "",
            algorithm_metrics=algorithm_metrics,
            api_metrics=api_metrics,
            live_metrics=live_metrics,
            token_metrics=token_metrics,
        )

    def render_summary(bundle: dict[str, object]) -> None:
        readiness = bundle["readiness"]
        summary_container.clear()
        with summary_container:
            metric_card("Readiness", readiness["overall"]["status"], readiness["overall"]["message"], _status_color(readiness["overall"]["status"]))
            metric_card(
                "Algorithm",
                bundle["algorithm_metrics"]["total_results"],
                f"{bundle['algorithm_metrics']['passed']} passed / {bundle['algorithm_metrics']['failed']} failed",
                _status_color(readiness["algorithm"]["status"]),
            )
            metric_card(
                "API",
                bundle["api_metrics"]["total_results"],
                f"{bundle['api_metrics']['passed']} passed / {bundle['api_metrics']['failed']} failed",
                _status_color(readiness["api"]["status"]),
            )
            metric_card(
                "Token Evidence",
                bundle["token_metrics"]["total_estimates"],
                "Estimativas salvas para decisão de custo",
                _status_color(readiness["token"]["status"]),
            )

    def render_workflow(bundle: dict[str, object]) -> None:
        readiness = bundle["readiness"]
        workflow_container.clear()
        with workflow_container:
            with ui.row().classes("w-full items-center justify-between gap-4"):
                with ui.column().classes("gap-1"):
                    ui.label("Context Builder Workflow").classes("text-xl font-bold afk-title")
                    ui.label("Transforme logs reais em contexto técnico antes de pedir implementação para IA.").classes("afk-muted")
                ui.html(f"<span class='afk-badge' style='color:{_status_color(readiness['overall']['status'])}'>{readiness['overall']['status']}</span>")
            with ui.row().classes("gap-2"):
                for step in ["Teste Real", "Logs Estruturados", "Evidências", "Contexto Técnico", "Implementação"]:
                    ui.html(f"<span class='afk-badge'>{escape(step)}</span>")
            ui.label(str(readiness["overall"]["message"])).classes("afk-muted")
            with ui.row().classes("gap-3"):
                for export_type, label, icon in [
                    ("markdown", "Export Markdown", "article"),
                    ("json", "Export JSON", "data_object"),
                    ("html", "Export HTML", "html"),
                    ("zip", "Export ZIP", "inventory_2"),
                ]:
                    ui.button(label, icon=icon, on_click=lambda fmt=export_type: export_bundle(fmt)).classes("afk-primary-btn")
                ui.button("Copiar Contexto", icon="content_copy", on_click=copy_context).classes("afk-ghost-btn")
                ui.button("Atualizar", icon="refresh", on_click=refresh).classes("afk-ghost-btn")

    def render_preview(bundle: dict[str, object]) -> None:
        preview_container.clear()
        with preview_container:
            ui.label("Preview e metadados").classes("text-xl font-bold afk-title")
            tabs_payload = {
                "Contexto": bundle["context"],
                "Readiness": bundle["readiness"],
                "Métricas": {
                    "algorithm": bundle["algorithm_metrics"],
                    "api": bundle["api_metrics"],
                    "live": bundle["live_metrics"],
                    "token": bundle["token_metrics"],
                },
                "Fontes": bundle["contexts"],
                "Export JSON": bundle,
            }
            with ui.tabs().classes("w-full") as tabs:
                tab_map = {name: ui.tab(name) for name in tabs_payload}
            with ui.tab_panels(tabs, value=tab_map["Contexto"]).classes("w-full"):
                with ui.tab_panel(tab_map["Contexto"]):
                    ui.markdown(str(bundle["context"])).classes("w-full")
                for name in ["Readiness", "Métricas", "Fontes", "Export JSON"]:
                    with ui.tab_panel(tab_map[name]):
                        ui.code(json.dumps(tabs_payload[name], ensure_ascii=False, indent=2), language="json").classes("w-full")

    def export_bundle(format_name: str) -> None:
        try:
            bundle = build_bundle()
            paths = export_guided_context_bundle(services.reports_dir, bundle)
            _record_context_export(services, bundle, paths)
            ui.notify(f"{format_name.upper()} exportado: {paths[format_name]}", type="positive")
        except Exception as exc:  # noqa: BLE001 - user-facing export
            ui.notify(f"Erro ao exportar contexto: {exc}", type="negative")

    def copy_context() -> None:
        bundle = build_bundle()
        ui.run_javascript(f"navigator.clipboard.writeText({json.dumps(str(bundle['context']))})")
        ui.notify("Contexto copiado para a área de transferência.", type="positive")

    def refresh() -> None:
        bundle = build_bundle()
        render_summary(bundle)
        render_workflow(bundle)
        render_preview(bundle)

    selected_source.on_value_change(lambda _: refresh())
    refresh()


def _empty_metrics() -> dict[str, object]:
    return {"total_runs": 0, "total_results": 0, "passed": 0, "failed": 0, "pass_rate": 0, "average_latency_ms": 0}


def _status_color(status: str) -> str:
    if status == "Ready":
        return "#10B981"
    if status == "Has failures":
        return "#EF4444"
    return "#F59E0B"


def _record_context_export(services, bundle: dict[str, object], paths: dict[str, str]) -> None:
    readiness = bundle.get("readiness") if isinstance(bundle.get("readiness"), dict) else {}
    evidence_modes = {
        key: (readiness.get(key, {}) or {}).get("evidence_modes", {})
        for key in ("algorithm", "api", "live", "token")
        if isinstance(readiness.get(key, {}), dict)
    }
    summary = {
        "source": "context_builder",
        "source_mode": bundle["source_mode"],
        "readiness": bundle["readiness"]["overall"]["status"],
        "evidence_mode": "mixed",
        "evidence_modes": evidence_modes,
        "generated_at": bundle["generated_at"],
        "paths": paths,
    }
    runs = services.observability_repository.list_runs(limit=1)
    if runs:
        services.observability_repository.record_context_export(
            runs[0]["id"],
            "multi",
            json.dumps(paths, ensure_ascii=False),
            summary,
        )
        return
    services.algorithm_repository.record_context_export(
        "multi",
        json.dumps(paths, ensure_ascii=False),
        summary,
    )
