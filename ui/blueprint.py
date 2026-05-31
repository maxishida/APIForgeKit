from __future__ import annotations

from datetime import UTC, datetime

from nicegui import ui

from core.blueprint_generator import export_nextjs_blueprint, generate_nextjs_blueprint


def render_blueprint(services) -> None:
    blueprint = generate_nextjs_blueprint()
    with ui.grid(columns=2).classes("w-full gap-4"):
        with ui.column().classes("afk-card gap-3").style("padding:18px;"):
            ui.label("Next.js Blueprint Generator").classes("text-xl font-bold")
            ui.label("Blueprint local para implementação futura com Prisma e API route.").classes("afk-muted")
            ui.button("Exportar Blueprint", icon="download", on_click=lambda: _export(services)).classes("afk-primary-btn")
        with ui.column().classes("afk-card gap-2").style("padding:18px;"):
            ui.label("Árvore visual").classes("text-xl font-bold")
            for item in ["app/api/leads/route.ts", "lib/lead-score.ts", "lib/prisma.ts", "types/lead.ts", "prisma/schema.prisma", "components/dashboard/*"]:
                with ui.row().classes("items-center gap-2"):
                    ui.icon("description").classes("afk-neon")
                    ui.label(item).classes("font-semibold")
    with ui.column().classes("afk-card w-full").style("padding:18px;"):
        ui.markdown(blueprint).classes("w-full")


def _export(services) -> None:
    path = services.blueprints_dir / f"nextjs_blueprint_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}.md"
    export_nextjs_blueprint(path)
    ui.notify(f"Blueprint exportado: {path}", type="positive")
