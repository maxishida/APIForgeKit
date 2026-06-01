from __future__ import annotations

import json
import zipfile
from datetime import UTC, datetime
from html import escape
from pathlib import Path


def create_report_bundle(
    *,
    output_dir: str | Path,
    name: str,
    markdown: str,
    payload: dict[str, object],
) -> dict[str, str]:
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    safe_name = _safe_name(name)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    base_name = f"{safe_name}_{stamp}" if safe_name != "demo" else safe_name

    md_path = directory / f"{base_name}.md"
    json_path = directory / f"{base_name}.json"
    html_path = directory / f"{base_name}.html"
    zip_path = directory / f"{base_name}.zip"

    md_path.write_text(markdown, encoding="utf-8")
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    html_path.write_text(_html(markdown), encoding="utf-8")

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.write(md_path, f"{safe_name}.md")
        archive.write(json_path, f"{safe_name}.json")
        archive.write(html_path, f"{safe_name}.html")

    return {"markdown": str(md_path), "json": str(json_path), "html": str(html_path), "zip": str(zip_path)}


def _safe_name(name: str) -> str:
    return "".join(char if char.isalnum() or char in {"-", "_"} else "_" for char in name.strip().lower()) or "report"


def _html(markdown: str) -> str:
    return (
        "<!doctype html><html><head><meta charset='utf-8'><title>APIForgeKit Report</title>"
        "<style>body{background:#0A0F1C;color:#F9FAFB;font-family:Inter,Arial;padding:32px;line-height:1.6}"
        "pre{white-space:pre-wrap;background:#111827;border:1px solid rgba(0,212,255,.18);padding:20px;border-radius:8px}"
        "code{color:#00D4FF}</style></head><body>"
        f"<pre>{escape(markdown)}</pre>"
        "</body></html>"
    )
