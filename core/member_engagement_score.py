from __future__ import annotations

from dataclasses import asdict, dataclass, field


TIER_THRESHOLDS = (
    (81, "Legend"),
    (61, "Theorist"),
    (31, "Resident"),
    (0, "Visitor"),
)

SPAM_FLAGS = frozenset({"spam", "bot", "fake", "promoção suspeita", "promocao suspeita"})


@dataclass(frozen=True)
class MemberEngagementInput:
    member_id: str
    username: str = ""
    posts_count: int = 0
    theories_count: int = 0
    likes_received: int = 0
    comments_received: int = 0
    days_active_streak: int = 0
    days_inactive: int = 0
    badges_count: int = 0
    has_first_post: bool = False
    has_first_theory: bool = False
    spam_flag: str = ""

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class MemberEngagementResult:
    member_id: str
    score: int
    tier: str
    status: str
    reasons: list[str] = field(default_factory=list)
    recommended_action: str = ""
    bot_eligible: bool = False

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["classification"] = self.tier
        payload["engagement_tier"] = self.tier
        payload["engagement_score"] = self.score
        return payload


def _tier_for_score(score: int) -> str:
    for minimum, label in TIER_THRESHOLDS:
        if score >= minimum:
            return label
    return "Visitor"


def calculate_member_engagement_score(member: MemberEngagementInput) -> MemberEngagementResult:
    if not str(member.member_id).strip():
        raise ValueError("member_id is required")

    normalized_spam = (member.spam_flag or "").strip().lower()
    if normalized_spam in SPAM_FLAGS:
        return MemberEngagementResult(
            member_id=member.member_id,
            score=0,
            tier="Visitor",
            status="invalid_member",
            reasons=[f"spam_flag={normalized_spam}"],
            recommended_action="Bloquear automações e revisar moderação.",
            bot_eligible=False,
        )

    score = 0
    reasons: list[str] = []

    if member.has_first_post:
        score += 10
        reasons.append("first_post:+10")
    if member.has_first_theory:
        score += 15
        reasons.append("first_theory:+15")

    extra_posts = max(member.posts_count - (1 if member.has_first_post else 0), 0)
    posts_bonus = min(extra_posts * 2, 20)
    if posts_bonus:
        score += posts_bonus
        reasons.append(f"extra_posts:+{posts_bonus}")

    extra_theories = max(member.theories_count - (1 if member.has_first_theory else 0), 0)
    theories_bonus = min(extra_theories * 3, 15)
    if theories_bonus:
        score += theories_bonus
        reasons.append(f"extra_theories:+{theories_bonus}")

    streak_bonus = min(max(member.days_active_streak, 0) * 5, 25)
    if streak_bonus:
        score += streak_bonus
        reasons.append(f"streak:+{streak_bonus}")

    likes_bonus = min(max(member.likes_received, 0) * 3, 30)
    if likes_bonus:
        score += likes_bonus
        reasons.append(f"likes:+{likes_bonus}")

    comments_bonus = min(max(member.comments_received, 0) * 2, 20)
    if comments_bonus:
        score += comments_bonus
        reasons.append(f"comments:+{comments_bonus}")

    if member.days_inactive >= 7:
        score -= 25
        reasons.append("inactive_7d:-25")

    score = max(0, min(score, 100))
    tier = _tier_for_score(score)
    status = "inactive_member" if member.days_inactive >= 7 else "active_member"
    bot_eligible = tier in {"Theorist", "Legend"} and status == "active_member"

    recommended = "Manter missões padrão de onboarding."
    if tier == "Legend":
        recommended = "Elegível para destaques do TheoryBot e missões avançadas."
    elif tier == "Theorist":
        recommended = "Elegível para TheoryBot e recompensas de engajamento."
    elif tier == "Resident":
        recommended = "Incentivar primeira teoria e retorno diário."
    elif member.days_inactive >= 7:
        recommended = "Disparar ViceBot de retorno e reduzir spam de VIPBot."

    return MemberEngagementResult(
        member_id=member.member_id,
        score=score,
        tier=tier,
        status=status,
        reasons=reasons,
        recommended_action=recommended,
        bot_eligible=bot_eligible,
    )