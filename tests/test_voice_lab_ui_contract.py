from ui import voice_lab


def test_voice_lab_declares_required_lead_fields_and_log_events():
    assert voice_lab.VOICE_LAB_FIELDS == [
        "lead_name",
        "origin",
        "previous_page",
        "user_message",
        "voice_id",
        "tts_language",
        "stt_language",
    ]
    assert {
        "lead_received",
        "user_message_received",
        "agent_response_request_started",
        "agent_response_received",
        "api_error",
        "voice_call_completed",
    }.issubset(set(voice_lab.VOICE_LAB_LOG_EVENTS))


def test_voice_lab_copy_explains_real_xai_voice_roundtrip():
    assert "TTS" in voice_lab.VOICE_LAB_HELP_TEXT
    assert "STT" in voice_lab.VOICE_LAB_HELP_TEXT
    assert "PostgreSQL" in voice_lab.VOICE_LAB_HELP_TEXT
