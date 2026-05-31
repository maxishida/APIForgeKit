from __future__ import annotations

from loguru import logger
from nicegui import ui

from core.config import get_settings
from core.database import build_engine, build_session_factory, database_status, init_db
from core.repositories import LeadTestRepository
from ui.app_shell import AppServices, render_shell, set_services
from ui.blueprint import render_blueprint
from ui.context_builder import render_context_builder
from ui.dashboard import render_dashboard
from ui.lead_lab import render_lead_lab
from ui.logs import render_logs
from ui.settings import render_settings
from ui.theme import apply_theme


settings = get_settings()
settings.log_path.parent.mkdir(parents=True, exist_ok=True)
settings.contexts_dir.mkdir(parents=True, exist_ok=True)
settings.blueprints_dir.mkdir(parents=True, exist_ok=True)

engine = build_engine(settings.database_url)
session_factory = build_session_factory(engine)
repository = LeadTestRepository(session_factory)

try:
    init_db(engine)
except Exception as exc:  # noqa: BLE001 - startup must degrade cleanly when PostgreSQL is offline
    logger.warning(f"Database initialization skipped: {exc}")

set_services(
    AppServices(
        engine=engine,
        repository=repository,
        log_path=settings.log_path,
        contexts_dir=settings.contexts_dir,
        blueprints_dir=settings.blueprints_dir,
    )
)


@ui.page("/")
def dashboard_page() -> None:
    apply_theme()
    render_shell(
        "Dashboard",
        "APIForgeKit Studio",
        "Observabilidade local para algoritmo de lead score",
        lambda: render_dashboard(_services()),
    )


@ui.page("/lead-lab")
def lead_lab_page() -> None:
    apply_theme()
    render_shell(
        "Lead Algorithm Lab",
        "Lead Algorithm Lab",
        "Execute o algoritmo determinístico e gere evidência estruturada",
        lambda: render_lead_lab(_services()),
    )


@ui.page("/logs")
def logs_page() -> None:
    apply_theme()
    render_shell("Logs", "Logs", "Histórico, busca, filtros e JSON completo", lambda: render_logs(_services()))


@ui.page("/context-builder")
def context_page() -> None:
    apply_theme()
    render_shell(
        "Context Builder",
        "Context Builder",
        "Transforme testes persistidos em contexto técnico para IA implementar",
        lambda: render_context_builder(_services()),
    )


@ui.page("/blueprint")
def blueprint_page() -> None:
    apply_theme()
    render_shell(
        "Next.js Blueprint",
        "Next.js Blueprint",
        "Estrutura futura com Prisma, API route e componentes de dashboard",
        lambda: render_blueprint(_services()),
    )


@ui.page("/settings")
def settings_page() -> None:
    apply_theme()
    render_shell("Settings", "Settings", "Status local e comandos operacionais", lambda: render_settings(_services()))


def _services() -> AppServices:
    from ui.app_shell import get_services

    return get_services()


if __name__ in {"__main__", "__mp_main__"}:
    current_status = database_status(engine)
    if current_status["online"]:
        logger.info(f"PostgreSQL online: {current_status['latency_ms']} ms")
    else:
        logger.warning("PostgreSQL offline. The UI will open in degraded mode.")
    ui.run(host=settings.app_host, port=settings.app_port, title="APIForgeKit Studio", dark=True, reload=False)
