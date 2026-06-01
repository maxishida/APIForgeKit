from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


COLOR_MAP = {
    "urgent_lead": "#10B981",
    "hot_lead": "#00D4FF",
    "warm_lead": "#F59E0B",
    "cold_lead": "#9CA3AF",
    "invalid_lead": "#EF4444",
}


def _style(fig: go.Figure) -> go.Figure:
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#F9FAFB", "family": "Inter"},
        margin={"l": 16, "r": 16, "t": 36, "b": 16},
        legend={"orientation": "h", "y": -0.18},
    )
    return fig


def empty_figure(title: str) -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(text="Sem dados ainda", x=0.5, y=0.5, showarrow=False, font={"color": "#9CA3AF", "size": 16})
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    fig.update_layout(title=title)
    return _style(fig)


def classification_donut(classifications: dict[str, int]) -> go.Figure:
    if not classifications:
        return empty_figure("Leads por Classificação")
    labels = list(classifications)
    values = [classifications[label] for label in labels]
    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.62,
                marker={"colors": [COLOR_MAP.get(label, "#00D4FF") for label in labels]},
            )
        ]
    )
    fig.update_layout(title="Leads por Classificação")
    return _style(fig)


def score_histogram(records: list[dict[str, object]]) -> go.Figure:
    if not records:
        return empty_figure("Distribuição de Score")
    frame = pd.DataFrame(records)
    fig = px.histogram(frame, x="score", nbins=10, title="Distribuição de Score", color_discrete_sequence=["#00D4FF"])
    return _style(fig)


def origin_bar(sources: dict[str, int]) -> go.Figure:
    if not sources:
        return empty_figure("Leads por Origem")
    frame = pd.DataFrame({"source": list(sources), "count": list(sources.values())})
    fig = px.bar(frame, x="source", y="count", title="Leads por Origem", color="source")
    return _style(fig)


def test_evolution(daily_counts: dict[str, int]) -> go.Figure:
    if not daily_counts:
        return empty_figure("Evolução de Testes")
    frame = pd.DataFrame({"date": list(daily_counts), "tests": list(daily_counts.values())})
    fig = px.line(frame, x="date", y="tests", markers=True, title="Evolução de Testes", color_discrete_sequence=["#00D4FF"])
    fig.update_traces(line={"width": 3})
    return _style(fig)


def average_score_area(daily_scores: dict[str, float]) -> go.Figure:
    if not daily_scores:
        return empty_figure("Score Médio por Dia")
    frame = pd.DataFrame({"date": list(daily_scores), "score": list(daily_scores.values())})
    fig = px.area(frame, x="date", y="score", title="Score Médio por Dia", color_discrete_sequence=["#10B981"])
    return _style(fig)


def channel_score_bar(channel_scores: dict[str, float]) -> go.Figure:
    if not channel_scores:
        return empty_figure("Score Médio por Canal")
    frame = pd.DataFrame({"channel": list(channel_scores), "score": list(channel_scores.values())})
    fig = px.bar(frame, x="channel", y="score", title="Score Médio por Canal", color="score", color_continuous_scale=["#2563EB", "#00D4FF", "#10B981"])
    return _style(fig)


OBS_STATUS_COLORS = {
    "success": "#10B981",
    "running": "#00D4FF",
    "failed": "#EF4444",
    "blocked": "#F59E0B",
    "pending": "#9CA3AF",
}


def event_status_donut(events: list[dict[str, object]]) -> go.Figure:
    if not events:
        return empty_figure("Eventos por Status")
    frame = pd.DataFrame(events)
    counts = frame["status"].fillna("unknown").value_counts().reset_index()
    counts.columns = ["status", "count"]
    fig = go.Figure(
        data=[
            go.Pie(
                labels=counts["status"],
                values=counts["count"],
                hole=0.62,
                marker={"colors": [OBS_STATUS_COLORS.get(str(status), "#00D4FF") for status in counts["status"]]},
            )
        ]
    )
    fig.update_layout(title="Eventos por Status")
    return _style(fig)


def module_event_bar(events: list[dict[str, object]]) -> go.Figure:
    if not events:
        return empty_figure("Eventos por Módulo")
    frame = pd.DataFrame(events)
    counts = frame["module"].fillna("unknown").value_counts().reset_index()
    counts.columns = ["module", "count"]
    fig = px.bar(counts, x="module", y="count", title="Eventos por Módulo", color="module")
    return _style(fig)


def latency_timeline(events: list[dict[str, object]]) -> go.Figure:
    latency_events = [event for event in events if float(event.get("latency_ms") or 0) > 0]
    if not latency_events:
        return empty_figure("Latência por Evento")
    frame = pd.DataFrame(latency_events)
    frame["timestamp"] = pd.to_datetime(frame["timestamp"])
    frame = frame.sort_values("timestamp")
    fig = px.line(
        frame,
        x="timestamp",
        y="latency_ms",
        color="module",
        markers=True,
        title="Latência por Evento",
    )
    fig.update_traces(line={"width": 3})
    return _style(fig)


def event_volume_area(events: list[dict[str, object]]) -> go.Figure:
    if not events:
        return empty_figure("Volume de Eventos")
    frame = pd.DataFrame(events)
    frame["timestamp"] = pd.to_datetime(frame["timestamp"])
    frame["minute"] = frame["timestamp"].dt.floor("min")
    counts = frame.groupby("minute").size().reset_index(name="events")
    fig = px.area(counts, x="minute", y="events", title="Volume de Eventos", color_discrete_sequence=["#00D4FF"])
    return _style(fig)


def result_status_donut(results: list[dict[str, object]], title: str = "Passed vs Failed") -> go.Figure:
    if not results:
        return empty_figure(title)
    frame = pd.DataFrame(results)
    counts = frame["status"].fillna("unknown").value_counts().reset_index()
    counts.columns = ["status", "count"]
    fig = go.Figure(
        data=[
            go.Pie(
                labels=counts["status"],
                values=counts["count"],
                hole=0.62,
                marker={"colors": [OBS_STATUS_COLORS.get(str(status), "#00D4FF") for status in counts["status"]]},
            )
        ]
    )
    fig.update_layout(title=title)
    return _style(fig)


def result_latency_bar(results: list[dict[str, object]], label_field: str = "case", title: str = "Latência por Caso") -> go.Figure:
    if not results:
        return empty_figure(title)
    rows = []
    for result in results[:30]:
        log = result.get("structured_log") or {}
        rows.append(
            {
                "label": log.get("case_name") or log.get("test_name") or result.get(label_field) or result.get("id"),
                "latency_ms": float(result.get("latency_ms") or 0),
                "status": result.get("status") or "unknown",
            }
        )
    frame = pd.DataFrame(rows)
    fig = px.bar(frame, x="label", y="latency_ms", color="status", title=title, color_discrete_map=OBS_STATUS_COLORS)
    return _style(fig)


def algorithm_score_distribution(results: list[dict[str, object]]) -> go.Figure:
    rows = []
    for result in results:
        actual = result.get("actual_output") or {}
        if isinstance(actual.get("score"), (int, float)):
            rows.append({"score": actual["score"], "status": result.get("status")})
    if not rows:
        return empty_figure("Distribuição de Score dos Casos")
    frame = pd.DataFrame(rows)
    fig = px.histogram(frame, x="score", color="status", nbins=10, title="Distribuição de Score dos Casos", color_discrete_map=OBS_STATUS_COLORS)
    return _style(fig)
