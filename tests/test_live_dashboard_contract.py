from ui.live_dashboard import LIVE_DASHBOARD_MODULE_OPTIONS


def test_live_dashboard_module_options_include_responses_api_and_chat_legacy():
    assert "responses_api" in LIVE_DASHBOARD_MODULE_OPTIONS
    assert "chat_legacy" in LIVE_DASHBOARD_MODULE_OPTIONS
