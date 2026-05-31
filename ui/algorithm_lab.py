from __future__ import annotations

import json
from html import escape

from nicegui import ui

from core.algorithm_test_lab import AlgorithmTestRunner, ensure_default_algorithms
from core.database import database_status
from ui.components.alerts import db_offline, empty_state
from ui.components.cards import metric_card


def render_algorithm_lab(services) -> None:
    status = database_status(services.engine)
    if not status["online"]:
        db_offline(str(status["error"]))
        empty_state("Algorithm Test Lab aguardando PostgreSQL", "Suba o banco com npm run db para salvar casos e resultados.")
        return

    ensure_default_algorithms(services.algorithm_repository)
    definitions = services.algorithm_repository.list_definitions()
    if not definitions:
        empty_state("Nenhum algoritmo cadastrado", "Cadastre um algoritmo antes de criar casos.")
        return

    definition_by_label = {definition["name"]: definition for definition in definitions}
    selected_algorithm = ui.select(list(definition_by_label), value=definitions[0]["name"], label="Selecionar algoritmo").classes("w-full")

    metrics_container = ui.grid(columns=4).classes("w-full gap-4")
    editor_container = ui.column().classes("afk-card w-full gap-4").style("padding:18px;")
    results_container = ui.column().classes("afk-card w-full gap-4").style("padding:18px;")
    context_container = ui.column().classes("afk-card w-full gap-4").style("padding:18px;")

    def selected_definition() -> dict[str, object]:
        return definition_by_label[str(selected_algorithm.value)]

    def refresh_metrics() -> None:
        metrics = services.algorithm_repository.metrics()
        metrics_container.clear()
        with metrics_container:
            metric_card("Runs", metrics["total_runs"], "Execuções de algoritmo", "#00D4FF")
            metric_card("Resultados", metrics["total_results"], "Casos executados", "#2563EB")
            metric_card("Passed", metrics["passed"], f"{metrics['pass_rate']}% aprovação", "#10B981")
            metric_card("Failed", metrics["failed"], "Casos divergentes", "#EF4444")

    def render_editor() -> None:
        definition = selected_definition()
        cases = services.algorithm_repository.list_cases(str(definition["id"]))
        case_options = {case["name"]: case for case in cases}
        first_case = cases[0] if cases else None

        editor_container.clear()
        with editor_container:
            with ui.row().classes("w-full items-center justify-between gap-4"):
                with ui.column().classes("gap-1"):
                    ui.label("Criar e executar caso").classes("text-xl font-bold afk-title")
                    ui.label("Defina input JSON, resultado esperado e compare com o algoritmo puro.").classes("afk-muted")
                ui.html("<span class='afk-badge'>Sem LLM</span>")

            case_name = ui.input("Nome do caso", value=first_case["name"] if first_case else "novo caso").classes("w-full")
            selected_case = ui.select(list(case_options), value=first_case["name"] if first_case else None, label="Caso salvo").classes("w-full")
            input_json = ui.textarea(
                "Input JSON",
                value=json.dumps(first_case["input_payload"] if first_case else {}, ensure_ascii=False, indent=2),
            ).classes("w-full")
            expected_json = ui.textarea(
                "Resultado esperado JSON",
                value=json.dumps(first_case["expected_output"] if first_case else {}, ensure_ascii=False, indent=2),
            ).classes("w-full")

            def load_case() -> None:
                if not selected_case.value:
                    return
                case = case_options[str(selected_case.value)]
                case_name.value = str(case["name"])
                input_json.value = json.dumps(case["input_payload"], ensure_ascii=False, indent=2)
                expected_json.value = json.dumps(case["expected_output"], ensure_ascii=False, indent=2)

            selected_case.on_value_change(lambda _: load_case())

            with ui.row().classes("gap-3"):
                ui.button("Salvar caso", icon="save", on_click=lambda: save_case(definition, case_name.value, input_json.value, expected_json.value)).classes(
                    "afk-ghost-btn"
                )
                ui.button("Executar teste único", icon="play_arrow", on_click=lambda: run_single(selected_case.value, case_options)).classes(
                    "afk-primary-btn"
                )
                ui.button("Run Demo Suite", icon="playlist_play", on_click=lambda: run_suite(definition)).classes("afk-primary-btn")
                ui.button("Generate AI Context", icon="integration_instructions", on_click=lambda: ui.navigate.to("/context-builder")).classes("afk-ghost-btn")
                ui.button("Atualizar", icon="refresh", on_click=lambda: ui.navigate.reload()).classes("afk-ghost-btn")

    def render_results() -> None:
        results = services.algorithm_repository.list_results(limit=100)
        results_container.clear()
        with results_container:
            ui.label("Resultados e diff").classes("text-xl font-bold afk-title")
            if not results:
                ui.label("Nenhum teste de algoritmo executado ainda.").classes("afk-muted")
                return
            row_data = [
                {
                    "created_at": result["created_at"],
                    "status": result["status"],
                    "case": result["structured_log"].get("case_name", result["case_id"]),
                    "classification": result["actual_output"].get("classification"),
                    "score": result["actual_output"].get("score"),
                    "latency_ms": result["latency_ms"],
                }
                for result in results
            ]
            ui.aggrid(
                {
                    "columnDefs": [
                        {"field": "created_at", "headerName": "Timestamp", "sortable": True, "filter": True, "minWidth": 180},
                        {"field": "status", "headerName": "Status", "sortable": True, "filter": True, "width": 120},
                        {"field": "case", "headerName": "Case", "sortable": True, "filter": True, "flex": 1},
                        {"field": "classification", "headerName": "Classification", "sortable": True, "filter": True, "width": 160},
                        {"field": "score", "headerName": "Score", "sortable": True, "filter": "agNumberColumnFilter", "width": 110},
                        {"field": "latency_ms", "headerName": "Latency", "sortable": True, "filter": "agNumberColumnFilter", "width": 120},
                    ],
                    "rowData": row_data,
                    "pagination": True,
                    "paginationPageSize": 12,
                    "defaultColDef": {"resizable": True},
                },
                theme="quartz-dark",
            ).classes("w-full").style("height:360px")

            options = {f"{result['structured_log'].get('case_name', result['case_id'])} | {result['created_at']}": result for result in results}
            selected = ui.select(list(options), value=list(options)[0], label="Abrir diff / JSON estruturado").classes("w-full")
            code = ui.code(json.dumps(options[selected.value]["structured_log"], ensure_ascii=False, indent=2), language="json").classes("w-full")

            def update_code() -> None:
                code.set_content(json.dumps(options[selected.value]["structured_log"], ensure_ascii=False, indent=2))

            selected.on_value_change(lambda _: update_code())

    def render_context() -> None:
        from core.algorithm_test_lab import build_algorithm_context

        context_container.clear()
        with context_container:
            ui.label("Contexto técnico para IA").classes("text-xl font-bold afk-title")
            ui.markdown(build_algorithm_context(services.algorithm_repository)).classes("w-full")

    def save_case(definition: dict[str, object], name: str, input_value: str, expected_value: str) -> None:
        try:
            payload = json.loads(input_value or "{}")
            expected = json.loads(expected_value or "{}")
            services.algorithm_repository.create_case(
                algorithm_id=str(definition["id"]),
                name=name or "caso sem nome",
                input_payload=payload,
                expected_output=expected,
                tags=["manual"],
            )
            ui.notify("Caso salvo no PostgreSQL.", type="positive")
            render_editor()
        except Exception as exc:  # noqa: BLE001 - user-facing validation
            ui.notify(f"Erro ao salvar caso: {exc}", type="negative")

    def run_single(case_label: str | None, case_options: dict[str, dict[str, object]]) -> None:
        if not case_label:
            ui.notify("Selecione um caso salvo para executar.", type="warning")
            return
        try:
            runner = AlgorithmTestRunner(services.algorithm_repository)
            runner.run_single_case(str(case_options[str(case_label)]["id"]))
            ui.notify("Teste único executado.", type="positive")
            refresh_all()
        except Exception as exc:  # noqa: BLE001
            ui.notify(f"Erro ao executar teste: {exc}", type="negative")

    def run_suite(definition: dict[str, object]) -> None:
        try:
            runner = AlgorithmTestRunner(services.algorithm_repository)
            run = runner.run_suite(str(definition["id"]))
            ui.notify(f"Suite concluída: {run['passed']} passed / {run['failed']} failed.", type="positive" if run["failed"] == 0 else "warning")
            refresh_all()
        except Exception as exc:  # noqa: BLE001
            ui.notify(f"Erro ao executar suite: {exc}", type="negative")

    def refresh_all() -> None:
        refresh_metrics()
        render_results()
        render_context()

    selected_algorithm.on_value_change(lambda _: (render_editor(), refresh_all()))
    render_editor()
    refresh_all()

    with ui.column().classes("afk-card w-full gap-2").style("padding:18px;"):
        ui.label("Contrato de saída").classes("text-xl font-bold afk-title")
        ui.html(
            "<p class='afk-muted'>Cada execução salva input, expected, actual, diff, status, latência, recomendação e impacto Next.js em <code>algorithm_test_results</code>.</p>"
        )
        ui.html(f"<pre style='white-space:pre-wrap;color:#9CA3AF'>{escape(json.dumps(selected_definition()['output_schema'], ensure_ascii=False, indent=2))}</pre>")
