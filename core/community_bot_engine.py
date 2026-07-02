from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from typing import Any


CONDITION_OPERATORS = frozenset(
    {
        "equals",
        "not_equals",
        "greater_than",
        "less_than",
        "exists",
        "not_exists",
        "contains",
        "not_contains",
    }
)

ACTION_TYPES = frozenset(
    {
        "send_notification",
        "send_popup",
        "create_feed_post",
        "give_credits",
        "give_badge",
        "add_ranking_points",
        "recommend_page",
        "assign_mission",
    }
)

SKIP_STATUSES = frozenset(
    {"rate_limited", "duplicate_blocked", "condition_not_met", "rule_inactive", "bot_inactive"}
)


@dataclass(frozen=True)
class BotEvent:
    user_id: str
    event_name: str
    entity_type: str = ""
    entity_id: str = ""
    metadata_json: dict[str, Any] = field(default_factory=dict)
    source: str = "web_app"
    simulate: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class BotRule:
    id: str
    bot_id: str
    bot_name: str
    bot_slug: str
    name: str
    event_name: str
    condition_json: dict[str, Any]
    action_json: list[dict[str, Any]]
    template_id: str = ""
    priority: int = 0
    is_active: bool = True
    cooldown_minutes: int = 0
    run_once_per_user: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class BotActionLog:
    bot_id: str
    rule_id: str
    user_id: str
    event_name: str
    action_type: str
    status: str
    input_json: dict[str, Any]
    output_json: dict[str, Any]
    error_message: str = ""
    execution_time_ms: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class BotEngineResult:
    status: str
    classification: str
    rules_evaluated: int
    rules_matched: int
    actions_executed: list[dict[str, Any]]
    actions_skipped: list[dict[str, Any]]
    bot_logs: list[dict[str, Any]]
    reasons: list[str]
    user_updates: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _resolve_path(context: dict[str, Any], path: str) -> Any:
    current: Any = context
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def evaluate_condition(operand: Any, operator: str, expected: Any) -> bool:
    if operator not in CONDITION_OPERATORS:
        raise ValueError(f"Unsupported condition operator: {operator}")

    if operator == "exists":
        return operand is not None
    if operator == "not_exists":
        return operand is None
    if operator == "equals":
        return operand == expected
    if operator == "not_equals":
        return operand != expected
    if operator == "greater_than":
        if operand is None or expected is None:
            return False
        return operand > expected
    if operator == "less_than":
        if operand is None or expected is None:
            return False
        return operand < expected
    if operator == "contains":
        if operand is None:
            return False
        if isinstance(operand, (list, tuple, set)):
            return expected in operand
        if isinstance(operand, str):
            return str(expected) in operand
        return False
    if operator == "not_contains":
        if operand is None:
            return True
        if isinstance(operand, (list, tuple, set)):
            return expected not in operand
        if isinstance(operand, str):
            return str(expected) not in operand
        return True
    return False


def evaluate_conditions(
    conditions: dict[str, Any],
    event: BotEvent,
    user: dict[str, Any],
) -> bool:
    if not conditions:
        return True

    context = {"user": user, "event": event.to_dict()}
    for key, spec in conditions.items():
        if isinstance(spec, dict) and "operator" in spec:
            operand = _resolve_path(context, str(spec.get("path", key)))
            if not evaluate_condition(operand, str(spec["operator"]), spec.get("value")):
                return False
            continue

        operand = _resolve_path(context, key)
        if operand != spec:
            return False
    return True


def _unique_event_key(user_id: str, event_name: str, rule_id: str) -> str:
    return f"{user_id}:{event_name}:{rule_id}"


def _parse_timestamp(value: str) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=UTC)
        return parsed
    except ValueError:
        return None


def check_rule_safety(
    rule: BotRule,
    event: BotEvent,
    history: list[dict[str, Any]],
    now: datetime,
) -> tuple[bool, str]:
    if not rule.is_active:
        return False, "rule_inactive"

    key = _unique_event_key(event.user_id, event.event_name, rule.id)
    if rule.run_once_per_user:
        for entry in history:
            if entry.get("unique_event_key") == key and entry.get("status") == "success":
                return False, "duplicate_blocked"
            if (
                entry.get("rule_id") == rule.id
                and entry.get("user_id") == event.user_id
                and entry.get("status") == "success"
            ):
                return False, "duplicate_blocked"

    if rule.cooldown_minutes > 0:
        cutoff = now - timedelta(minutes=rule.cooldown_minutes)
        for entry in history:
            if entry.get("rule_id") != rule.id or entry.get("user_id") != event.user_id:
                continue
            if entry.get("status") not in {"success", "rate_limited"}:
                continue
            created_at = _parse_timestamp(str(entry.get("created_at", "")))
            if created_at and created_at >= cutoff:
                return False, "rate_limited"

    return True, "allowed"


def _deterministic_id(prefix: str, *parts: str) -> str:
    digest = sha256(":".join(parts).encode("utf-8")).hexdigest()[:10]
    return f"{prefix}_{digest}"


def render_template(template: str, variables: dict[str, Any]) -> str:
    rendered = template
    for key, value in variables.items():
        rendered = rendered.replace(f"{{{{{key}}}}}", str(value))
    return rendered


def execute_action(
    action: dict[str, Any],
    rule: BotRule,
    event: BotEvent,
    user: dict[str, Any],
    templates: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    action_type = str(action.get("type", ""))
    if action_type not in ACTION_TYPES:
        raise ValueError(f"Unsupported action type: {action_type}")

    variables = {
        "username": user.get("username", user.get("user_id", "")),
        "bot_name": rule.bot_name,
        "credits": action.get("amount", user.get("credits", 0)),
        "badge_name": action.get("badge_slug", action.get("badge_name", "")),
        "post_title": event.metadata_json.get("title", ""),
        "theory_title": event.metadata_json.get("title", ""),
        "level": user.get("level", 1),
        "days_inactive": event.metadata_json.get("days_inactive", 0),
        "launch_days_left": event.metadata_json.get("launch_days_left", 0),
        "mission_name": action.get("mission_slug", ""),
        "vip_plan": user.get("vip_plan", ""),
    }

    template_key = str(action.get("template", ""))
    template = templates.get(template_key, {})
    title = render_template(str(template.get("title", action.get("title", ""))), variables)
    message = render_template(str(template.get("message", action.get("message", ""))), variables)

    output: dict[str, Any] = {
        "action_type": action_type,
        "simulated": event.simulate,
        "bot_id": rule.bot_id,
        "bot_name": rule.bot_name,
        "bot_slug": rule.bot_slug,
        "official_tag": "BOT OFICIAL",
    }

    if action_type == "send_notification":
        output["notification"] = {
            "id": _deterministic_id("notif", rule.id, event.user_id, action_type, template_key),
            "title": title,
            "message": message,
            "type": action.get("notification_type", "system"),
            "url": action.get("url", ""),
        }
    elif action_type == "send_popup":
        output["popup"] = {"title": title, "message": message}
    elif action_type == "create_feed_post":
        output["feed_post"] = {
            "id": _deterministic_id("post", rule.id, event.user_id, action_type, str(action.get("title", ""))),
            "title": title or action.get("title", ""),
            "message": message,
            "bot_slug": rule.bot_slug,
        }
    elif action_type == "give_credits":
        output["credits_transaction"] = {
            "amount": int(action.get("amount", 0)),
            "type": "bot_reward",
            "reason": action.get("reason", "bot_reward"),
        }
        output["credits_delta"] = int(action.get("amount", 0))
    elif action_type == "give_badge":
        output["badge"] = {
            "slug": action.get("badge_slug", ""),
            "name": action.get("badge_name", action.get("badge_slug", "")),
            "source": "bot_reward",
        }
    elif action_type == "add_ranking_points":
        output["ranking_points"] = int(action.get("points", 0))
    elif action_type == "recommend_page":
        output["recommended_page"] = action.get("page", "")
    elif action_type == "assign_mission":
        output["mission"] = {
            "slug": action.get("mission_slug", ""),
            "name": action.get("mission_name", action.get("mission_slug", "")),
        }

    return output


def _apply_user_updates(user: dict[str, Any], action_output: dict[str, Any]) -> None:
    if "credits_delta" in action_output:
        user["credits"] = int(user.get("credits", 0)) + int(action_output["credits_delta"])

    if "badge" in action_output:
        badges = list(user.get("badges", []))
        slug = action_output["badge"]["slug"]
        if slug and slug not in badges:
            badges.append(slug)
        user["badges"] = badges

    if "ranking_points" in action_output:
        user["ranking_points"] = int(user.get("ranking_points", 0)) + int(action_output["ranking_points"])

    if action_output.get("action_type") == "send_notification":
        notification_type = (action_output.get("notification") or {}).get("type", "")
        if notification_type == "welcome":
            user["hasReceivedWelcome"] = True
        if notification_type == "mission":
            user["hasActiveMission"] = True

    if action_output.get("action_type") == "assign_mission":
        user["hasActiveMission"] = True


def process_bot_event(
    event: BotEvent,
    user: dict[str, Any],
    rules: list[BotRule],
    history: list[dict[str, Any]] | None = None,
    templates: dict[str, dict[str, Any]] | None = None,
    now: datetime | None = None,
) -> BotEngineResult:
    if not event.user_id.strip():
        raise ValueError("user_id is required")
    if not event.event_name.strip():
        raise ValueError("event_name is required")

    history = history or []
    templates = templates or {}
    now = now or datetime.now(UTC)
    user_state = deepcopy(user)

    active_rules = [
        rule
        for rule in sorted(rules, key=lambda item: item.priority, reverse=True)
        if rule.is_active and rule.event_name == event.event_name
    ]

    executed: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    logs: list[dict[str, Any]] = []
    reasons: list[str] = []
    matched = 0

    for rule in active_rules:
        allowed, safety_reason = check_rule_safety(rule, event, history, now)
        if not allowed:
            skip_entry = {
                "rule_id": rule.id,
                "rule_name": rule.name,
                "bot_name": rule.bot_name,
                "status": safety_reason,
            }
            skipped.append(skip_entry)
            logs.append(
                BotActionLog(
                    bot_id=rule.bot_id,
                    rule_id=rule.id,
                    user_id=event.user_id,
                    event_name=event.event_name,
                    action_type="rule_gate",
                    status=safety_reason,
                    input_json={"run_once_per_user": rule.run_once_per_user, "cooldown_minutes": rule.cooldown_minutes},
                    output_json={},
                ).to_dict()
            )
            reasons.append(f"{rule.name}: bloqueado por {safety_reason}")
            continue

        if not evaluate_conditions(rule.condition_json, event, user_state):
            skip_entry = {
                "rule_id": rule.id,
                "rule_name": rule.name,
                "bot_name": rule.bot_name,
                "status": "condition_not_met",
            }
            skipped.append(skip_entry)
            logs.append(
                BotActionLog(
                    bot_id=rule.bot_id,
                    rule_id=rule.id,
                    user_id=event.user_id,
                    event_name=event.event_name,
                    action_type="rule_gate",
                    status="condition_not_met",
                    input_json={"conditions": rule.condition_json},
                    output_json={},
                ).to_dict()
            )
            reasons.append(f"{rule.name}: condição não atendida")
            continue

        matched += 1
        rule_outputs: list[dict[str, Any]] = []
        for action in rule.action_json:
            output = execute_action(action, rule, event, user_state, templates)
            if event.simulate:
                output["simulated"] = True
            executed.append(output)
            rule_outputs.append(output)
            _apply_user_updates(user_state, output)
            logs.append(
                BotActionLog(
                    bot_id=rule.bot_id,
                    rule_id=rule.id,
                    user_id=event.user_id,
                    event_name=event.event_name,
                    action_type=str(action.get("type", "")),
                    status="success",
                    input_json=dict(action),
                    output_json=output,
                    execution_time_ms=1,
                ).to_dict()
            )

        reasons.append(f"{rule.name}: {len(rule_outputs)} ação(ões) executada(s)")

    blocking_skips = [
        item for item in skipped if str(item.get("status")) not in {"condition_not_met", "rule_inactive", "bot_inactive"}
    ]
    classification = "success"
    if matched == 0 and skipped:
        classification = "blocked"
    elif matched > 0 and blocking_skips:
        classification = "partial"

    return BotEngineResult(
        status="processed",
        classification=classification,
        rules_evaluated=len(active_rules),
        rules_matched=matched,
        actions_executed=executed,
        actions_skipped=skipped,
        bot_logs=logs,
        reasons=reasons,
        user_updates=user_state,
    )