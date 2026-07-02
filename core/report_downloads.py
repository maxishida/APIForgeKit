from __future__ import annotations

from pathlib import Path

from fastapi import HTTPException
from fastapi.responses import FileResponse
from nicegui import app

from core.config import get_settings

MEDIA_TYPES = {
    ".md": "text/markdown; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".zip": "application/zip",
    ".html": "text/html; charset=utf-8",
}


def _safe_report_path(filename: str) -> Path:
    clean = Path(filename).name
    if clean != filename or not clean:
        raise HTTPException(status_code=400, detail="Invalid filename")
    path = get_settings().reports_dir / clean
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="Report not found")
    return path


def register_report_download_routes() -> None:
    @app.get("/download/reports/{filename}")
    def download_report(filename: str) -> FileResponse:
        path = _safe_report_path(filename)
        media_type = MEDIA_TYPES.get(path.suffix.lower(), "application/octet-stream")
        return FileResponse(path, filename=path.name, media_type=media_type)

    @app.get("/exports/reports/{filename}")
    def download_report_alias(filename: str) -> FileResponse:
        path = _safe_report_path(filename)
        media_type = MEDIA_TYPES.get(path.suffix.lower(), "application/octet-stream")
        return FileResponse(path, filename=path.name, media_type=media_type)