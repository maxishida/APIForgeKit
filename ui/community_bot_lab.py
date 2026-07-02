from __future__ import annotations

import json
from html import escape
from pathlib import Path

from nicegui import ui

from core.algorithm_test_lab import (
    AlgorithmTestRunner,
    build_algorithm_context,
    ensure_default_algorithms,
    export_algorithm_suite,
    run_algorithm,
    summarize_algorithm_invariants,
)
from core.community_bot_seed import DEFAULT_COMMUNITY_BOT_CASES, _BASE_RULES, _DEFAULT_TEMPLATES
from core.database import database_status
from core.report_bundle import create_report_bundle
from ui.components.alerts import db_offline, empty_state
from ui.components.badges import evidence_badge
from ui.components.cards import metric_card


SCENARIO_OPTIONS = {case["name"]: case for case in DEFAULT_COMMUNITY_BOT_CASES}

EVENT_PRESETS = [
    "user.first_login",
    "post.first_created",
    "theory.first_created",
    "credits.low",
    "user.inactive_3_days",
    "theory.trending",
]


def _default_sandbox_payload(event_name: str = "user.first_login", simulate: bool = True) -> dict[str, object]:
    return {
        "event": {
            "user_id": "user_sandbox",
            "event_name": event_name,
            "entity_type": "user",
            "entity_id": "user_sandbox",
            "metadata_json": {"page": "/dashboard"},
            "source": "community_bot_lab",
            "simulate": simulate,
        },
        "user": {
            "user_id": "user_sandbox",
            "username": "VicePlayer",
            "profileCompleted": False,
            "hasReceivedWelcome": False,
            "hasActiveMission": False,
            "credits": 0,
            "badges": [],
            "level": 1,
            "ranking_points": 0,
        },
        "rules": _BASE_RULES,
        "history": [],
        "templates": _DEFAULT_TEMPLATES,
    }


def render_community_bot_lab(services) -> None:
    status = database_status(services.engine)
    if not status["online"]:
        db_offline(str(status["error"]))
        empty_state("Community Bot Lab aguardando PostgreSQL", "Execute npm run db antes de testar.")
        return

    ensure_default_algorithms(services.algorithm_repository)
    try:
        definition = services.algorithm_repository.get_definition_by_name("community_bot_engine")
    except ValueError:
        empty_state("Algoritmo não encontrado", "Rode ensure_default_algorithms ou reinicie o Studio.")
        return

    metrics_row = ui.grid(columns=4).classes("w-full gap-4")
    playground = ui.column().classes("afk-card w-full gap-4").style("padding:18px;")
    output_panel = ui.column().classes("afk-card w-full gap-4").style("padding:18px;")
    suite_panel = ui.column().classes("afk-card w-full gap-4").style("padding:18px;")

    def refresh_metrics() -> None:
        results = services.algorithm_repository.list_results(algorithm_id=str(definition["id"]), limit=100)
        passed = sum(1 for item in results if item["status"] == "passed")
        failed = sum(1 for item in results if item["status"] == "failed")
        invariants = summarize_algorithm_invariants(results)
        metrics_row.clear()
        with metrics_row:
            metric_card("Casos seed", len(DEFAULT_COMMUNITY_BOT_CASES), "Fluxos MVP documentados", "#00D4FF")
            metric_card("Passed", passed, "Execuções aprovadas", "#10B981")
            metric_card("Failed", failed, "Divergências", "#EF4444")
            ready = invariants.get("all_passed") and failed == 0 and passed >= len(DEFAULT_COMMUNITY_BOT_CASES)
            metric_card("Readiness", "Ready" if ready else "Needs tests", "Contexto para implementação", "#8B5CF6")

    def render_playground() -> None:
        playground.clear()
        with playground:
            with ui.row().classes("w-full items-center justify-between gap-4"):
                with ui.column().classes("gap-1"):
                    ui.label("Sandbox — Vice City NPC Engine").classes("text-xl font-bold afk-title")
                    ui.label("Simule eventos, regras e ações sem IA. Modo teste não persiste efeitos reais.").classes("afk-muted")
                with ui.row().classes("gap-2"):
                    evidence_badge("seed_validation")
                    ui.html("<span class='afk-badge'>BOT OFICIAL</span>")

            scenario = ui.select(list(SCENARIO_OPTIONS), label="Cenário MVP pré-carregado").classes("w-full")
            event_name = ui.select(EVENT_PRESETS, value="user.first_login", label="Evento gatilho").classes("w-full")
            simulate_toggle = ui.switch("Modo simulador admin (dry-run)", value=True)
            payload_area = ui.textarea(
                "Payload JSON (event + user + rules + history + templates)",
                value=json.dumps(_default_sandbox_payload(), ensure_ascii=False, indent=2),
            ).classes("w-full").style("min-height:320px;font-family:monospace;")

            def load_scenario() -> None:
                if not scenario.value:
                    return
                case = SCENARIO_OPTIONS[str(scenario.value)]
                payload_area.value = json.dumps(case["input_payload"], ensure_ascii=False, indent=2)
                event_name.value = str((case["input_payload"].get("event") or {}).get("event_name", "user.first_login"))

            def load_event_preset() -> None:
                payload_area.value = json.dumps(
                    _default_sandbox_payload(str(event_name.value), bool(simulate_toggle.value)),
                    ensure_ascii=False,
                    indent=2,
                )

            scenario.on_value_change(lambda _: load_scenario())
            event_name.on_value_change(lambda _: load_event_preset())
            simulate_toggle.on_value_change(lambda _: load_event_preset())

            with ui.row().classes("gap-3 flex-wrap"):
                ui.button("Executar sandbox", icon="play_circle", on_click=lambda: run_sandbox(payload_area, output_panel)).classes(
                    "afk-primary-btn"
                )
                ui.button("Rodar suíte 15/15", icon="verified", on_click=lambda: run_full_suite()).classes("afk-primary-btn")
                ui.button("Export Evidence Pack", icon="inventory_2", on_click=lambda: export_pack()).classes("afk-ghost-btn")
                ui.button("Abrir Algorithm Lab", icon="science", on_click=lambda: ui.navigate.to("/algorithm-test-lab")).classes("afk-ghost-btn")
                ui.button("Context Builder", icon="integration_instructions", on_click=lambda: ui.navigate.to("/context-builder")).classes(
                    "afk-ghost-btn"
                )

    def run_sandbox(payload_area, panel) -> None:
        try:
            payload = json.loads(payload_area.value or "{}")
            result = run_algorithm("community_bot_engine", payload)
            _render_output(panel, result, title="Resultado do sandbox")
            ui.notify(
                f"Sandbox: {result.get('classification')} — {result.get('rules_matched')} regra(s) executada(s)",
                type="positive" if result.get("classification") == "success" else "warning",
            )
        except Exception as exc:  # noqa: BLE001
            ui.notify(f"Erro no sandbox: {exc}", type="negative")

    def run_full_suite() -> None:
        try:
            runner = AlgorithmTestRunner(services.algorithm_repository)
            run = runner.run_suite(str(definition["id"]))
            refresh_metrics()
            render_suite_results()
            ui.notify(
                f"Suíte: {run['passed']} passed / {run['failed']} failed",
                type="positive" if run["failed"] == 0 else "negative",
            )
        except Exception as exc:  # noqa: BLE001
            ui.notify(f"Erro na suíte: {exc}", type="negative")

    def export_pack() -> None:
        try:
            context = build_algorithm_context(services.algorithm_repository, algorithm_name="community_bot_engine")
            results = services.algorithm_repository.list_results(algorithm_id=str(definition["id"]), limit=100)
            bundle = create_report_bundle(
                output_dir=services.reports_dir,
                name="community_bot_engine_ui_evidence_pack",
                markdown=context,
                payload={
                    "source": "community_bot_lab_ui",
                    "algorithm": "community_bot_engine",
                    "invariants": summarize_algorithm_invariants(results),
                },
            )
            export_algorithm_suite(services.algorithm_repository, str(definition["id"]), services.reports_dir)
            ui.notify(f"Evidence pack: {bundle['zip']}", type="positive")
        except Exception as exc:  # noqa: BLE001
            ui.notify(f"Erro ao exportar: {exc}", type="negative")

    def render_suite_results() -> None:
        results = services.algorithm_repository.list_results(algorithm_id=str(definition["id"]), limit=30)
        suite_panel.clear()
        with suite_panel:
            ui.label("Últimos resultados da suíte").classes("text-xl font-bold afk-title")
            if not results:
                ui.label("Nenhum resultado ainda. Clique em Rodar suíte 15/15.").classes("afk-muted")
                return
            rows = [
                {
                    "case": item["structured_log"].get("case_name", item["case_id"]),
                    "status": item["status"],
                    "classification": (item.get("actual_output") or {}).get("classification"),
                    "rules": (item.get("actual_output") or {}).get("rules_matched"),
                    "latency_ms": item["latency_ms"],
                }
                for item in results[:15]
            ]
            ui.aggrid(
                {
                    "columnDefs": [
                        {"field": "case", "headerName": "Caso", "flex": 1},
                        {"field": "status", "headerName": "Status", "width": 110},
                        {"field": "classification", "headerName": "Class", "width": 120},
                        {"field": "rules", "headerName": "Rules", "width": 90},
                        {"field": "latency_ms", "headerName": "ms", "width": 90},
                    ],
                    "rowData": rows,
                    "pagination": True,
                    "paginationPageSize": 10,
                },
                theme="quartz-dark",
            ).classes("w-full").style("height:280px")

    def download_report_file(filename: str) -> None:
        path = Path(services.reports_dir) / filename
        if not path.exists():
            ui.notify(f"Arquivo não encontrado: {filename}", type="negative")
            return
        media = "application/json" if path.suffix == ".json" else "text/markdown"
        ui.download.content(path.read_text(encoding="utf-8"), filename, media_type=media)

    def render_docs_card() -> None:
        reports = [
            "CODE_GTA6_COMMUNITY_BOT_ENGINE_IMPLEMENTATION_CONTEXT.md",
            "community_bot_engine_context.md",
            "community_bot_engine.json",
        ]
        with ui.column().classes("afk-card w-full gap-2").style("padding:18px;"):
            ui.label("Documentação para implementação").classes("text-xl font-bold afk-title")
            with ui.row().classes("gap-3 flex-wrap"):
                for name in reports:
                    path = Path(services.reports_dir) / name
                    if not path.exists():
                        continue
                    ui.link(name, f"/download/reports/{name}", new_tab=True).classes("afk-neon")
                    ui.button(icon="download", on_click=lambda n=name: download_report_file(n)).props("flat round dense")
            ui.markdown(
                """
**Pipeline validado:** User Action → Event → Rules Engine → Conditions → Actions → Logs

**Bots:** ViceBot, MissionBot, TheoryBot, NewsBot, ModBot, VIPBot (tag `BOT OFICIAL`)

**URL desta página:** `/community-bot-lab`
                """
            ).classes("afk-muted")

    render_playground()
    _render_output(output_panel, None, title="Saída do motor de regras")
    render_suite_results()
    refresh_metrics()
    render_docs_card()


def _render_output(panel, result: dict[str, object] | None, title: str) -> None:
    panel.clear()
    with panel:
        ui.label(title).classes("text-xl font-bold afk-title")
        if result is None:
            ui.label("Execute o sandbox ou a suíte para ver ações, logs e classificação.").classes("afk-muted")
            return

        classification = str(result.get("classification", ""))
        color = {"success": "#10B981", "partial": "#F59E0B", "blocked": "#EF4444", "invalid": "#EF4444"}.get(
            classification, "#9CA3AF"
        )
        with ui.row().classes("gap-3 flex-wrap"):
            ui.html(f"<span class='afk-badge' style='color:{color}'>classification: {escape(classification)}</span>")
            ui.html(f"<span class='afk-badge'>rules_matched: {result.get('rules_matched', 0)}</span>")
            ui.html(f"<span class='afk-badge'>actions: {len(result.get('actions_executed') or [])}</span>")
            ui.html(f"<span class='afk-badge'>skipped: {len(result.get('actions_skipped') or [])}</span>")

        sections = {
            "Actions Executed": result.get("actions_executed"),
            "Actions Skipped": result.get("actions_skipped"),
            "Bot Logs": result.get("bot_logs"),
            "User Updates": result.get("user_updates"),
            "Reasons": result.get("reasons"),
            "Full JSON": result,
        }
        with ui.tabs().classes("w-full") as tabs:
            tab_map = {name: ui.tab(name) for name in sections}
        with ui.tab_panels(tabs, value=tab_map["Actions Executed"]).classes("w-full"):
            for name, payload in sections.items():
                with ui.tab_panel(tab_map[name]):
                    ui.code(json.dumps(payload, ensure_ascii=False, indent=2), language="json").classes("w-full")