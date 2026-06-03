from ui import live_dashboard


def test_live_dashboard_declares_operational_signal_cards():
    labels = [card["label"] for card in live_dashboard.DASHBOARD_SIGNAL_CARDS]

    assert labels == [
        "Evidence Modes",
        "P95 Latency",
        "Recent Failures",
        "Last Event",
    ]


def test_live_dashboard_has_empty_state_copy_for_filtered_stream():
    assert "Nenhum evento encontrado" in live_dashboard.LIVE_DASHBOARD_EMPTY_STATE_COPY
    assert "filtros" in live_dashboard.LIVE_DASHBOARD_EMPTY_STATE_COPY
