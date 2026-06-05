from __future__ import annotations

import json
import threading
from pathlib import Path

from nicegui import ui

from core.database import database_status
from core.xai_voice_runner import VOICE_LOG_EVENT_TYPES, VoiceLeadInput, XaiVoiceRunner
from ui.components.alerts import db_offline, empty_state
from ui.components.cards import metric_card


VOICE_LAB_FIELDS = [
    "lead_name",
    "origin",
    "previous_page",
    "user_message",
    "voice_id",
    "tts_language",
    "stt_language",
]

VOICE_LAB_LOG_EVENTS = list(VOICE_LOG_EVENT_TYPES)

VOICE_LAB_HELP_TEXT = (
    "Executa um roundtrip real xAI Voice: TTS gera áudio, STT transcreve, o agente responde e tudo é salvo no PostgreSQL."
)


def render_voice_lab(services) -> None:
    status = database_status(services.engine)
    state: dict[str, object] = {"active": False, "last_run": None, "last_error": ""}

    if not status["online"]:
        db_offline(str(status["error"]))
        empty_state("Voice Lab aguardando PostgreSQL", "Suba o banco com npm run db para gravar logs de voz.")
        return

    with ui.row().classes("w-full items-start justify-between gap-4"):
        with ui.column().classes("gap-1"):
            ui.label("xAI Voice Lab").classes("text-2xl font-bold afk-title")
            ui.label(VOICE_LAB_HELP_TEXT).classes("afk-muted")
        ui.html("<span class='afk-badge'>Real HTTP Voice</span>")

    form_container = ui.column().classes("afk-card w-full gap-4").style("padding:18px;")
    status_container = ui.grid(columns=4).classes("w-full gap-4")
    events_container = ui.column().classes("afk-card w-full gap-3").style("padding:18px;")

    with form_container:
        ui.label("Lead + Voice Input").classes("text-xl font-bold afk-title")
        with ui.grid(columns=3).classes("w-full gap-4"):
            lead_name = ui.input("Lead recebido", value="Lead Voice QA").classes("w-full")
            origin = ui.select(["WhatsApp", "Landing Page", "Instagram", "LinkedIn", "Ligação", "Site"], value="WhatsApp", label="Origem do usuário").classes(
                "w-full"
            )
            previous_page = ui.input("Página visitada antes do contato", value="/pricing").classes("w-full")
        user_message = ui.textarea(
            "Mensagem enviada pelo usuário",
            value="Hello, I want to buy today through WhatsApp. My budget is five hundred dollars.",
        ).classes("w-full").props("rows=4")
        with ui.grid(columns=3).classes("w-full gap-4"):
            voice_id = ui.select(["eve", "ara", "rex", "sal", "leo"], value="eve", label="Voice ID").classes("w-full")
            tts_language = ui.input("TTS language", value="en").classes("w-full")
            stt_language = ui.input("STT language", value="en").classes("w-full")
        with ui.row().classes("gap-3"):
            ui.button(
                "Executar Voice Roundtrip",
                icon="graphic_eq",
                on_click=lambda: _start_voice_roundtrip(
                    services,
                    state,
                    VoiceLeadInput(
                        lead_name=str(lead_name.value or ""),
                        user_message=str(user_message.value or ""),
                        origin=str(origin.value or ""),
                        previous_page=str(previous_page.value or ""),
                        voice_id=str(voice_id.value or "eve"),
                        tts_language=str(tts_language.value or "en"),
                        stt_language=str(stt_language.value or "en"),
                    ),
                    refresh,
                ),
            ).classes("afk-primary-btn")
            ui.button("Abrir Logs", icon="terminal", on_click=lambda: ui.navigate.to("/logs")).classes("afk-ghost-btn")
            ui.button("Context Builder", icon="integration_instructions", on_click=lambda: ui.navigate.to("/context-builder")).classes("afk-ghost-btn")

    def refresh() -> None:
        runs = services.observability_repository.list_runs(limit=20)
        voice_runs = [run for run in runs if run.get("suite_name") == "voice_roundtrip"]
        events = services.observability_repository.list_events(limit=200)
        voice_events = [event for event in events if event.get("module") == "voice"]
        latest_run = voice_runs[0] if voice_runs else {}
        latest_events = [event for event in voice_events if not latest_run or event.get("run_id") == latest_run.get("id")]

        status_container.clear()
        with status_container:
            metric_card("Voice Runs", len(voice_runs), "Roundtrips", "#00D4FF")
            metric_card("Voice Events", len(voice_events), "Logs persistidos", "#2563EB")
            metric_card("Último status", latest_run.get("status", "none"), "Run mais recente", "#10B981" if latest_run.get("status") == "success" else "#F59E0B")
            metric_card("Ativo", "sim" if state["active"] else "não", "Runner", "#00D4FF" if state["active"] else "#9CA3AF")

        events_container.clear()
        with events_container:
            ui.label("Voice Logs").classes("text-xl font-bold afk-title")
            if state.get("last_error"):
                ui.label(str(state["last_error"])).classes("text-red-400")
            if not latest_events:
                ui.label("Nenhum log de voz ainda. Execute o roundtrip para gravar evidência.").classes("afk-muted")
                return
            ui.code(json.dumps(latest_run, ensure_ascii=False, indent=2), language="json").classes("w-full")
            for event in latest_events[:12]:
                ui.html(
                    f"""
                    <div style="border-top:1px solid rgba(255,255,255,.08);padding:10px 0;">
                      <span class="afk-badge">{event.get("status")}</span>
                      <b style="color:#00D4FF">{event.get("event_type")}</b>
                      <span style="color:#9CA3AF"> {event.get("latency_ms")} ms</span>
                      <div>{event.get("message")}</div>
                    </div>
                    """
                )

    refresh()
    ui.timer(2.0, refresh)


def _start_voice_roundtrip(services, state: dict[str, object], lead: VoiceLeadInput, refresh_callback) -> None:
    if state["active"]:
        ui.notify("Voice roundtrip já está em execução.", type="warning")
        return
    if not lead.user_message.strip():
        ui.notify("Informe a mensagem enviada pelo usuário.", type="warning")
        return

    state["active"] = True
    state["last_error"] = ""

    def worker() -> None:
        try:
            output_dir = Path(services.reports_dir) / "voice"
            state["last_run"] = XaiVoiceRunner(services.observability_repository, output_dir=output_dir).run_roundtrip(lead)
        except Exception as exc:  # noqa: BLE001 - surfaced in UI
            state["last_error"] = str(exc)
        finally:
            state["active"] = False

    threading.Thread(target=worker, daemon=True).start()
    ui.notify("Voice roundtrip iniciado. Logs aparecem em /logs e no Dashboard.", type="positive")
    refresh_callback()
