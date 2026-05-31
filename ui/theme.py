from __future__ import annotations

from nicegui import ui


CSS = """
:root {
  --afk-bg: #0A0F1C;
  --afk-panel: #111827;
  --afk-panel-2: #0B1220;
  --afk-border: rgba(37, 99, 235, 0.28);
  --afk-accent: #00D4FF;
  --afk-accent-2: #2563EB;
  --afk-success: #10B981;
  --afk-warning: #F59E0B;
  --afk-error: #EF4444;
  --afk-text: #F9FAFB;
  --afk-muted: #9CA3AF;
}

body, .nicegui-content {
  background:
    radial-gradient(circle at 20% 10%, rgba(0, 212, 255, 0.10), transparent 28rem),
    radial-gradient(circle at 80% 0%, rgba(37, 99, 235, 0.10), transparent 32rem),
    var(--afk-bg) !important;
  color: var(--afk-text) !important;
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}

.afk-sidebar {
  background: linear-gradient(180deg, rgba(11, 18, 32, 0.98), rgba(10, 15, 28, 0.98)) !important;
  border-right: 1px solid rgba(0, 212, 255, 0.14);
}

.afk-header {
  background: rgba(10, 15, 28, 0.84) !important;
  border-bottom: 1px solid rgba(0, 212, 255, 0.15);
  backdrop-filter: blur(14px);
}

.afk-page {
  max-width: 1500px;
  margin: 0 auto;
  padding: 24px;
}

.afk-card {
  background: linear-gradient(180deg, rgba(17, 24, 39, 0.94), rgba(11, 18, 32, 0.96));
  border: 1px solid var(--afk-border);
  border-radius: 8px;
  box-shadow: 0 20px 70px rgba(0, 0, 0, 0.22), inset 0 1px 0 rgba(255, 255, 255, 0.03);
}

.afk-card:hover {
  border-color: rgba(0, 212, 255, 0.52);
  box-shadow: 0 24px 80px rgba(0, 212, 255, 0.08), 0 20px 70px rgba(0, 0, 0, 0.22);
  transform: translateY(-1px);
  transition: all 140ms ease;
}

.afk-title {
  color: var(--afk-text);
  letter-spacing: 0;
}

.afk-muted {
  color: var(--afk-muted);
}

.afk-neon {
  color: var(--afk-accent);
  text-shadow: 0 0 20px rgba(0, 212, 255, 0.3);
}

.afk-input .q-field__control,
.q-field__control {
  background: rgba(15, 23, 42, 0.95) !important;
  border: 1px solid rgba(148, 163, 184, 0.18) !important;
  color: var(--afk-text) !important;
}

.q-field__label, .q-field__native, .q-field__input, .q-checkbox__label {
  color: var(--afk-text) !important;
}

.q-menu, .q-item {
  background: #111827 !important;
  color: var(--afk-text) !important;
}

.afk-primary-btn {
  background: linear-gradient(135deg, #00D4FF, #2563EB) !important;
  color: white !important;
  border-radius: 8px !important;
  box-shadow: 0 16px 40px rgba(0, 212, 255, 0.22);
}

.afk-ghost-btn {
  background: rgba(17, 24, 39, 0.9) !important;
  color: var(--afk-text) !important;
  border: 1px solid rgba(0, 212, 255, 0.22) !important;
  border-radius: 8px !important;
}

.afk-link {
  color: var(--afk-muted) !important;
  border-radius: 8px;
  padding: 10px 12px;
  width: 100%;
}

.afk-link:hover, .afk-link-active {
  color: var(--afk-text) !important;
  background: rgba(0, 212, 255, 0.10) !important;
  border: 1px solid rgba(0, 212, 255, 0.22);
}

.afk-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border-radius: 999px;
  padding: 4px 10px;
  font-size: 12px;
  border: 1px solid rgba(255,255,255,0.10);
  background: rgba(255,255,255,0.05);
}

.ag-theme-quartz-dark {
  --ag-background-color: #111827;
  --ag-foreground-color: #F9FAFB;
  --ag-header-background-color: #0B1220;
  --ag-border-color: rgba(37, 99, 235, 0.24);
  --ag-row-hover-color: rgba(0, 212, 255, 0.08);
  --ag-selected-row-background-color: rgba(37, 99, 235, 0.20);
}
"""


def apply_theme() -> None:
    ui.add_head_html(
        "<link rel=\"preconnect\" href=\"https://fonts.googleapis.com\">"
        "<link rel=\"preconnect\" href=\"https://fonts.gstatic.com\" crossorigin>"
        "<link href=\"https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap\" rel=\"stylesheet\">"
    )
    ui.add_head_html(f"<style>{CSS}</style>")
    ui.colors(primary="#00D4FF", secondary="#2563EB", accent="#10B981", dark="#0A0F1C")
