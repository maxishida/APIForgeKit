from __future__ import annotations

from html import escape

from nicegui import ui


def metric_card(label: str, value: object, caption: str = "", accent: str = "#00D4FF") -> None:
    ui.html(
        f"""
        <div class="afk-card" style="padding:18px; min-height:126px;">
          <div style="display:flex;align-items:center;justify-content:space-between;gap:12px;">
            <div style="color:#9CA3AF;font-size:12px;text-transform:uppercase;font-weight:700;letter-spacing:.08em;">{escape(label)}</div>
            <div style="width:10px;height:10px;border-radius:999px;background:{accent};box-shadow:0 0 22px {accent};"></div>
          </div>
          <div style="font-size:32px;line-height:1.1;font-weight:800;color:#F9FAFB;margin-top:12px;">{escape(str(value))}</div>
          <div style="color:#9CA3AF;font-size:13px;margin-top:8px;">{escape(caption)}</div>
        </div>
        """
    ).classes("w-full")


def section_card(title: str, subtitle: str = ""):
    with ui.column().classes("afk-card w-full gap-3").style("padding:18px;"):
        ui.label(title).classes("text-lg font-bold afk-title")
        if subtitle:
            ui.label(subtitle).classes("text-sm afk-muted")
        yield
