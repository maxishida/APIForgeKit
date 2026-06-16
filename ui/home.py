from __future__ import annotations

from html import escape

from nicegui import ui

from core.algorithm_test_lab import AlgorithmTestRunner, ensure_default_algorithms
from core.api_test_lab import ApiTestRunner, ensure_default_api_suites
from core.database import database_status
from core.demo_dashboard import build_demo_dashboard_snapshot
from core.project_health import build_project_health
from core.workflow import build_official_journey_progress
from ui.components.alerts import db_offline
from ui.components.cards import metric_card


def render_home(services) -> None:
    status = database_status(services.engine)
    if status["online"]:
        ensure_default_algorithms(services.algorithm_repository)
    else:
        db_offline(str(status["error"]))

    algorithm_metrics = services.algorithm_repository.metrics() if status["online"] else {}
    api_metrics = services.api_test_repository.metrics() if status["online"] else {}
    provider_metrics = services.observability_repository.metrics() if status["online"] else {}
    provider_events = services.observability_repository.list_events(limit=200) if status["online"] else []
    context_exports = services.observability_repository.list_context_exports(limit=5) if status["online"] else []
    xai_runs = services.observability_repository.list_runs(limit=1, provider="xai") if status["online"] else []
    project_health = build_project_health(
        db_status=status,
        xai_runs=xai_runs,
        context_exports=context_exports,
        events=provider_events,
    )
    snapshot = build_demo_dashboard_snapshot(
        db_status=status,
        algorithm_metrics=algorithm_metrics,
        provider_metrics=provider_metrics,
    )
    journey_steps = build_official_journey_progress(
        db_online=bool(status["online"]),
        algorithm_metrics=algorithm_metrics,
        api_metrics=api_metrics,
        provider_metrics=provider_metrics,
    )

    with ui.grid(columns=4).classes("w-full gap-4"):
        metric_card("PostgreSQL", snapshot["database"]["label"], f"{snapshot['database']['latency_ms']} ms", snapshot["database"]["accent"])
        metric_card("Algorithm Pass Rate", snapshot["algorithm"]["primary_metric"], snapshot["algorithm"]["caption"], snapshot["algorithm"]["accent"])
        metric_card("Generic API Pass", f"{float(api_metrics.get('pass_rate') or 0):g}%", f"{int(api_metrics.get('passed') or 0)} passed", "#00D4FF")
        metric_card("Provider Runs", snapshot["provider"]["primary_metric"], snapshot["provider"]["caption"], "#2563EB")

    _project_health_panel(project_health)

    with ui.grid(columns=2).classes("w-full gap-4"):
        _track_card(
            title="Algorithm Test Lab",
            badge="Pure Python",
            caption="Valide lógica determinística com expected vs actual antes de pedir implementação para IA.",
            primary_label="Run Seed Validation",
            primary_icon="playlist_play",
            primary_action=lambda: _run_algorithm_demo(services),
            secondary_label="Open Lab",
            secondary_target="/algorithm-test-lab",
            accent="#10B981",
        )
        _track_card(
            title="Generic API Lab",
            badge="HTTP + Dry-run",
            caption="Valide APIs, webhooks e contratos como WhatsApp antes de conectar no SaaS real.",
            primary_label="Run Contract Dry-run",
            primary_icon="api",
            primary_action=lambda: _run_api_contract_dry_run(services),
            secondary_label="Open API Lab",
            secondary_target="/api-test-lab",
            accent="#00D4FF",
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
        _track_card(
            title="Token Calculator",
            badge="Cost Control",
            caption="Projete custo por usuário e compare prompt cru contra contexto técnico compacto.",
            primary_label="Open Calculator",
            primary_icon="calculate",
            primary_action=lambda: ui.navigate.to("/token-calculator"),
            secondary_label="Context Builder",
            secondary_target="/context-builder",
            accent="#F59E0B",
        )

    with ui.column().classes("afk-card w-full gap-4").style("padding:18px;"):
        with ui.row().classes("w-full items-center justify-between gap-4"):
            with ui.column().classes("gap-1"):
                ui.label("Official Validation Journey").classes("text-xl font-bold afk-title")
                ui.label("Siga estes 8 passos para sair de teste validado para contexto pronto para IA.").classes("afk-muted")
            ui.html("<span class='afk-badge' style='color:#00D4FF'>Evidence-first</span>")
        with ui.grid(columns=4).classes("w-full gap-3"):
            for step in journey_steps:
                _journey_card(services, step)
        with ui.row().classes("gap-3"):
            ui.button("Open Tutorial", icon="article", on_click=lambda: ui.navigate.to("/tutorial")).classes("afk-primary-btn")
            ui.button("Run Algorithm Suite", icon="playlist_play", on_click=lambda: _run_algorithm_demo(services)).classes("afk-primary-btn")
            ui.button("Run API Dry-run", icon="api", on_click=lambda: _run_api_contract_dry_run(services)).classes("afk-primary-btn")
            ui.button("Open Context Builder", icon="integration_instructions", on_click=lambda: ui.navigate.to("/context-builder")).classes("afk-ghost-btn")


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


def _journey_card(services, step: dict[str, object]) -> None:
    status = str(step.get("status") or "Pending")
    color = "#10B981" if status == "Ready" else "#F59E0B"
    with ui.column().classes("afk-card gap-3").style("padding:16px;min-height:260px;background:rgba(15,23,42,.58);"):
        with ui.row().classes("w-full items-center justify-between gap-2"):
            ui.html(f"<span class='afk-badge' style='color:#00D4FF'>STEP {int(step['number'])}</span>")
            ui.html(f"<span class='afk-badge' style='color:{color}'>{escape(status)}</span>")
        ui.label(str(step["title"])).classes("text-lg font-extrabold afk-title")
        ui.html(f"<span class='afk-badge' style='align-self:flex-start'>{escape(str(step['evidence_mode']))}</span>")
        ui.label(str(step["help"])).classes("afk-muted").style("font-size:13px;line-height:1.55;")
        ui.label(f"Evidência: {step['evidence']}").classes("afk-muted").style("font-size:12px;line-height:1.45;")
        ui.space()
        ui.button(
            str(step["cta_label"]),
            icon=_journey_icon(str(step["title"])),
            on_click=lambda title=str(step["title"]), route=str(step["route"]): _run_journey_action(services, title, route),
        ).classes("afk-ghost-btn")


def _journey_icon(title: str) -> str:
    icons = {
        "Abrir Tutorial": "article",
        "Rodar Algorithm Suite": "playlist_play",
        "Rodar API Contract Dry-run": "api",
        "Ver Dashboard": "monitor_heart",
        "Abrir Logs": "terminal",
        "Gerar Context Builder": "integration_instructions",
        "Baixar Evidence Pack": "inventory_2",
        "Usar contexto com IA": "psychology",
    }
    return icons.get(title, "arrow_forward")


def _run_journey_action(services, title: str, route: str) -> None:
    if title == "Rodar Algorithm Suite":
        _run_algorithm_demo(services)
        return
    if title == "Rodar API Contract Dry-run":
        _run_api_contract_dry_run(services)
        return
    ui.navigate.to(route)


def _run_algorithm_demo(services) -> None:
    status = database_status(services.engine)
    if not status["online"]:
        ui.notify("PostgreSQL offline. Rode npm run db antes da validação seed.", type="negative")
        return
    ensure_default_algorithms(services.algorithm_repository)
    definition = services.algorithm_repository.get_definition_by_name("lead_score")
    run = AlgorithmTestRunner(services.algorithm_repository).run_suite(str(definition["id"]))
    ui.notify(f"Seed validation: {run['passed']} passed / {run['failed']} failed.", type="positive" if run["failed"] == 0 else "warning")
    ui.navigate.to("/algorithm-test-lab")


def _run_api_contract_dry_run(services) -> None:
    status = database_status(services.engine)
    if not status["online"]:
        ui.notify("PostgreSQL offline. Rode npm run db antes do dry-run de API.", type="negative")
        return
    ensure_default_api_suites(services.api_test_repository)
    suite = services.api_test_repository.get_suite_by_name("whatsapp_validation_pack")
    run = ApiTestRunner(services.api_test_repository).run_suite(str(suite["id"]))
    ui.notify(
        f"API contract dry-run: {run['passed']} passed / {run['failed']} failed.",
        type="positive" if run["failed"] == 0 else "warning",
    )
    ui.navigate.to("/api-test-lab")


def _project_health_panel(health: dict[str, object]) -> None:
    database = health.get("database", {}) if isinstance(health.get("database"), dict) else {}
    xai = health.get("latest_xai_run", {}) if isinstance(health.get("latest_xai_run"), dict) else {}
    context = health.get("latest_context_export", {}) if isinstance(health.get("latest_context_export"), dict) else {}
    failed = health.get("failed_events", {}) if isinstance(health.get("failed_events"), dict) else {}
    readiness = health.get("readiness", {}) if isinstance(health.get("readiness"), dict) else {}
    modes = health.get("evidence_modes", {}) if isinstance(health.get("evidence_modes"), dict) else {}
    mode_text = ", ".join(f"{key}={value}" for key, value in sorted(modes.items())) or "none"
    with ui.column().classes("afk-card w-full gap-4").style("padding:18px;"):
        with ui.row().classes("w-full items-center justify-between gap-4"):
            with ui.column().classes("gap-1"):
                ui.label("Project Health").classes("text-xl font-bold afk-title")
                ui.label("Estado operacional do harness antes de gravar demo ou entregar contexto para IA.").classes("afk-muted")
            ui.html(f"<span class='afk-badge' style='color:{_health_color(str(readiness.get('status') or ''))}'>{escape(str(readiness.get('status') or 'Unknown'))}</span>")
        with ui.grid(columns=5).classes("w-full gap-3"):
            metric_card("PostgreSQL", str(database.get("status") or "Unknown"), f"{database.get('latency_ms', 0)} ms", "#00D4FF")
            metric_card("Latest xAI Run", str(xai.get("status") or "No runs"), str(xai.get("suite_name") or ""), "#2563EB")
            metric_card("Context Export", str(context.get("status") or "No exports"), f"{context.get('path_count', 0)} arquivos", "#10B981")
            metric_card("Failed Events", int(failed.get("count") or 0), "eventos failed", "#EF4444")
            metric_card("Evidence Modes", mode_text, "últimos eventos", "#F59E0B")
        missing = context.get("missing_paths") if isinstance(context.get("missing_paths"), list) else []
        if missing:
            ui.label("Context exports apontam para arquivos ausentes. Gere o Evidence Pack novamente antes de demo.").classes("afk-muted").style("color:#F59E0B;")


def _health_color(status: str) -> str:
    if status == "Ready":
        return "#10B981"
    if status == "Needs attention":
        return "#F59E0B"
    return "#EF4444"
