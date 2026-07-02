from datetime import UTC, datetime

from core.community_bot_engine import (
    BotEvent,
    BotRule,
    check_rule_safety,
    evaluate_condition,
    evaluate_conditions,
    process_bot_event,
)
from core.community_bot_seed import _BASE_RULES, _DEFAULT_TEMPLATES


def _rule(rule_id: str) -> BotRule:
    payload = next(item for item in _BASE_RULES if item["id"] == rule_id)
    return BotRule(**payload)


def test_condition_operators_cover_mvp_comparisons():
    assert evaluate_condition(3, "less_than", 5) is True
    assert evaluate_condition(["first_post"], "not_contains", "vip") is True
    assert evaluate_condition("hello world", "contains", "world") is True
    assert evaluate_condition(None, "not_exists", None) is True


def test_first_login_runs_welcome_and_mission_rules():
    event = BotEvent(user_id="user_1", event_name="user.first_login")
    user = {
        "user_id": "user_1",
        "username": "Tommy",
        "hasReceivedWelcome": False,
        "hasActiveMission": False,
        "profileCompleted": False,
        "credits": 0,
        "badges": [],
    }
    rules = [_rule("rule_welcome"), _rule("rule_first_mission")]
    result = process_bot_event(event, user, rules, templates=_DEFAULT_TEMPLATES)

    assert result.classification == "success"
    assert result.rules_matched == 2
    assert len(result.actions_executed) == 4
    assert result.user_updates["credits"] == 10
    assert result.user_updates["hasReceivedWelcome"] is True
    assert result.user_updates["hasActiveMission"] is True


def test_run_once_blocks_duplicate_welcome():
    event = BotEvent(user_id="user_1", event_name="user.first_login")
    user = {"user_id": "user_1", "username": "Tommy", "hasReceivedWelcome": False, "hasActiveMission": False}
    rules = [_rule("rule_welcome")]
    history = [
        {
            "rule_id": "rule_welcome",
            "user_id": "user_1",
            "status": "success",
            "unique_event_key": "user_1:user.first_login:rule_welcome",
            "created_at": "2026-07-01T10:00:00+00:00",
        }
    ]
    allowed, reason = check_rule_safety(_rule("rule_welcome"), event, history, datetime.now(UTC))
    assert allowed is False
    assert reason == "duplicate_blocked"


def test_credits_low_condition_uses_user_state():
    event = BotEvent(user_id="user_2", event_name="credits.low")
    user = {"user_id": "user_2", "username": "Low", "credits": 20}
    assert evaluate_conditions(_rule("rule_credits_low").condition_json, event, user) is False

    user["credits"] = 2
    assert evaluate_conditions(_rule("rule_credits_low").condition_json, event, user) is True