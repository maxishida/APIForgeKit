from __future__ import annotations

import json
from html import escape

from nicegui import ui

from core.algorithm_test_lab import (
    AlgorithmTestRunner,
    build_algorithm_context,
    ensure_default_algorithms,
    export_algorithm_suite,
    import_algorithm_suite,
    summarize_algorithm_invariants,
)
from core.database import database_status
from core.report_bundle import create_report_bundle
from ui.components.alerts import db_offline, empty_state
from ui.components.badges import evidence_badge
from ui.components.cards import metric_card
from ui.components.charts import algorithm_score_distribution, result_latency_bar, result_status_donut


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
    evidence_container = ui.grid(columns=3).classes("w-full gap-4")
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
                with ui.row().classes("gap-2"):
                    evidence_badge("seed_validation")
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
            import_path = ui.input("Import suite JSON path", placeholder="exports/reports/lead_score.json").classes("w-full")

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
                ui.button("Run Canonical lead_score", icon="verified", on_click=run_canonical_lead_score).classes("afk-primary-btn")
                ui.button("Run Canonical Suite", icon="playlist_play", on_click=lambda: run_suite(definition)).classes("afk-primary-btn")
                ui.button("Export Evidence Pack", icon="inventory_2", on_click=lambda: export_evidence_pack(definition)).classes("afk-ghost-btn")
                ui.button("Export Suite JSON", icon="download", on_click=lambda: export_suite(definition)).classes("afk-ghost-btn")
                ui.button("Import Suite JSON", icon="upload_file", on_click=lambda: import_suite(import_path.value)).classes("afk-ghost-btn")
                ui.button("Open Context Builder", icon="integration_instructions", on_click=lambda: ui.navigate.to("/context-builder")).classes("afk-ghost-btn")
                ui.button("Atualizar", icon="refresh", on_click=lambda: ui.navigate.reload()).classes("afk-ghost-btn")

    def render_results() -> None:
        definition = selected_definition()
        results = services.algorithm_repository.list_results(algorithm_id=str(definition["id"]), limit=100)
        invariant_summary = summarize_algorithm_invariants(results)
        latest_run = [run for run in services.algorithm_repository.list_runs(limit=50) if run.get("algorithm_id") == definition["id"]][:1]
        evidence_container.clear()
        with evidence_container:
            with ui.column().classes("afk-card").style("padding:12px;"):
                ui.plotly(result_status_donut(results, "Algorithm Pass/Fail")).classes("w-full")
            with ui.column().classes("afk-card").style("padding:12px;"):
                ui.plotly(algorithm_score_distribution(results)).classes("w-full")
            with ui.column().classes("afk-card").style("padding:12px;"):
                ui.plotly(result_latency_bar(results, title="Latência por Caso")).classes("w-full")
        results_container.clear()
        with results_container:
            with ui.row().classes("w-full items-center justify-between gap-4"):
                ui.label("Resultados e diff").classes("text-xl font-bold afk-title")
                if latest_run and latest_run[0]["status"] == "passed" and invariant_summary["all_passed"]:
                    ui.html("<span class='afk-badge' style='color:#10B981'>Ready for implementation context</span>")
            with ui.row().classes("gap-2"):
                for label, key in [
                    ("Payload", "payload_validated"),
                    ("Deterministic", "deterministic"),
                    ("Score 0-100", "score_clamped"),
                    ("Invalid Override", "invalid_override_checked"),
                ]:
                    value = invariant_summary[key]
                    color = "#10B981" if invariant_summary["total"] and value == invariant_summary["total"] else "#F59E0B"
                    ui.html(f"<span class='afk-badge' style='color:{color}'>{label}: {value}/{invariant_summary['total']}</span>")
            if not results:
                ui.label("Nenhum teste de algoritmo executado ainda.").classes("afk-muted")
                return
            row_data = [
                {
                    "created_at": result["created_at"],
                    "run_id": result["run_id"],
                    "status": result["status"],
                    "case": result["structured_log"].get("case_name", result["case_id"]),
                    "classification": result["actual_output"].get("classification"),
                    "score": result["actual_output"].get("score"),
                    "invariants_ok": _invariants_ok(result),
                    "diff_count": len((result.get("diff") or {}).get("mismatches") or []),
                    "latency_ms": result["latency_ms"],
                }
                for result in results
            ]
            ui.aggrid(
                {
                    "columnDefs": [
                        {"field": "created_at", "headerName": "Timestamp", "sortable": True, "filter": True, "minWidth": 180},
                        {"field": "run_id", "headerName": "Run ID", "sortable": True, "filter": True, "minWidth": 180},
                        {"field": "status", "headerName": "Status", "sortable": True, "filter": True, "width": 120},
                        {"field": "case", "headerName": "Case", "sortable": True, "filter": True, "flex": 1},
                        {"field": "classification", "headerName": "Classification", "sortable": True, "filter": True, "width": 160},
                        {"field": "score", "headerName": "Score", "sortable": True, "filter": "agNumberColumnFilter", "width": 110},
                        {"field": "invariants_ok", "headerName": "Invariants", "sortable": True, "filter": True, "width": 130},
                        {"field": "diff_count", "headerName": "Diffs", "sortable": True, "filter": "agNumberColumnFilter", "width": 100},
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
            detail_container = ui.column().classes("w-full gap-3")

            def update_code() -> None:
                detail_container.clear()
                result = options[selected.value]
                sections = {
                    "Input": result["input_payload"],
                    "Expected": result["expected_output"],
                    "Actual": result["actual_output"],
                    "Diff": result["diff"],
                    "Invariants": result["structured_log"].get("invariants", {}),
                    "Structured Log": result["structured_log"],
                }
                with detail_container:
                    with ui.tabs().classes("w-full") as tabs:
                        tab_map = {name: ui.tab(name) for name in sections}
                    with ui.tab_panels(tabs, value=tab_map["Structured Log"]).classes("w-full"):
                        for name, payload in sections.items():
                            with ui.tab_panel(tab_map[name]):
                                ui.code(json.dumps(payload, ensure_ascii=False, indent=2), language="json").classes("w-full")

            selected.on_value_change(lambda _: update_code())
            update_code()

    def render_context() -> None:
        context_container.clear()
        with context_container:
            ui.label("Contexto técnico para IA").classes("text-xl font-bold afk-title")
            ui.markdown(build_algorithm_context(services.algorithm_repository, algorithm_name=str(selected_algorithm.value))).classes("w-full")

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

    def run_canonical_lead_score() -> None:
        try:
            ensure_default_algorithms(services.algorithm_repository)
            definition = services.algorithm_repository.get_definition_by_name("lead_score")
            run_suite(definition)
        except Exception as exc:  # noqa: BLE001
            ui.notify(f"Erro ao executar lead_score: {exc}", type="negative")

    def export_suite(definition: dict[str, object]) -> None:
        try:
            path = export_algorithm_suite(services.algorithm_repository, str(definition["id"]), services.reports_dir)
            ui.notify(f"Suite exportada: {path}", type="positive")
        except Exception as exc:  # noqa: BLE001
            ui.notify(f"Erro ao exportar suite: {exc}", type="negative")

    def import_suite(path: str | None) -> None:
        if not path:
            ui.notify("Informe o caminho do JSON da suite.", type="warning")
            return
        try:
            definition = import_algorithm_suite(services.algorithm_repository, path)
            ui.notify(f"Suite importada: {definition['name']}", type="positive")
            ui.navigate.reload()
        except Exception as exc:  # noqa: BLE001
            ui.notify(f"Erro ao importar suite: {exc}", type="negative")

    def export_evidence_pack(definition: dict[str, object]) -> None:
        try:
            context = build_algorithm_context(services.algorithm_repository, algorithm_name=str(definition["name"]))
            results = services.algorithm_repository.list_results(algorithm_id=str(definition["id"]), limit=100)
            bundle = create_report_bundle(
                output_dir=services.reports_dir,
                name=f"{definition['name']}_ui_evidence_pack",
                markdown=context,
                payload={
                    "source": "algorithm_test_lab_ui",
                    "algorithm": definition["name"],
                    "invariants": summarize_algorithm_invariants(results),
                },
            )
            ui.notify(f"Evidence pack exportado: {bundle['zip']}", type="positive")
        except Exception as exc:  # noqa: BLE001
            ui.notify(f"Erro ao exportar evidence pack: {exc}", type="negative")

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


def _invariants_ok(result: dict[str, object]) -> bool:
    invariants = (result.get("structured_log") or {}).get("invariants") or {}
    return bool(invariants) and all(value is True for value in invariants.values())
