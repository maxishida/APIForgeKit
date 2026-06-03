from __future__ import annotations

from html import escape
from pathlib import Path

from nicegui import ui

from core.config import ROOT_DIR


TUTORIAL_DOC_PATH = ROOT_DIR / "docs" / "OPEN_SOURCE_TUTORIAL.md"

TUTORIAL_SECTIONS = [
    {
        "title": "1. Evidence First",
        "body": "Teste -> Log -> PostgreSQL -> Dashboard -> Context Builder -> Evidence Pack. Esse é o caminho antes de pedir implementação para IA.",
        "command": "npm run db && npm run dev",
    },
    {
        "title": "2. Algorithm Test Lab",
        "body": "Use a canonical suite para validar regras determinísticas como lead_score, comparar expected vs actual, ver diff e salvar seed_validation.",
        "command": "npm run algorithm:suite",
    },
    {
        "title": "3. ACP Harness",
        "body": "Conecte IDE, cliente ACP ou CLI ao executor de skill. Para prompt local simples, use python run_acp_prompt.py \"/validate-lead-score\".",
        "command": "python run_acp_prompt.py \"/validate-lead-score\"",
    },
    {
        "title": "4. Context Builder",
        "body": "Exporte Markdown, JSON, HTML e ZIP somente depois que a evidência tiver readiness Ready ou as falhas estiverem documentadas.",
        "command": "python run_acp_prompt.py \"/build-context\"",
    },
]

SYSTEM_DIAGRAM_LANES = [
    {
        "label": "ACP Client / CLI / IDE",
        "detail": "initialize -> session/new -> session/prompt with ContentBlock[]",
        "badge": "entry",
    },
    {
        "label": "SKILL.md Gates",
        "detail": "Classify request, require evidence, block implementation until context exists",
        "badge": "policy",
    },
    {
        "label": "Validation Labs",
        "detail": "Algorithm Test Lab, Generic API Lab, Token Calculator, Provider/xAI Validation",
        "badge": "runner",
    },
    {
        "label": "PostgreSQL Evidence",
        "detail": "Runs, events, requests, responses, token estimates and context exports",
        "badge": "store",
    },
    {
        "label": "Dashboard + Context",
        "detail": "Live metrics, logs, readiness and technical context",
        "badge": "observe",
    },
    {
        "label": "Evidence Pack",
        "detail": "Markdown, JSON, HTML and ZIP for future implementation",
        "badge": "export",
    },
]


def render_tutorial() -> None:
    content = _read_tutorial_markdown()
    _render_hero()
    _render_system_diagram()
    _render_workflow_cards()
    _render_command_panel()
    _render_markdown_reference(content)


def _read_tutorial_markdown() -> str:
    if TUTORIAL_DOC_PATH.exists():
        return TUTORIAL_DOC_PATH.read_text(encoding="utf-8")
    return "# APIForgeKit Tutorial\n\nTutorial nao encontrado em docs/OPEN_SOURCE_TUTORIAL.md."


def _render_hero() -> None:
    ui.html(
        """
        <section class="afk-card" style="padding:28px; overflow:hidden; position:relative;">
          <div style="position:absolute; inset:0; background:linear-gradient(120deg, rgba(0,212,255,.16), transparent 48%, rgba(16,185,129,.09)); pointer-events:none;"></div>
          <div style="position:relative; display:grid; grid-template-columns:minmax(0,1.4fr) minmax(280px,.6fr); gap:24px; align-items:end;">
            <div>
              <div class="afk-badge" style="color:#00D4FF;">Local-first validation harness</div>
              <h2 style="font-size:34px; line-height:1.1; margin:16px 0 10px; color:#F9FAFB; font-weight:850;">APIForgeKit Tutorial</h2>
              <p style="color:#9CA3AF; max-width:820px; font-size:15px; line-height:1.7;">
                Valide APIs, webhooks e algoritmos antes de gerar codigo de produto. O Studio transforma testes em logs, evidencias e contexto reutilizavel para economizar tokens de LLM.
              </p>
            </div>
            <div style="display:grid; gap:10px;">
              <div class="afk-badge">evidence_mode: seed_validation</div>
              <div class="afk-badge">ACP: prompt-driven</div>
              <div class="afk-badge">PostgreSQL: source of truth</div>
            </div>
          </div>
        </section>
        """
    ).classes("w-full")


def _render_workflow_cards() -> None:
    with ui.grid(columns=4).classes("w-full gap-4"):
        for section in TUTORIAL_SECTIONS:
            ui.html(
                f"""
                <article class="afk-card" style="padding:18px; min-height:190px; display:flex; flex-direction:column; gap:12px;">
                  <h3 style="margin:0; color:#F9FAFB; font-size:16px; font-weight:800;">{escape(section["title"])}</h3>
                  <p style="margin:0; color:#9CA3AF; line-height:1.6; font-size:13px;">{escape(section["body"])}</p>
                  <code style="margin-top:auto; display:block; color:#00D4FF; background:rgba(0,212,255,.08); border:1px solid rgba(0,212,255,.18); padding:10px; border-radius:8px; white-space:normal;">{escape(section["command"])}</code>
                </article>
                """
            )


def _render_system_diagram() -> None:
    with ui.column().classes("afk-card w-full gap-4").style("padding:22px;"):
        with ui.row().classes("w-full items-center justify-between gap-3"):
            with ui.column().classes("gap-1"):
                ui.label("System Flow").classes("text-xl font-bold afk-title")
                ui.label("ACP e SKILL.md comandam os labs; evidências voltam para PostgreSQL, dashboard e Context Builder.").classes("text-sm afk-muted")
            ui.link("Abrir Mermaid em docs/SYSTEM_DIAGRAM.md", "https://github.com/maxishida/APIForgeKit/blob/main/docs/SYSTEM_DIAGRAM.md", new_tab=True).classes("afk-neon")
        with ui.grid(columns=6).classes("w-full gap-3"):
            for index, lane in enumerate(SYSTEM_DIAGRAM_LANES):
                arrow = "->" if index < len(SYSTEM_DIAGRAM_LANES) - 1 else "OK"
                ui.html(
                    f"""
                    <div style="min-height:178px; border:1px solid rgba(0,212,255,.18); border-radius:8px; padding:14px; background:rgba(11,18,32,.72); display:flex; flex-direction:column; gap:10px;">
                      <div style="display:flex; align-items:center; justify-content:space-between; gap:8px;">
                        <span class="afk-badge" style="color:#00D4FF;">{escape(lane["badge"])}</span>
                        <span style="color:#9CA3AF; font-weight:800;">{arrow}</span>
                      </div>
                      <strong style="color:#F9FAFB; line-height:1.25;">{escape(lane["label"])}</strong>
                      <p style="color:#9CA3AF; font-size:13px; line-height:1.55; margin:0;">{escape(lane["detail"])}</p>
                    </div>
                    """
                )


def _render_command_panel() -> None:
    commands = [
        ("Studio", "python app.py", "Abre a interface NiceGUI em http://localhost:8080."),
        ("Algorithm", "npm run algorithm:suite", "Executa lead_score e exporta contexto/evidencia."),
        ("ACP stdio", "npm run acp", "Servidor ACP para IDEs e clientes compativeis."),
        ("ACP prompt", 'python run_acp_prompt.py "/validate-lead-score"', "Atalho CLI para rodar um comando ACP completo."),
    ]
    with ui.column().classes("afk-card w-full gap-3").style("padding:22px;"):
        ui.label("Quick Start").classes("text-lg font-bold afk-title")
        ui.label("Use estes comandos para gravar uma apresentacao, testar o MVP ou conectar o harness em um fluxo de IDE/CLI.").classes("text-sm afk-muted")
        with ui.grid(columns=2).classes("w-full gap-3"):
            for label, command, description in commands:
                ui.html(
                    f"""
                    <div style="border:1px solid rgba(0,212,255,.16); border-radius:8px; padding:14px; background:rgba(11,18,32,.72);">
                      <div style="display:flex; align-items:center; justify-content:space-between; gap:10px;">
                        <strong style="color:#F9FAFB;">{escape(label)}</strong>
                        <span class="afk-badge">ready</span>
                      </div>
                      <code style="display:block; margin:12px 0; color:#00D4FF;">{escape(command)}</code>
                      <p style="margin:0; color:#9CA3AF; font-size:13px;">{escape(description)}</p>
                    </div>
                    """
                )


def _render_markdown_reference(content: str) -> None:
    with ui.column().classes("afk-card w-full gap-3").style("padding:22px;"):
        ui.label("Open Source Tutorial").classes("text-lg font-bold afk-title")
        ui.label(str(TUTORIAL_DOC_PATH.relative_to(ROOT_DIR))).classes("text-xs afk-muted")
        ui.markdown(content).classes("w-full")
