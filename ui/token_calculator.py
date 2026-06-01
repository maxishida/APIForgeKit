from __future__ import annotations

import json

from nicegui import ui

from core.database import database_status
from core.token_usage import calculate_token_cost, estimate_context_savings, get_pricing, provider_options
from ui.components.alerts import db_offline
from ui.components.cards import metric_card


def render_token_calculator(services) -> None:
    status = database_status(services.engine)
    if not status["online"]:
        db_offline(str(status["error"]))

    repository = services.token_usage_repository
    options = provider_options()
    provider = ui.select(list(options), value="xai", label="Provider").classes("w-full")
    model = ui.select(options["xai"], value=options["xai"][0], label="Modelo").classes("w-full")
    metrics_container = ui.grid(columns=4).classes("w-full gap-4")
    details_container = ui.column().classes("afk-card w-full gap-4").style("padding:18px;")
    history_container = ui.column().classes("afk-card w-full gap-4").style("padding:18px;")

    with ui.grid(columns=2).classes("w-full gap-4"):
        with ui.column().classes("afk-card gap-4").style("padding:18px;"):
            ui.label("Usage Calculator").classes("text-xl font-bold afk-title")
            ui.label("Calcule custo por usuário usando preços seedados de docs oficiais do provider.").classes("afk-muted")
            users = ui.number("Usuários", value=10, min=1, step=1).classes("w-full")
            requests_per_day = ui.number("Requests por usuário / dia", value=20, min=0, step=1).classes("w-full")
            days = ui.number("Dias", value=30, min=1, step=1).classes("w-full")
            input_tokens = ui.number("Input tokens por request", value=1000, min=0, step=100).classes("w-full")
            cached_tokens = ui.number("Cached input tokens por request", value=0, min=0, step=100).classes("w-full")
            output_tokens = ui.number("Output tokens por request", value=500, min=0, step=100).classes("w-full")
            ui.button(
                "Calcular e salvar",
                icon="calculate",
                on_click=lambda: calculate_and_save(
                    provider.value,
                    model.value,
                    int(users.value or 1),
                    int(requests_per_day.value or 0),
                    int(days.value or 30),
                    int(input_tokens.value or 0),
                    int(output_tokens.value or 0),
                    int(cached_tokens.value or 0),
                ),
            ).classes("afk-primary-btn")

        with ui.column().classes("afk-card gap-4").style("padding:18px;"):
            ui.label("Context Savings").classes("text-xl font-bold afk-title")
            ui.label("Compare prompt cru versus contexto técnico compacto gerado pelo Lab.").classes("afk-muted")
            raw_context = ui.number("Tokens do prompt cru", value=80000, min=0, step=1000).classes("w-full")
            structured_context = ui.number("Tokens do contexto estruturado", value=12000, min=0, step=1000).classes("w-full")
            repeated_calls = ui.number("Chamadas repetidas", value=5, min=1, step=1).classes("w-full")
            savings_code = ui.code("Calcule para ver economia estimada.", language="json").classes("w-full")

            def calculate_savings() -> None:
                savings = estimate_context_savings(
                    provider=str(provider.value),
                    model=str(model.value),
                    raw_context_tokens=int(raw_context.value or 0),
                    structured_context_tokens=int(structured_context.value or 0),
                    output_tokens=int(output_tokens.value or 0),
                    repeated_calls=int(repeated_calls.value or 1),
                )
                savings_code.set_content(json.dumps(savings, ensure_ascii=False, indent=2))

            ui.button("Calcular economia", icon="savings", on_click=calculate_savings).classes("afk-ghost-btn")

    def sync_models() -> None:
        model.options = options[str(provider.value)]
        model.value = options[str(provider.value)][0]
        model.update()
        render_pricing()

    def render_pricing() -> None:
        pricing = get_pricing(str(provider.value), str(model.value))
        details_container.clear()
        with details_container:
            ui.label("Pricing Source").classes("text-xl font-bold afk-title")
            ui.html(f"<span class='afk-badge'>{pricing.provider} / {pricing.model}</span>")
            ui.label(f"Input: ${pricing.input_per_million}/1M tokens").classes("afk-muted")
            ui.label(f"Cached input: ${pricing.cached_input_per_million}/1M tokens").classes("afk-muted")
            ui.label(f"Output: ${pricing.output_per_million}/1M tokens").classes("afk-muted")
            ui.link("Abrir documentação oficial de preço", pricing.source_url, new_tab=True).classes("afk-neon")
            ui.label(pricing.notes).classes("afk-muted")

    def calculate_and_save(
        provider_value: str,
        model_value: str,
        users_value: int,
        requests_value: int,
        days_value: int,
        input_value: int,
        output_value: int,
        cached_value: int,
    ) -> None:
        estimate = calculate_token_cost(
            provider=provider_value,
            model=model_value,
            input_tokens_per_request=input_value,
            output_tokens_per_request=output_value,
            cached_input_tokens_per_request=cached_value,
            users=users_value,
            requests_per_user_per_day=requests_value,
            days=days_value,
        )
        if status["online"]:
            repository.save_estimate(estimate)
        ui.notify(f"Custo estimado: ${estimate['estimated_cost_usd']} / {estimate['users']} usuários.", type="positive")
        render_metrics(estimate)
        render_history()

    def render_metrics(estimate: dict[str, object] | None = None) -> None:
        if estimate is None:
            estimate = calculate_token_cost(
                provider=str(provider.value),
                model=str(model.value),
                input_tokens_per_request=1000,
                output_tokens_per_request=500,
                users=10,
                requests_per_user_per_day=20,
                days=30,
            )
        metrics_container.clear()
        with metrics_container:
            metric_card("Requests", estimate["total_requests"], "Projetados", "#00D4FF")
            metric_card("Tokens", estimate["total_tokens"], "Input + output", "#2563EB")
            metric_card("Custo", f"${estimate['estimated_cost_usd']}", "USD estimado", "#10B981")
            metric_card("Por usuário", f"${estimate['cost_per_user_usd']}", "No período", "#F59E0B")

    def render_history() -> None:
        history_container.clear()
        with history_container:
            ui.label("Histórico de estimativas").classes("text-xl font-bold afk-title")
            if not status["online"]:
                ui.label("PostgreSQL offline. O cálculo funciona, mas o histórico não será salvo.").classes("afk-muted")
                return
            rows = repository.list_estimates(limit=50)
            if not rows:
                ui.label("Nenhuma estimativa salva ainda.").classes("afk-muted")
                return
            ui.aggrid(
                {
                    "columnDefs": [
                        {"field": "created_at", "headerName": "Timestamp", "sortable": True, "filter": True, "minWidth": 180},
                        {"field": "provider", "headerName": "Provider", "sortable": True, "filter": True, "width": 120},
                        {"field": "model", "headerName": "Model", "sortable": True, "filter": True, "flex": 1},
                        {"field": "users", "headerName": "Users", "sortable": True, "filter": "agNumberColumnFilter", "width": 110},
                        {"field": "estimated_cost_usd", "headerName": "Cost", "sortable": True, "filter": "agNumberColumnFilter", "width": 120},
                    ],
                    "rowData": rows,
                    "pagination": True,
                    "paginationPageSize": 8,
                    "defaultColDef": {"resizable": True},
                },
                theme="quartz-dark",
            ).classes("w-full").style("height:300px")

    provider.on_value_change(lambda _: sync_models())
    model.on_value_change(lambda _: render_pricing())
    render_pricing()
    render_metrics()
    render_history()
