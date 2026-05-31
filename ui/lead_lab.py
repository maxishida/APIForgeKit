from __future__ import annotations

import json

from nicegui import ui

from core.database import database_status
from core.lead_algorithm import LeadInput, LeadScoreResult, calculate_lead_score
from core.lead_logger import append_lead_test_log
from ui.components.alerts import db_offline
from ui.components.badges import badge
from ui.components.cards import metric_card


def _render_result(output: LeadScoreResult) -> None:
    with ui.grid(columns=4).classes("w-full gap-4"):
        metric_card("Score Final", output.score, "0 a 100", "#00D4FF")
        metric_card("Classificação", output.status, "Status do lead", "#10B981" if output.score > 60 else "#F59E0B")
        metric_card("Confiança", output.confidence, "Determinística", "#2563EB")
        metric_card("Próxima Ação", output.recommended_action, "Recomendação", "#10B981")
    with ui.column().classes("afk-card w-full gap-3").style("padding:18px;"):
        ui.label("Motivos da classificação").classes("text-lg font-bold")
        for reason in output.reasons:
            ui.label(f"• {reason}").classes("afk-muted")
        ui.separator().classes("opacity-20")
        ui.label("Impacto Next.js").classes("text-sm afk-muted")
        ui.label(output.nextjs_impact).classes("afk-neon font-bold")
        ui.code(json.dumps(output.to_dict(), ensure_ascii=False, indent=2), language="json").classes("w-full")


def render_lead_lab(services) -> None:
    status = database_status(services.engine)
    if not status["online"]:
        db_offline(str(status["error"]))

    result_container = ui.column().classes("w-full gap-4")
    with ui.grid(columns=2).classes("w-full gap-4"):
        with ui.column().classes("afk-card gap-4").style("padding:18px;"):
            ui.label("Lead Data").classes("text-lg font-bold")
            lead_name = ui.input("Nome do lead", value="Lead teste").classes("w-full afk-input")
            source = ui.select(["Instagram", "WhatsApp", "Landing Page", "LinkedIn", "Ligação"], value="WhatsApp", label="Origem").classes("w-full afk-input")
            message = ui.textarea("Mensagem", value="Quero comprar hoje pelo WhatsApp. Preciso de orçamento urgente.").classes("w-full afk-input")
        with ui.column().classes("afk-card gap-4").style("padding:18px;"):
            ui.label("Business Data").classes("text-lg font-bold")
            budget = ui.input("Orçamento informado", value="5000").classes("w-full afk-input")
            urgency = ui.select(["baixa", "média", "alta"], value="alta", label="Urgência").classes("w-full afk-input")
            interest = ui.select(["baixo", "médio", "alto"], value="alto", label="Interesse").classes("w-full afk-input")
            ui.label("Contact Data").classes("text-lg font-bold mt-3")
            has_phone = ui.checkbox("Tem telefone", value=True)
            has_email = ui.checkbox("Tem e-mail", value=True)
            previous_customer = ui.checkbox("Já comprou antes", value=False)

    def run_test() -> None:
        current_status = database_status(services.engine)
        if not current_status["online"]:
            ui.notify("PostgreSQL offline. Rode `docker compose up -d` antes de executar testes reais.", type="negative")
            return
        lead_input = LeadInput(
            lead_name=lead_name.value or "",
            source=source.value or "",
            message=message.value or "",
            budget=budget.value or "",
            urgency=urgency.value or "",
            interest=interest.value or "",
            has_phone=bool(has_phone.value),
            has_email=bool(has_email.value),
            previous_customer=bool(previous_customer.value),
        )
        output = calculate_lead_score(lead_input)
        services.repository.create_from_result(lead_input, output)
        append_lead_test_log(services.log_path, lead_input, output)
        result_container.clear()
        with result_container:
            ui.label("Resultado").classes("text-2xl font-extrabold afk-title")
            badge(output.status, output.status)
            _render_result(output)
        ui.notify("Teste executado e persistido com sucesso.", type="positive")

    with ui.row().classes("w-full justify-end"):
        ui.button("Executar Teste", icon="play_arrow", on_click=run_test).classes("afk-primary-btn")

    with result_container:
        ui.label("Resultado").classes("text-2xl font-extrabold afk-title")
        ui.label("Execute um teste para visualizar score, motivos e payload estruturado.").classes("afk-muted")
