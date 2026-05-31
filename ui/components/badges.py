from __future__ import annotations

from html import escape

from nicegui import ui


COLORS = {
    "urgent_lead": "#10B981",
    "hot_lead": "#00D4FF",
    "warm_lead": "#F59E0B",
    "cold_lead": "#9CA3AF",
    "invalid_lead": "#EF4444",
    "success": "#10B981",
    "failed": "#EF4444",
}


def badge(label: str, value: str) -> None:
    color = COLORS.get(value, "#9CA3AF")
    ui.html(
        f"""
        <span class="afk-badge" style="color:{color};">
          <span style="width:7px;height:7px;border-radius:999px;background:{color};box-shadow:0 0 16px {color};"></span>
          {escape(label)}
        </span>
        """
    )
