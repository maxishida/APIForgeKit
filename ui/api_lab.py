from __future__ import annotations

import json

from nicegui import ui

from core.api_test_lab import ApiTestRunner, ensure_default_api_suites, export_api_suite
from core.database import database_status
from ui.components.alerts import db_offline, empty_state
from ui.components.cards import metric_card
from ui.components.charts import result_latency_bar, result_status_donut


def render_api_lab(services) -> None:
    status = database_status(services.engine)
    if not status["online"]:
        db_offline(str(status["error"]))
        empty_state("Generic API Lab aguardando PostgreSQL", "Suba o banco com npm run db para salvar contratos, requests e diffs.")
        return

    ensure_default_api_suites(services.api_test_repository)
    suites = services.api_test_repository.list_suites()
    if not suites:
        empty_state("Nenhuma suite de API", "Crie uma suite para validar endpoints ou contratos em dry-run.")
        return

    suite_by_name = {suite["name"]: suite for suite in suites}
    selected_suite = ui.select(list(suite_by_name), value=suites[0]["name"], label="Suite").classes("w-full")
    metrics_container = ui.grid(columns=4).classes("w-full gap-4")
    controls_container = ui.column().classes("afk-card w-full gap-4").style("padding:18px;")
    evidence_container = ui.grid(columns=2).classes("w-full gap-4")
    results_container = ui.column().classes("afk-card w-full gap-4").style("padding:18px;")
    editor_container = ui.column().classes("afk-card w-full gap-4").style("padding:18px;")

    def selected() -> dict[str, object]:
        return suite_by_name[str(selected_suite.value)]

    def refresh_metrics() -> None:
        metrics = services.api_test_repository.metrics()
        metrics_container.clear()
        with metrics_container:
            metric_card("API Runs", metrics["total_runs"], "Suites executadas", "#00D4FF")
            metric_card("API Results", metrics["total_results"], "Casos validados", "#2563EB")
            metric_card("Passed", metrics["passed"], f"{metrics['pass_rate']}% aprovação", "#10B981")
            metric_card("Avg Latency", f"{metrics['average_latency_ms']} ms", "Dry-run ou HTTP real", "#F59E0B")

    def render_controls() -> None:
        suite = selected()
        controls_container.clear()
        with controls_container:
            with ui.row().classes("w-full items-center justify-between gap-4"):
                with ui.column().classes("gap-1"):
                    ui.label("Generic API Test Lab").classes("text-xl font-bold afk-title")
                    ui.label("Teste endpoints reais ou contratos dry-run antes de implementar integrações.").classes("afk-muted")
                ui.html(f"<span class='afk-badge'>{suite['provider']}</span>")
            ui.label(str(suite["description"])).classes("afk-muted")
            with ui.row().classes("gap-3"):
                ui.button("Executar Suite", icon="playlist_play", on_click=lambda: run_suite(suite)).classes("afk-primary-btn")
                ui.button("Exportar Suite JSON", icon="download", on_click=lambda: export_suite(suite)).classes("afk-ghost-btn")
                ui.button("Atualizar", icon="refresh", on_click=lambda: refresh_all()).classes("afk-ghost-btn")

    def render_editor() -> None:
        suite = selected()
        cases = services.api_test_repository.list_cases(str(suite["id"]))
        first = cases[0] if cases else None
        case_options = {case["name"]: case for case in cases}
        editor_container.clear()
        with editor_container:
            ui.label("Criar caso de API").classes("text-xl font-bold afk-title")
            ui.label("Use dry-run para validar payload/contrato, ou desmarque para chamar HTTP real.").classes("afk-muted")
            selected_case = ui.select(list(case_options), value=first["name"] if first else None, label="Caso salvo").classes("w-full")
            case_name = ui.input("Nome", value=first["name"] if first else "novo caso").classes("w-full")
            method = ui.select(["GET", "POST", "PUT", "PATCH", "DELETE"], value=first["method"] if first else "POST", label="Método").classes("w-full")
            url = ui.input("URL", value=first["url"] if first else "dry-run://demo").classes("w-full")
            dry_run = ui.checkbox("Dry-run / contrato local", value=bool(first["dry_run"]) if first else True).classes("w-full")
            headers = ui.textarea("Headers JSON", value=json.dumps(first["headers"] if first else {}, ensure_ascii=False, indent=2)).classes("w-full")
            body = ui.textarea("Body JSON", value=json.dumps(first["body"] if first else {}, ensure_ascii=False, indent=2)).classes("w-full")
            expected = ui.textarea("Expected JSON", value=json.dumps(first["expected"] if first else {"status_code": 200}, ensure_ascii=False, indent=2)).classes("w-full")
            mock = ui.textarea(
                "Mock response JSON",
                value=json.dumps(first["mock_response"] if first else {"status_code": 200, "json": {"ok": True}}, ensure_ascii=False, indent=2),
            ).classes("w-full")

            def load_case() -> None:
                if not selected_case.value:
                    return
                case = case_options[str(selected_case.value)]
                case_name.value = str(case["name"])
                method.value = str(case["method"])
                url.value = str(case["url"])
                dry_run.value = bool(case["dry_run"])
                headers.value = json.dumps(case["headers"], ensure_ascii=False, indent=2)
                body.value = json.dumps(case["body"], ensure_ascii=False, indent=2)
                expected.value = json.dumps(case["expected"], ensure_ascii=False, indent=2)
                mock.value = json.dumps(case["mock_response"], ensure_ascii=False, indent=2)

            selected_case.on_value_change(lambda _: load_case())
            with ui.row().classes("gap-3"):
                ui.button(
                    "Salvar caso",
                    icon="save",
                    on_click=lambda: save_case(suite, case_name.value, method.value, url.value, headers.value, body.value, expected.value, dry_run.value, mock.value),
                ).classes("afk-ghost-btn")
                ui.button("Executar caso", icon="play_arrow", on_click=lambda: run_single(selected_case.value, case_options)).classes("afk-primary-btn")

    def render_results() -> None:
        results = services.api_test_repository.list_results(limit=100)
        evidence_container.clear()
        with evidence_container:
            with ui.column().classes("afk-card").style("padding:12px;"):
                ui.plotly(result_status_donut(results, "API Contract Pass/Fail")).classes("w-full")
            with ui.column().classes("afk-card").style("padding:12px;"):
                ui.plotly(result_latency_bar(results, title="Latência por API Test")).classes("w-full")
        results_container.clear()
        with results_container:
            ui.label("Resultados, diff e JSON estruturado").classes("text-xl font-bold afk-title")
            if not results:
                ui.label("Nenhuma execução ainda. Rode a suite WhatsApp para gerar evidências.").classes("afk-muted")
                return
            rows = [
                {
                    "created_at": result["created_at"],
                    "status": result["status"],
                    "test": result["structured_log"].get("test_name", result["case_id"]),
                    "provider": result["structured_log"].get("provider"),
                    "status_code": result["response"].get("status_code"),
                    "latency_ms": result["latency_ms"],
                }
                for result in results
            ]
            ui.aggrid(
                {
                    "columnDefs": [
                        {"field": "created_at", "headerName": "Timestamp", "sortable": True, "filter": True, "minWidth": 180},
                        {"field": "status", "headerName": "Status", "sortable": True, "filter": True, "width": 120},
                        {"field": "provider", "headerName": "Provider", "sortable": True, "filter": True, "width": 130},
                        {"field": "test", "headerName": "Test", "sortable": True, "filter": True, "flex": 1},
                        {"field": "status_code", "headerName": "HTTP", "sortable": True, "filter": "agNumberColumnFilter", "width": 110},
                        {"field": "latency_ms", "headerName": "Latency", "sortable": True, "filter": "agNumberColumnFilter", "width": 120},
                    ],
                    "rowData": rows,
                    "pagination": True,
                    "paginationPageSize": 10,
                    "defaultColDef": {"resizable": True},
                },
                theme="quartz-dark",
            ).classes("w-full").style("height:340px")
            options = {f"{result['structured_log'].get('test_name')} | {result['created_at']}": result for result in results}
            selected_result = ui.select(list(options), value=list(options)[0], label="Abrir JSON").classes("w-full")
            code = ui.code(json.dumps(options[selected_result.value]["structured_log"], ensure_ascii=False, indent=2), language="json").classes("w-full")

            def update_code() -> None:
                code.set_content(json.dumps(options[selected_result.value]["structured_log"], ensure_ascii=False, indent=2))

            selected_result.on_value_change(lambda _: update_code())

    def save_case(suite: dict[str, object], name: str, method: str, url: str, headers: str, body: str, expected: str, dry: bool, mock: str) -> None:
        try:
            services.api_test_repository.create_case(
                suite_id=str(suite["id"]),
                name=name or "caso sem nome",
                method=method,
                url=url,
                headers=json.loads(headers or "{}"),
                body=json.loads(body or "{}"),
                expected=json.loads(expected or "{}"),
                dry_run=bool(dry),
                mock_response=json.loads(mock or "{}"),
                tags=["manual"],
            )
            ui.notify("Caso salvo.", type="positive")
            refresh_all()
        except Exception as exc:  # noqa: BLE001
            ui.notify(f"Erro ao salvar: {exc}", type="negative")

    def run_single(label: str | None, cases: dict[str, dict[str, object]]) -> None:
        if not label:
            ui.notify("Selecione um caso.", type="warning")
            return
        try:
            run = ApiTestRunner(services.api_test_repository).run_single_case(str(cases[str(label)]["id"]))
            ui.notify(f"Caso concluído: {run['status']}", type="positive" if run["status"] == "passed" else "warning")
            refresh_all()
        except Exception as exc:  # noqa: BLE001
            ui.notify(f"Erro ao executar: {exc}", type="negative")

    def run_suite(suite: dict[str, object]) -> None:
        try:
            run = ApiTestRunner(services.api_test_repository).run_suite(str(suite["id"]))
            ui.notify(f"Suite: {run['passed']} passed / {run['failed']} failed.", type="positive" if run["failed"] == 0 else "warning")
            refresh_all()
        except Exception as exc:  # noqa: BLE001
            ui.notify(f"Erro ao executar suite: {exc}", type="negative")

    def export_suite(suite: dict[str, object]) -> None:
        path = export_api_suite(services.api_test_repository, str(suite["id"]), services.reports_dir)
        ui.notify(f"Suite exportada: {path}", type="positive")

    def refresh_all() -> None:
        refresh_metrics()
        render_controls()
        render_editor()
        render_results()

    selected_suite.on_value_change(lambda _: refresh_all())
    refresh_all()
