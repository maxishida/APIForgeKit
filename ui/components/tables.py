from __future__ import annotations

from nicegui import ui


def logs_grid(records: list[dict[str, object]]) -> None:
    column_defs = [
        {"field": "created_at", "headerName": "Timestamp", "sortable": True, "filter": True, "minWidth": 180},
        {"field": "lead_name", "headerName": "Lead", "sortable": True, "filter": True},
        {"field": "source", "headerName": "Origem", "sortable": True, "filter": True},
        {"field": "classification", "headerName": "Classificação", "sortable": True, "filter": True},
        {"field": "score", "headerName": "Score", "sortable": True, "filter": "agNumberColumnFilter", "width": 110},
        {"field": "status", "headerName": "Status", "sortable": True, "filter": True, "width": 120},
        {"field": "message", "headerName": "Mensagem", "sortable": False, "filter": True, "flex": 1},
    ]
    ui.aggrid(
        {
            "columnDefs": column_defs,
            "rowData": records,
            "pagination": True,
            "paginationPageSize": 12,
            "animateRows": True,
            "rowSelection": "single",
            "defaultColDef": {"resizable": True},
        },
        theme="quartz-dark",
    ).classes("w-full").style("height:520px")


def observability_grid(records: list[dict[str, object]]) -> None:
    column_defs = [
        {"field": "timestamp", "headerName": "Timestamp", "sortable": True, "filter": True, "minWidth": 180},
        {"field": "provider", "headerName": "Provider", "sortable": True, "filter": True, "width": 120},
        {"field": "module", "headerName": "Module", "sortable": True, "filter": True, "width": 150},
        {"field": "test_name", "headerName": "Test", "sortable": True, "filter": True, "width": 150},
        {"field": "event_type", "headerName": "Event", "sortable": True, "filter": True, "width": 170},
        {"field": "status", "headerName": "Status", "sortable": True, "filter": True, "width": 120},
        {"field": "latency_ms", "headerName": "Latency", "sortable": True, "filter": "agNumberColumnFilter", "width": 120},
        {"field": "message", "headerName": "Message", "sortable": False, "filter": True, "flex": 1},
    ]
    ui.aggrid(
        {
            "columnDefs": column_defs,
            "rowData": records,
            "pagination": True,
            "paginationPageSize": 16,
            "animateRows": True,
            "rowSelection": "single",
            "defaultColDef": {"resizable": True},
        },
        theme="quartz-dark",
    ).classes("w-full").style("height:560px")
