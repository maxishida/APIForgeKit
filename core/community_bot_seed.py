from __future__ import annotations

COMMUNITY_BOT_ENGINE_RULES = [
    "Pipeline: User Action -> Event -> Rules Engine -> Conditions -> Actions -> Logs",
    "Regras ordenadas por prioridade decrescente",
    "run_once_per_user bloqueia boas-vindas e primeira missão duplicadas",
    "cooldown_minutes bloqueia spam de alertas VIP",
    "Condições suportam equals, not_equals, greater_than, less_than, exists, not_exists, contains",
    "Ações MVP: send_notification, give_credits, give_badge, assign_mission, recommend_page, create_feed_post, add_ranking_points",
    "Bots oficiais sempre carregam tag BOT OFICIAL",
    "Modo simulate não persiste efeitos colaterais reais, mas retorna plano de execução",
    "Todo processamento de regra gera bot_action_logs",
    "user.first_login dispara ViceBot + MissionBot + créditos de boas-vindas",
    "post.first_created entrega badge Novo Morador + ranking",
    "theory.first_created entrega badge Teórico + créditos",
    "credits.low dispara VIPBot com recommend_page /vip",
    "user.inactive_3_days dispara retorno da comunidade",
    "theory.trending cria post automático no feed",
    "user.engagementTier e user.engagementScore alimentados por member_engagement_score",
    "Theorist elegível recebe missão avançada extra em theory.first_created",
]

COMMUNITY_BOT_NEXTJS_FILES = [
    "/lib/community-bot-engine.ts",
    "/lib/bot-rules-engine.ts",
    "/lib/condition-evaluator.ts",
    "/lib/bot-action-executor.ts",
    "/services/event-tracking.service.ts",
    "/services/bot-logger.service.ts",
    "/app/api/events/track/route.ts",
    "/app/api/admin/bots/simulate-event/route.ts",
    "/app/admin/bots/page.tsx",
    "/prisma/schema.prisma",
    "/tests/community-bot-engine.test.ts",
]

COMMUNITY_BOT_INPUT_SCHEMA = {
    "type": "object",
    "required": ["event", "user", "rules"],
    "properties": {
        "event": {"type": "object"},
        "user": {"type": "object"},
        "rules": {"type": "array"},
        "history": {"type": "array"},
        "templates": {"type": "object"},
    },
}

COMMUNITY_BOT_OUTPUT_SCHEMA = {
    "type": "object",
    "required": [
        "status",
        "classification",
        "rules_evaluated",
        "rules_matched",
        "actions_executed",
        "actions_skipped",
        "bot_logs",
        "reasons",
    ],
    "properties": {
        "status": {"type": "string"},
        "classification": {"type": "string"},
        "rules_evaluated": {"type": "integer"},
        "rules_matched": {"type": "integer"},
        "actions_executed": {"type": "array"},
        "actions_skipped": {"type": "array"},
        "bot_logs": {"type": "array"},
        "reasons": {"type": "array"},
    },
}

_WELCOME_TEMPLATE = {
    "title": "Bem-vindo à Vice City, {{username}}",
    "message": "Sua jornada começou. Crie sua primeira teoria e ganhe {{credits}} créditos.",
}

_MISSION_TEMPLATE = {
    "title": "Missão desbloqueada",
    "message": "Publique sua primeira teoria. Recompensa: badge Novo Morador + 10 créditos.",
}

_VIP_TEMPLATE = {
    "title": "Créditos baixos",
    "message": "Você tem poucos créditos. Assine VIP para receber benefícios mensais.",
}

_DEFAULT_TEMPLATES = {
    "welcome_new_user": _WELCOME_TEMPLATE,
    "mission_first_theory": _MISSION_TEMPLATE,
    "vip_low_credits": _VIP_TEMPLATE,
}

_BASE_RULES = [
    {
        "id": "rule_welcome",
        "bot_id": "bot_vice",
        "bot_name": "ViceBot",
        "bot_slug": "vicebot",
        "name": "ViceBot boas-vindas",
        "event_name": "user.first_login",
        "condition_json": {
            "user.hasReceivedWelcome": False,
            "user.profileCompleted": False,
        },
        "action_json": [
            {
                "type": "send_notification",
                "template": "welcome_new_user",
                "notification_type": "welcome",
            },
            {"type": "give_credits", "amount": 10, "reason": "welcome_bonus"},
        ],
        "priority": 100,
        "run_once_per_user": True,
    },
    {
        "id": "rule_first_mission",
        "bot_id": "bot_mission",
        "bot_name": "MissionBot",
        "bot_slug": "missionbot",
        "name": "Missão inicial",
        "event_name": "user.first_login",
        "condition_json": {"user.hasActiveMission": False},
        "action_json": [
            {
                "type": "assign_mission",
                "mission_slug": "first_theory",
                "mission_name": "Publique sua primeira teoria",
            },
            {
                "type": "send_notification",
                "template": "mission_first_theory",
                "notification_type": "mission",
            },
        ],
        "priority": 90,
        "run_once_per_user": True,
    },
    {
        "id": "rule_first_post",
        "bot_id": "bot_mission",
        "bot_name": "MissionBot",
        "bot_slug": "missionbot",
        "name": "Badge primeiro post",
        "event_name": "post.first_created",
        "condition_json": {
            "user.badges": {"operator": "not_contains", "path": "user.badges", "value": "first_post"},
        },
        "action_json": [
            {
                "type": "send_notification",
                "title": "Parabéns pelo primeiro post",
                "message": "Você publicou seu primeiro post em Vice City.",
                "notification_type": "mission",
            },
            {
                "type": "give_badge",
                "badge_slug": "first_post",
                "badge_name": "Novo Morador de Vice City",
            },
            {"type": "add_ranking_points", "points": 20},
        ],
        "priority": 80,
        "run_once_per_user": True,
    },
    {
        "id": "rule_first_theory",
        "bot_id": "bot_theory",
        "bot_name": "TheoryBot",
        "bot_slug": "theorybot",
        "name": "Badge primeira teoria",
        "event_name": "theory.first_created",
        "condition_json": {
            "user.badges": {"operator": "not_contains", "path": "user.badges", "value": "first_theory"},
        },
        "action_json": [
            {
                "type": "send_notification",
                "title": "Primeira teoria publicada",
                "message": "Você ganhou o badge Teórico de Leonida.",
                "notification_type": "theory",
            },
            {"type": "give_badge", "badge_slug": "first_theory", "badge_name": "Teórico de Leonida"},
            {"type": "give_credits", "amount": 15, "reason": "first_theory_bonus"},
        ],
        "priority": 80,
        "run_once_per_user": True,
    },
    {
        "id": "rule_theorist_bonus",
        "bot_id": "bot_theory",
        "bot_name": "TheoryBot",
        "bot_slug": "theorybot",
        "name": "Bônus pipeline para Theorist elegível",
        "event_name": "theory.first_created",
        "condition_json": {
            "user.engagementTier": {"operator": "equals", "path": "user.engagementTier", "value": "Theorist"},
            "user.engagementScore": {"operator": "greater_than", "path": "user.engagementScore", "value": 60},
        },
        "action_json": [
            {
                "type": "assign_mission",
                "mission_slug": "advanced_theory",
                "mission_name": "Teoria avançada desbloqueada",
            },
            {"type": "give_credits", "amount": 5, "reason": "theorist_pipeline_bonus"},
        ],
        "priority": 75,
        "run_once_per_user": True,
    },
    {
        "id": "rule_credits_low",
        "bot_id": "bot_vip",
        "bot_name": "VIPBot",
        "bot_slug": "vipbot",
        "name": "Alerta créditos baixos",
        "event_name": "credits.low",
        "condition_json": {
            "user.credits": {"operator": "less_than", "path": "user.credits", "value": 5},
        },
        "action_json": [
            {
                "type": "send_notification",
                "template": "vip_low_credits",
                "notification_type": "vip",
            },
            {"type": "recommend_page", "page": "/vip"},
        ],
        "priority": 70,
        "cooldown_minutes": 1440,
    },
    {
        "id": "rule_inactive_return",
        "bot_id": "bot_vice",
        "bot_name": "ViceBot",
        "bot_slug": "vicebot",
        "name": "Retorno após inatividade",
        "event_name": "user.inactive_3_days",
        "condition_json": {},
        "action_json": [
            {
                "type": "send_notification",
                "title": "Sentimos sua falta",
                "message": "Volte para /theories e participe da comunidade.",
                "notification_type": "system",
            },
            {"type": "recommend_page", "page": "/theories"},
        ],
        "priority": 60,
        "cooldown_minutes": 4320,
    },
    {
        "id": "rule_theory_trending",
        "bot_id": "bot_theory",
        "bot_name": "TheoryBot",
        "bot_slug": "theorybot",
        "name": "Teoria em alta",
        "event_name": "theory.trending",
        "condition_json": {
            "event.metadata_json.likes": {"operator": "greater_than", "path": "event.metadata_json.likes", "value": 10},
        },
        "action_json": [
            {
                "type": "create_feed_post",
                "title": "Teoria do dia",
                "message": "Participe da discussão sobre {{theory_title}}.",
            }
        ],
        "priority": 50,
    },
]

DEFAULT_COMMUNITY_BOT_CASES = [
    {
        "name": "fluxo 1 primeiro login completo",
        "input_payload": {
            "event": {
                "user_id": "user_123",
                "event_name": "user.first_login",
                "entity_type": "user",
                "entity_id": "user_123",
                "metadata_json": {"page": "/dashboard"},
                "source": "web_app",
            },
            "user": {
                "user_id": "user_123",
                "username": "Tommy",
                "profileCompleted": False,
                "hasReceivedWelcome": False,
                "hasActiveMission": False,
                "credits": 0,
                "badges": [],
                "level": 1,
            },
            "rules": _BASE_RULES,
            "history": [],
            "templates": _DEFAULT_TEMPLATES,
        },
        "expected_output": {
            "classification": "success",
            "rules_matched": 2,
            "actions_executed_count": 4,
            "action_types": [
                "send_notification",
                "give_credits",
                "assign_mission",
                "send_notification",
            ],
        },
        "tags": ["mvp", "onboarding", "welcome"],
    },
    {
        "name": "fluxo 1 boas-vindas duplicada bloqueada",
        "input_payload": {
            "event": {
                "user_id": "user_123",
                "event_name": "user.first_login",
                "entity_type": "user",
                "entity_id": "user_123",
                "metadata_json": {},
                "source": "web_app",
            },
            "user": {
                "user_id": "user_123",
                "username": "Tommy",
                "profileCompleted": False,
                "hasReceivedWelcome": False,
                "hasActiveMission": False,
                "credits": 10,
                "badges": [],
            },
            "rules": [_BASE_RULES[0]],
            "history": [
                {
                    "rule_id": "rule_welcome",
                    "user_id": "user_123",
                    "status": "success",
                    "unique_event_key": "user_123:user.first_login:rule_welcome",
                    "created_at": "2026-07-01T10:00:00+00:00",
                }
            ],
            "templates": _DEFAULT_TEMPLATES,
        },
        "expected_output": {
            "classification": "blocked",
            "rules_matched": 0,
            "skipped_status": "duplicate_blocked",
        },
        "tags": ["mvp", "idempotency", "edge"],
    },
    {
        "name": "fluxo 2 primeiro post badge e ranking",
        "input_payload": {
            "event": {
                "user_id": "user_456",
                "event_name": "post.first_created",
                "entity_type": "post",
                "entity_id": "post_999",
                "metadata_json": {"title": "Jason vai trair Lucia?", "category": "theory"},
            },
            "user": {
                "user_id": "user_456",
                "username": "LuciaFan",
                "badges": [],
                "ranking_points": 0,
            },
            "rules": _BASE_RULES,
            "history": [],
            "templates": _DEFAULT_TEMPLATES,
        },
        "expected_output": {
            "classification": "success",
            "rules_matched": 1,
            "actions_executed_count": 3,
            "action_types": ["send_notification", "give_badge", "add_ranking_points"],
        },
        "tags": ["mvp", "gamification"],
    },
    {
        "name": "fluxo 3 primeira teoria badge e creditos",
        "input_payload": {
            "event": {
                "user_id": "user_789",
                "event_name": "theory.first_created",
                "entity_type": "theory",
                "entity_id": "theory_001",
                "metadata_json": {"title": "Lucia protege Jason"},
            },
            "user": {
                "user_id": "user_789",
                "username": "TheoryKing",
                "credits": 5,
                "badges": [],
            },
            "rules": _BASE_RULES,
            "history": [],
            "templates": _DEFAULT_TEMPLATES,
        },
        "expected_output": {
            "classification": "success",
            "rules_matched": 1,
            "actions_executed_count": 3,
            "action_types": ["send_notification", "give_badge", "give_credits"],
        },
        "tags": ["mvp", "theory"],
    },
    {
        "name": "fluxo 4 creditos baixos VIPBot",
        "input_payload": {
            "event": {
                "user_id": "user_vip",
                "event_name": "credits.low",
                "entity_type": "user",
                "entity_id": "user_vip",
                "metadata_json": {"page": "/dashboard"},
            },
            "user": {"user_id": "user_vip", "username": "LowCredits", "credits": 3},
            "rules": _BASE_RULES,
            "history": [],
            "templates": _DEFAULT_TEMPLATES,
        },
        "expected_output": {
            "classification": "success",
            "rules_matched": 1,
            "actions_executed_count": 2,
            "action_types": ["send_notification", "recommend_page"],
        },
        "tags": ["mvp", "vip", "monetization"],
    },
    {
        "name": "fluxo 4 condicao creditos nao atendida",
        "input_payload": {
            "event": {
                "user_id": "user_ok",
                "event_name": "credits.low",
                "entity_type": "user",
                "entity_id": "user_ok",
                "metadata_json": {},
            },
            "user": {"user_id": "user_ok", "username": "RichUser", "credits": 20},
            "rules": _BASE_RULES,
            "history": [],
            "templates": _DEFAULT_TEMPLATES,
        },
        "expected_output": {
            "classification": "blocked",
            "rules_matched": 0,
            "skipped_status": "condition_not_met",
        },
        "tags": ["mvp", "condition"],
    },
    {
        "name": "fluxo 5 usuario inativo retorno",
        "input_payload": {
            "event": {
                "user_id": "user_inactive",
                "event_name": "user.inactive_3_days",
                "entity_type": "user",
                "entity_id": "user_inactive",
                "metadata_json": {"days_inactive": 4, "page": "/feed"},
            },
            "user": {"user_id": "user_inactive", "username": "AwayUser"},
            "rules": _BASE_RULES,
            "history": [],
            "templates": _DEFAULT_TEMPLATES,
        },
        "expected_output": {
            "classification": "success",
            "rules_matched": 1,
            "actions_executed_count": 2,
            "action_types": ["send_notification", "recommend_page"],
        },
        "tags": ["mvp", "retention"],
    },
    {
        "name": "fluxo 6 teoria trending feed post",
        "input_payload": {
            "event": {
                "user_id": "user_trend",
                "event_name": "theory.trending",
                "entity_type": "theory",
                "entity_id": "theory_hot",
                "metadata_json": {"title": "Jason trai Lucia?", "likes": 25, "comments": 8},
            },
            "user": {"user_id": "user_trend", "username": "Debater"},
            "rules": _BASE_RULES,
            "history": [],
            "templates": _DEFAULT_TEMPLATES,
        },
        "expected_output": {
            "classification": "success",
            "rules_matched": 1,
            "actions_executed_count": 1,
            "action_types": ["create_feed_post"],
        },
        "tags": ["mvp", "theory", "feed"],
    },
    {
        "name": "cooldown VIPBot bloqueia spam",
        "input_payload": {
            "event": {
                "user_id": "user_vip",
                "event_name": "credits.low",
                "entity_type": "user",
                "entity_id": "user_vip",
                "metadata_json": {},
            },
            "user": {"user_id": "user_vip", "username": "LowCredits", "credits": 2},
            "rules": _BASE_RULES,
            "history": [
                {
                    "rule_id": "rule_credits_low",
                    "user_id": "user_vip",
                    "status": "success",
                    "created_at": "2026-07-02T10:00:00+00:00",
                }
            ],
            "templates": _DEFAULT_TEMPLATES,
        },
        "expected_output": {
            "classification": "blocked",
            "rules_matched": 0,
            "skipped_status": "rate_limited",
        },
        "tags": ["mvp", "anti-spam", "edge"],
    },
    {
        "name": "simulador admin modo teste",
        "input_payload": {
            "event": {
                "user_id": "user_sim",
                "event_name": "user.first_login",
                "entity_type": "user",
                "entity_id": "user_sim",
                "metadata_json": {},
                "source": "admin_simulator",
                "simulate": True,
            },
            "user": {
                "user_id": "user_sim",
                "username": "SimUser",
                "hasReceivedWelcome": False,
                "hasActiveMission": False,
                "profileCompleted": False,
                "credits": 0,
            },
            "rules": _BASE_RULES[:2],
            "history": [],
            "templates": _DEFAULT_TEMPLATES,
        },
        "expected_output": {
            "classification": "success",
            "rules_matched": 2,
            "actions_executed_count": 4,
            "all_simulated": True,
        },
        "tags": ["admin", "simulator"],
    },
    {
        "name": "evento invalido sem user_id",
        "input_payload": {
            "event": {
                "user_id": "",
                "event_name": "user.created",
                "metadata_json": {},
            },
            "user": {},
            "rules": _BASE_RULES,
            "history": [],
            "templates": _DEFAULT_TEMPLATES,
        },
        "expected_output": {"status": "invalid_event"},
        "tags": ["edge", "validation"],
    },
    {
        "name": "prioridade regras maior primeiro",
        "input_payload": {
            "event": {
                "user_id": "user_prio",
                "event_name": "user.first_login",
                "entity_type": "user",
                "entity_id": "user_prio",
                "metadata_json": {},
            },
            "user": {
                "user_id": "user_prio",
                "username": "PrioUser",
                "hasReceivedWelcome": False,
                "hasActiveMission": False,
                "profileCompleted": False,
                "credits": 0,
            },
            "rules": _BASE_RULES[:2],
            "history": [],
            "templates": _DEFAULT_TEMPLATES,
        },
        "expected_output": {
            "classification": "success",
            "first_executed_bot": "ViceBot",
        },
        "tags": ["priority"],
    },
    {
        "name": "contains badge ja existente bloqueia first_post",
        "input_payload": {
            "event": {
                "user_id": "user_has_badge",
                "event_name": "post.first_created",
                "entity_type": "post",
                "entity_id": "post_dup",
                "metadata_json": {"title": "Outro post"},
            },
            "user": {
                "user_id": "user_has_badge",
                "username": "Veteran",
                "badges": ["first_post"],
            },
            "rules": _BASE_RULES,
            "history": [],
            "templates": _DEFAULT_TEMPLATES,
        },
        "expected_output": {
            "classification": "blocked",
            "rules_matched": 0,
            "skipped_status": "condition_not_met",
        },
        "tags": ["edge", "badge"],
    },
    {
        "name": "todos logs gerados por regra",
        "input_payload": {
            "event": {
                "user_id": "user_logs",
                "event_name": "user.inactive_3_days",
                "entity_type": "user",
                "entity_id": "user_logs",
                "metadata_json": {"days_inactive": 5},
            },
            "user": {"user_id": "user_logs", "username": "LogUser"},
            "rules": _BASE_RULES,
            "history": [],
            "templates": _DEFAULT_TEMPLATES,
        },
        "expected_output": {
            "classification": "success",
            "min_bot_logs": 2,
        },
        "tags": ["logging"],
    },
    {
        "name": "tag oficial em todas acoes",
        "input_payload": {
            "event": {
                "user_id": "user_tag",
                "event_name": "theory.first_created",
                "entity_type": "theory",
                "entity_id": "theory_tag",
                "metadata_json": {"title": "Rumor do mapa"},
            },
            "user": {"user_id": "user_tag", "username": "TagUser", "credits": 0, "badges": []},
            "rules": _BASE_RULES,
            "history": [],
            "templates": _DEFAULT_TEMPLATES,
        },
        "expected_output": {
            "classification": "success",
            "official_tag": "BOT OFICIAL",
        },
        "tags": ["official", "branding"],
    },
    {
        "name": "pipeline theorist elegivel recebe bonus",
        "input_payload": {
            "event": {
                "user_id": "user_pipe",
                "event_name": "theory.first_created",
                "entity_type": "theory",
                "entity_id": "theory_pipe",
                "metadata_json": {"title": "Leonida volta?"},
            },
            "user": {
                "user_id": "user_pipe",
                "username": "Theorist",
                "engagementTier": "Theorist",
                "engagementScore": 65,
                "credits": 5,
                "badges": [],
            },
            "rules": _BASE_RULES,
            "history": [],
            "templates": _DEFAULT_TEMPLATES,
        },
        "expected_output": {
            "classification": "success",
            "rules_matched": 2,
            "actions_executed_count": 5,
            "action_types": [
                "send_notification",
                "give_badge",
                "give_credits",
                "assign_mission",
                "give_credits",
            ],
        },
        "tags": ["pipeline", "engagement", "theorist"],
    },
    {
        "name": "pipeline visitor sem bonus theorist",
        "input_payload": {
            "event": {
                "user_id": "user_visitor",
                "event_name": "theory.first_created",
                "entity_type": "theory",
                "entity_id": "theory_visitor",
                "metadata_json": {"title": "Primeira teoria"},
            },
            "user": {
                "user_id": "user_visitor",
                "username": "Visitor",
                "engagementTier": "Visitor",
                "engagementScore": 15,
                "credits": 0,
                "badges": [],
            },
            "rules": _BASE_RULES,
            "history": [],
            "templates": _DEFAULT_TEMPLATES,
        },
        "expected_output": {
            "classification": "success",
            "rules_matched": 1,
            "actions_executed_count": 3,
            "action_types": ["send_notification", "give_badge", "give_credits"],
        },
        "tags": ["pipeline", "engagement", "visitor"],
    },
]