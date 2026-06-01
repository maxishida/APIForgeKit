from __future__ import annotations

import json

from nicegui import ui

from core.database import database_status
from core.token_usage import calculate_token_cost, estimate_context_savings, get_pricing, get_usage_presets, provider_options
from ui.components.alerts import db_offline
from ui.components.cards import metric_card


ACCENT_BY_PROVIDER = {
    "xai": "#00D4FF",
    "openai": "#10B981",
    "anthropic": "#F59E0B",
    "gemini": "#2563EB",
}


def render_token_calculator(services) -> None:
    status = database_status(services.engine)
    if not status["online"]:
        db_offline(str(status["error"]))

    repository = services.token_usage_repository
    options = provider_options()
    presets = get_usage_presets()
    active_preset = {"key": "saas_small"}

    with ui.row().classes("w-full items-start justify-between gap-4"):
        with ui.column().classes("gap-1"):
            ui.label("Token Cost Lab").classes("text-2xl font-bold afk-title")
            ui.label("Simule uso por usuário, estime custo e compare contexto bruto contra evidência compacta.").classes("afk-muted")
        ui.html("<span class='afk-badge'>Planning Harness</span>")

    with ui.grid(columns=4).classes("w-full gap-3"):
        for key, preset in presets.items():
            ui.button(
                str(preset["label"]),
                icon="speed",
                on_click=lambda preset_key=key: apply_preset(preset_key),
            ).classes("afk-ghost-btn")

    with ui.grid(columns=3).classes("w-full gap-4"):
        with ui.column().classes("afk-card gap-4").style("padding:18px;"):
            with ui.row().classes("w-full items-center justify-between"):
                ui.label("Modelo").classes("text-xl font-bold afk-title")
                provider_badge = ui.html("")
            provider = ui.select(list(options), value="xai", label="Provider").classes("w-full")
            model = ui.select(options["xai"], value=options["xai"][0], label="Modelo").classes("w-full")
            with ui.row().classes("gap-3"):
                ui.button("Fonte oficial", icon="open_in_new", on_click=lambda: ui.run_javascript(f"window.open('{get_pricing(str(provider.value), str(model.value)).source_url}', '_blank')")).classes(
                    "afk-ghost-btn"
                )
                ui.button("Salvar estimativa", icon="save", on_click=lambda: calculate_and_save()).classes("afk-primary-btn")

        with ui.column().classes("afk-card gap-4").style("padding:18px;"):
            ui.label("Volume").classes("text-xl font-bold afk-title")
            users = ui.number("Usuários", value=50, min=1, step=1).classes("w-full")
            requests_per_day = ui.number("Requests / usuário / dia", value=15, min=0, step=1).classes("w-full")
            days = ui.number("Dias", value=30, min=1, step=1).classes("w-full")

        with ui.column().classes("afk-card gap-4").style("padding:18px;"):
            ui.label("Tokens").classes("text-xl font-bold afk-title")
            input_tokens = ui.number("Input / request", value=1400, min=0, step=100).classes("w-full")
            cached_tokens = ui.number("Cached input / request", value=200, min=0, step=100).classes("w-full")
            output_tokens = ui.number("Output / request", value=500, min=0, step=100).classes("w-full")

    with ui.grid(columns=2).classes("w-full gap-4"):
        with ui.column().classes("afk-card gap-4").style("padding:18px;"):
            ui.label("Context Savings").classes("text-xl font-bold afk-title")
            with ui.grid(columns=3).classes("w-full gap-3"):
                raw_context = ui.number("Prompt bruto", value=80_000, min=0, step=1000).classes("w-full")
                structured_context = ui.number("Contexto validado", value=12_000, min=0, step=1000).classes("w-full")
                repeated_calls = ui.number("Repetições", value=8, min=1, step=1).classes("w-full")
            savings_metrics_container = ui.grid(columns=3).classes("w-full gap-4")
            savings_code = ui.code("{}", language="json").classes("w-full")

        with ui.column().classes("afk-card gap-3").style("padding:18px;"):
            ui.label("Checklist").classes("text-xl font-bold afk-title")
            for text in [
                "Conferir preço oficial antes de decisão financeira.",
                "Medir tokens reais nos logs do provider quando disponível.",
                "Trocar prompt bruto por contexto técnico do APIForgeKit.",
                "Salvar estimativas para comparar modelos ao longo do projeto.",
            ]:
                ui.html(f"<div class='afk-muted' style='display:flex;gap:8px;align-items:center'><span class='afk-badge'>i</span>{text}</div>")

    metrics_container = ui.grid(columns=4).classes("w-full gap-4")

    with ui.grid(columns=2).classes("w-full gap-4"):
        details_container = ui.column().classes("afk-card w-full gap-4").style("padding:18px;")
        result_container = ui.column().classes("afk-card w-full gap-4").style("padding:18px;")

    history_container = ui.column().classes("afk-card w-full gap-4").style("padding:18px;")

    def sync_models() -> None:
        model.options = options[str(provider.value)]
        model.value = options[str(provider.value)][0]
        model.update()
        refresh_all()

    def render_pricing() -> None:
        pricing = get_pricing(str(provider.value), str(model.value))
        details_container.clear()
        with details_container:
            ui.label("Pricing Source").classes("text-xl font-bold afk-title")
            ui.html(f"<span class='afk-badge'>{pricing.provider} / {pricing.model}</span>")
            with ui.grid(columns=3).classes("w-full gap-3"):
                metric_card("Input", f"${pricing.input_per_million}", "/1M tokens", ACCENT_BY_PROVIDER.get(pricing.provider, "#00D4FF"))
                metric_card("Cached", f"${pricing.cached_input_per_million}", "/1M tokens", "#2563EB")
                metric_card("Output", f"${pricing.output_per_million}", "/1M tokens", "#F59E0B")
            ui.link("Abrir documentação oficial de preço", pricing.source_url, new_tab=True).classes("afk-neon")
            ui.label(pricing.notes).classes("afk-muted")
        provider_badge.set_content(f"<span class='afk-badge' style='color:{ACCENT_BY_PROVIDER.get(str(provider.value), '#00D4FF')}'>{provider.value}</span>")

    def current_estimate() -> dict[str, object]:
        return calculate_token_cost(
            provider=str(provider.value),
            model=str(model.value),
            input_tokens_per_request=int(input_tokens.value or 0),
            output_tokens_per_request=int(output_tokens.value or 0),
            cached_input_tokens_per_request=int(cached_tokens.value or 0),
            users=int(users.value or 1),
            requests_per_user_per_day=int(requests_per_day.value or 0),
            days=int(days.value or 30),
        )

    def current_savings() -> dict[str, object]:
        return estimate_context_savings(
            provider=str(provider.value),
            model=str(model.value),
            raw_context_tokens=int(raw_context.value or 0),
            structured_context_tokens=int(structured_context.value or 0),
            output_tokens=int(output_tokens.value or 0),
            repeated_calls=int(repeated_calls.value or 1),
        )

    def calculate_and_save() -> None:
        estimate = current_estimate()
        if status["online"]:
            repository.save_estimate(estimate)
        ui.notify(f"Custo estimado: ${estimate['estimated_cost_usd']} / {estimate['users']} usuários.", type="positive")
        refresh_all()
        render_history()

    def render_metrics() -> None:
        estimate = current_estimate()
        metrics_container.clear()
        with metrics_container:
            metric_card("Requests", estimate["total_requests"], "Projetados", "#00D4FF")
            metric_card("Tokens", estimate["total_tokens"], "Input + output", "#2563EB")
            metric_card("Custo", f"${estimate['estimated_cost_usd']}", "USD estimado", "#10B981")
            metric_card("Por usuário", f"${estimate['cost_per_user_usd']}", "No período", "#F59E0B")
        result_container.clear()
        with result_container:
            ui.label("Resumo do cálculo").classes("text-xl font-bold afk-title")
            ui.code(json.dumps(estimate, ensure_ascii=False, indent=2), language="json").classes("w-full")

    def render_savings() -> None:
        savings = current_savings()
        savings_metrics_container.clear()
        with savings_metrics_container:
            metric_card("Economia", f"${savings['saved_cost_usd']}", f"{savings['savings_percent']}%", "#10B981")
            metric_card("Tokens salvos", savings["saved_tokens"], "Prompt bruto - contexto", "#00D4FF")
            metric_card("Chamadas", savings["repeated_calls"], "Repetições", "#F59E0B")
        savings_code.set_content(json.dumps(savings, ensure_ascii=False, indent=2))

    def refresh_all() -> None:
        render_pricing()
        render_metrics()
        render_savings()

    def apply_preset(preset_key: str) -> None:
        active_preset["key"] = preset_key
        preset = presets[preset_key]
        users.value = int(preset["users"])
        requests_per_day.value = int(preset["requests_per_user_per_day"])
        days.value = int(preset["days"])
        input_tokens.value = int(preset["input_tokens_per_request"])
        output_tokens.value = int(preset["output_tokens_per_request"])
        cached_tokens.value = int(preset["cached_input_tokens_per_request"])
        raw_context.value = int(preset["raw_context_tokens"])
        structured_context.value = int(preset["structured_context_tokens"])
        repeated_calls.value = int(preset["repeated_calls"])
        refresh_all()

    def render_history() -> None:
        history_container.clear()
        with history_container:
            with ui.row().classes("w-full items-center justify-between"):
                ui.label("Histórico de estimativas").classes("text-xl font-bold afk-title")
                ui.html(f"<span class='afk-badge'>{active_preset['key']}</span>")
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
                        {"field": "total_tokens", "headerName": "Tokens", "sortable": True, "filter": "agNumberColumnFilter", "width": 130},
                    ],
                    "rowData": rows,
                    "pagination": True,
                    "paginationPageSize": 8,
                    "defaultColDef": {"resizable": True},
                },
                theme="quartz-dark",
            ).classes("w-full").style("height:300px")

    provider.on_value_change(lambda _: sync_models())
    model.on_value_change(lambda _: refresh_all())
    for control in (users, requests_per_day, days, input_tokens, cached_tokens, output_tokens, raw_context, structured_context, repeated_calls):
        control.on_value_change(lambda _: refresh_all())
    refresh_all()
    render_history()
