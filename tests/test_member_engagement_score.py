from core.member_engagement_score import MemberEngagementInput, calculate_member_engagement_score


def test_visitor_without_activity():
    result = calculate_member_engagement_score(MemberEngagementInput(member_id="m1", username="Newbie"))
    assert result.tier == "Visitor"
    assert result.status == "active_member"
    assert result.score == 0
    assert result.bot_eligible is False


def test_resident_with_first_post_theory_and_likes():
    result = calculate_member_engagement_score(
        MemberEngagementInput(
            member_id="m2",
            username="Poster",
            has_first_post=True,
            has_first_theory=True,
            likes_received=2,
        )
    )
    assert result.tier == "Resident"
    assert result.score >= 31
    assert result.bot_eligible is False


def test_theorist_is_bot_eligible():
    result = calculate_member_engagement_score(
        MemberEngagementInput(
            member_id="m3",
            username="TheoryFan",
            has_first_post=True,
            has_first_theory=True,
            likes_received=8,
            comments_received=4,
            days_active_streak=3,
        )
    )
    assert result.tier == "Theorist"
    assert result.score >= 61
    assert result.bot_eligible is True


def test_spam_flag_invalidates_member():
    result = calculate_member_engagement_score(
        MemberEngagementInput(member_id="m6", username="Spammer", spam_flag="spam")
    )
    assert result.score == 0
    assert result.status == "invalid_member"
    assert result.bot_eligible is False


def test_inactive_member_loses_points():
    result = calculate_member_engagement_score(
        MemberEngagementInput(
            member_id="m5",
            username="Away",
            has_first_post=True,
            likes_received=5,
            days_inactive=7,
        )
    )
    assert result.status == "inactive_member"
    assert result.bot_eligible is False


def test_member_id_is_required():
    try:
        calculate_member_engagement_score(MemberEngagementInput(member_id=""))
        raised = False
    except ValueError:
        raised = True
    assert raised