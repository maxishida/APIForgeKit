from __future__ import annotations

from loguru import logger
from nicegui import ui

from core.acp_audit import AcpAuditRepository
from core.algorithm_test_lab import AlgorithmTestRepository, ensure_default_algorithms
from core.api_test_lab import ApiTestRepository, ensure_default_api_suites
from core.config import get_settings
from core.database import build_engine, build_session_factory, database_status, init_db
from core.observability import ObservabilityRepository
from core.repositories import LeadTestRepository
from core.token_usage import TokenUsageRepository
from ui.app_shell import AppServices, render_shell, set_services
from ui.api_lab import render_api_lab
from ui.algorithm_lab import render_algorithm_lab
from ui.blueprint import render_blueprint
from ui.context_builder import render_context_builder
from ui.home import render_home
from ui.lead_lab import render_lead_lab
from ui.live_dashboard import render_live_dashboard
from ui.logs import render_logs
from ui.settings import render_settings
from ui.theme import apply_theme
from ui.token_calculator import render_token_calculator
from ui.tutorial import render_tutorial


settings = get_settings()
settings.log_path.parent.mkdir(parents=True, exist_ok=True)
settings.contexts_dir.mkdir(parents=True, exist_ok=True)
settings.blueprints_dir.mkdir(parents=True, exist_ok=True)
settings.reports_dir.mkdir(parents=True, exist_ok=True)

engine = build_engine(settings.database_url)
session_factory = build_session_factory(engine)
repository = LeadTestRepository(session_factory)
observability_repository = ObservabilityRepository(session_factory)
algorithm_repository = AlgorithmTestRepository(session_factory)
api_test_repository = ApiTestRepository(session_factory)
token_usage_repository = TokenUsageRepository(session_factory)
acp_audit_repository = AcpAuditRepository(session_factory)

try:
    init_db(engine)
    ensure_default_algorithms(algorithm_repository)
    ensure_default_api_suites(api_test_repository)
except Exception as exc:  # noqa: BLE001 - startup must degrade cleanly when PostgreSQL is offline
    logger.warning(f"Database initialization skipped: {exc}")

set_services(
    AppServices(
        engine=engine,
        session_factory=session_factory,
        repository=repository,
        observability_repository=observability_repository,
        algorithm_repository=algorithm_repository,
        api_test_repository=api_test_repository,
        token_usage_repository=token_usage_repository,
        acp_audit_repository=acp_audit_repository,
        log_path=settings.log_path,
        contexts_dir=settings.contexts_dir,
        blueprints_dir=settings.blueprints_dir,
        reports_dir=settings.reports_dir,
    )
)


@ui.page("/")
def dashboard_page() -> None:
    apply_theme()
    render_shell(
        "Home",
        "APIForgeKit Test Lab",
        "Teste APIs e algoritmos antes de gastar tokens implementando no escuro",
        lambda: render_home(_services()),
    )


@ui.page("/live-dashboard")
def live_dashboard_page() -> None:
    apply_theme()
    render_shell(
        "API Provider Lab",
        "API Provider Lab",
        "Observabilidade local para validação real de APIs de IA",
        lambda: render_live_dashboard(_services()),
    )


@ui.page("/api-test-lab")
def api_test_lab_page() -> None:
    apply_theme()
    render_shell(
        "Generic API Lab",
        "Generic API Lab",
        "Valide endpoints, webhooks e contratos dry-run com logs estruturados",
        lambda: render_api_lab(_services()),
    )


@ui.page("/lead-lab")
def lead_lab_page() -> None:
    apply_theme()
    render_shell(
        "Legacy Lead Lab",
        "Legacy Lead Algorithm Lab",
        "Referência legada; use Algorithm Test Lab como caminho canônico",
        lambda: render_lead_lab(_services()),
    )


@ui.page("/algorithm-test-lab")
def algorithm_test_lab_page() -> None:
    apply_theme()
    render_shell(
        "Algorithm Test Lab",
        "Algorithm Test Lab",
        "Valide algoritmos determinísticos com esperado x recebido",
        lambda: render_algorithm_lab(_services()),
    )


@ui.page("/token-calculator")
def token_calculator_page() -> None:
    apply_theme()
    render_shell(
        "Token Calculator",
        "Token Calculator",
        "Calcule custo por usuário e economia de contexto com preços de docs oficiais",
        lambda: render_token_calculator(_services()),
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
        "Transforme logs reais em contexto técnico e evidências reutilizáveis",
        lambda: render_context_builder(_services()),
    )


@ui.page("/blueprint")
def blueprint_page() -> None:
    apply_theme()
    render_shell(
        "Blueprint Archive",
        "Legacy Blueprint Archive",
        "Referência futura preservada; o MVP atual é validação e contexto",
        lambda: render_blueprint(_services()),
    )


@ui.page("/settings")
def settings_page() -> None:
    apply_theme()
    render_shell("Settings", "Settings", "Status local e comandos operacionais", lambda: render_settings(_services()))


@ui.page("/tutorial")
def tutorial_page() -> None:
    apply_theme()
    render_shell(
        "Tutorial",
        "Open Source Tutorial",
        "Fluxo simples para economizar tokens de LLM com testes reais",
        render_tutorial,
    )


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
