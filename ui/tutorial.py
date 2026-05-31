from __future__ import annotations

from nicegui import ui

from core.config import ROOT_DIR


def render_tutorial() -> None:
    path = ROOT_DIR / "OPEN_SOURCE_TUTORIAL.md"
    if path.exists():
        content = path.read_text(encoding="utf-8")
    else:
        content = "# APIForgeKit Tutorial\n\nTutorial não encontrado."
    with ui.column().classes("afk-card w-full").style("padding:22px;"):
        ui.markdown(content).classes("w-full")
