from __future__ import annotations

MEMBER_ENGAGEMENT_RULES = [
    "Score 0-100 com clamp determinístico",
    "Tiers: Visitor 0-30, Resident 31-60, Theorist 61-80, Legend 81-100",
    "+10 first_post, +15 first_theory",
    "+2 por post extra além do first (cap 20), +3 por teoria extra além da first (cap 15)",
    "+5 por dia de streak (cap 25)",
    "+3 por like recebido (cap 30), +2 por comentário (cap 20)",
    "-25 se days_inactive >= 7",
    "spam_flag bloqueia com status invalid_member e score 0",
    "bot_eligible true para Theorist/Legend ativos",
    "Usado pelo Bot Engine via user.engagementScore e user.engagementTier",
]

MEMBER_ENGAGEMENT_NEXTJS_FILES = [
    "/lib/member-engagement-score.ts",
    "/services/member-score.service.ts",
    "/prisma/schema.prisma",
    "/tests/member-engagement-score.test.ts",
]

MEMBER_ENGAGEMENT_INPUT_SCHEMA = {
    "type": "object",
    "required": ["member_id"],
    "properties": {
        "member_id": {"type": "string"},
        "username": {"type": "string"},
        "posts_count": {"type": "integer"},
        "theories_count": {"type": "integer"},
        "likes_received": {"type": "integer"},
        "comments_received": {"type": "integer"},
        "days_active_streak": {"type": "integer"},
        "days_inactive": {"type": "integer"},
        "badges_count": {"type": "integer"},
        "has_first_post": {"type": "boolean"},
        "has_first_theory": {"type": "boolean"},
        "spam_flag": {"type": "string"},
    },
}

MEMBER_ENGAGEMENT_OUTPUT_SCHEMA = {
    "type": "object",
    "required": ["score", "tier", "status", "reasons", "bot_eligible"],
    "properties": {
        "score": {"type": "integer"},
        "tier": {"type": "string"},
        "status": {"type": "string"},
        "reasons": {"type": "array"},
        "bot_eligible": {"type": "boolean"},
    },
}

DEFAULT_MEMBER_ENGAGEMENT_CASES = [
    {
        "name": "visitante novo sem atividade",
        "input_payload": {"member_id": "m1", "username": "Newbie"},
        "expected_output": {"tier": "Visitor", "status": "active_member", "min_score": 0, "max_score": 30},
        "tags": ["cold", "visitor"],
    },
    {
        "name": "residente com first post",
        "input_payload": {
            "member_id": "m2",
            "username": "Poster",
            "has_first_post": True,
            "has_first_theory": True,
            "posts_count": 1,
            "likes_received": 2,
        },
        "expected_output": {"tier": "Resident", "status": "active_member", "min_score": 31},
        "tags": ["resident"],
    },
    {
        "name": "teorico engajado",
        "input_payload": {
            "member_id": "m3",
            "username": "TheoryFan",
            "has_first_post": True,
            "has_first_theory": True,
            "theories_count": 3,
            "likes_received": 8,
            "comments_received": 4,
            "days_active_streak": 3,
        },
        "expected_output": {"tier": "Theorist", "status": "active_member", "min_score": 61, "bot_eligible": True},
        "tags": ["theorist", "bot"],
    },
    {
        "name": "lenda da comunidade",
        "input_payload": {
            "member_id": "m4",
            "username": "Legend",
            "has_first_post": True,
            "has_first_theory": True,
            "likes_received": 15,
            "comments_received": 10,
            "days_active_streak": 5,
        },
        "expected_output": {"tier": "Legend", "status": "active_member", "min_score": 81, "bot_eligible": True},
        "tags": ["legend"],
    },
    {
        "name": "inativo 7 dias perde pontos",
        "input_payload": {
            "member_id": "m5",
            "username": "Away",
            "has_first_post": True,
            "likes_received": 5,
            "days_inactive": 7,
        },
        "expected_output": {"tier": "Visitor", "status": "inactive_member", "bot_eligible": False},
        "tags": ["inactive", "edge"],
    },
    {
        "name": "spam invalida membro",
        "input_payload": {"member_id": "m6", "username": "Spammer", "spam_flag": "spam"},
        "expected_output": {"tier": "Visitor", "status": "invalid_member", "score": 0, "bot_eligible": False},
        "tags": ["spam", "invalid"],
    },
    {
        "name": "streak capped em 25",
        "input_payload": {
            "member_id": "m7",
            "username": "Streaker",
            "has_first_post": True,
            "days_active_streak": 10,
        },
        "expected_output": {"min_score": 30, "max_score": 45},
        "tags": ["streak", "cap"],
    },
    {
        "name": "likes capped em 30",
        "input_payload": {
            "member_id": "m8",
            "username": "Liked",
            "has_first_theory": True,
            "likes_received": 20,
        },
        "expected_output": {"min_score": 40, "max_score": 55},
        "tags": ["likes", "cap"],
    },
    {
        "name": "residente medio",
        "input_payload": {
            "member_id": "m9",
            "username": "Mid",
            "has_first_post": True,
            "has_first_theory": True,
            "likes_received": 3,
            "comments_received": 2,
        },
        "expected_output": {"tier": "Resident", "min_score": 31, "max_score": 60},
        "tags": ["resident"],
    },
    {
        "name": "bot elegivel theorist minimo",
        "input_payload": {
            "member_id": "m10",
            "username": "Eligible",
            "has_first_post": True,
            "has_first_theory": True,
            "likes_received": 10,
            "comments_received": 5,
            "days_active_streak": 2,
        },
        "expected_output": {"tier": "Theorist", "bot_eligible": True, "min_score": 61},
        "tags": ["bot", "pipeline"],
    },
    {
        "name": "member_id obrigatorio",
        "input_payload": {"member_id": ""},
        "expected_output": {"status": "invalid_input"},
        "tags": ["validation", "edge"],
    },
    {
        "name": "deterministico mesmo input",
        "input_payload": {
            "member_id": "m11",
            "username": "Stable",
            "has_first_post": True,
            "has_first_theory": True,
            "likes_received": 4,
        },
        "expected_output": {"tier": "Resident", "min_score": 31},
        "tags": ["deterministic"],
    },
]