# Community Bot Engine / Vice City NPC Engine

Motor determinístico de bots oficiais validado no **Algorithm Test Lab** como `community_bot_engine`.

## Objetivo do produto

Manter a comunidade viva com **mini conteúdo** (notificações, missões, posts, badges, créditos) **sem IA no MVP**:

```txt
User Action → Event → member_engagement_score → Bot Rules Engine → Conditions → Actions → Logs
```

Frase do produto:

> Os NPCs oficiais mantêm Vice City viva enquanto a comunidade cresce.

Bots oficiais (tag obrigatória: `BOT OFICIAL` / `SISTEMA` / `IA DESATIVADA NO MVP`):

- ViceBot, MissionBot, TheoryBot, NewsBot, ModBot, VIPBot

## Status no APIForgeKit

| Campo | Valor |
| --- | --- |
| Algoritmo | `community_bot_engine` |
| Evidence mode | `seed_validation` |
| Casos seed | 17/17 (inclui 2 casos cross-pipeline com `engagementTier`) |
| Pipeline | `member_engagement_score` + `community_bot_engine` |
| UI | `/community-bot-lab` |
| Código | `core/community_bot_engine.py` |
| Casos | `core/community_bot_seed.py` |
| Readiness | `Ready` após suíte passed |

## Como testar na UI

```bash
npm run db
npm run dev
# ou: powershell -File scripts/run_dev_docker.ps1
```

Abra:

```txt
http://localhost:8080/community-bot-lab
```

Na página:

1. Escolha um cenário MVP no dropdown
2. **Executar sandbox** — teste rápido com JSON editável
3. **Rodar suíte 17/17** — validação canônica do Bot Engine
4. **Rodar pipeline completa** — valida `member_engagement_score` + `community_bot_engine`
5. **Export Evidence Pack** — ZIP para handoff à IDE

## Como testar via CLI

```bash
npm run db
npm run community:pipeline   # recomendado: valida score + bot + exporta handoff
python scripts/run_community_bot_suite.py
```

Ou:

```bash
python run_algorithm_lab.py --suite community_bot_engine --export
```

## Download do contexto de implementação

Após export, os arquivos ficam em `exports/reports/` (gitignored). Com o Studio rodando:

```txt
http://localhost:8080/download/reports/CODE_GTA6_COMMUNITY_PIPELINE_IMPLEMENTATION_CONTEXT.md
http://localhost:8080/download/reports/CODE_GTA6_COMMUNITY_BOT_ENGINE_IMPLEMENTATION_CONTEXT.md
http://localhost:8080/download/reports/community_pipeline_context.md
http://localhost:8080/download/reports/community_bot_engine_context.md
http://localhost:8080/download/reports/community_bot_engine.json
http://localhost:8080/download/reports/member_engagement_score.json
```

**Context Builder:** selecione modo **Community Pipeline** em `/context-builder`.

Gere o pacote completo com **Export Evidence Pack** na UI ou `run_community_bot_suite.py`.

## Pipeline validado

1. Registrar `user_behavior_events`
2. Buscar `bot_rules` ativas por `event_name`, ordenar por `priority` DESC
3. Para cada regra: `checkRuleSafety` → `evaluateConditions` → `executeActions` → `logBotAction`
4. Classificação: `success`, `partial`, `blocked`, `invalid`

### Operadores de condição

```txt
equals | not_equals | greater_than | less_than | exists | not_exists | contains | not_contains
```

### Ações MVP

```txt
send_notification | send_popup | create_feed_post | give_credits | give_badge
add_ranking_points | recommend_page | assign_mission
```

### Anti-spam

- `run_once_per_user` → `duplicate_blocked`
- `cooldown_minutes` → `rate_limited`
- `unique_event_key` → `{userId}:{eventName}:{ruleId}`

## Fluxos MVP (17 casos seed)

| Fluxo | Evento | Resultado validado |
| --- | --- | --- |
| Primeiro login | `user.first_login` | ViceBot + MissionBot + 10 créditos |
| Boas-vindas duplicada | `user.first_login` | `duplicate_blocked` |
| Primeiro post | `post.first_created` | Badge + ranking + notificação |
| Primeira teoria | `theory.first_created` | Badge + 15 créditos |
| Créditos baixos | `credits.low` | VIPBot + `/vip` |
| Créditos ok | `credits.low` | `condition_not_met` |
| Usuário inativo | `user.inactive_3_days` | Retorno + recommend page |
| Teoria trending | `theory.trending` | Post automático no feed |
| Cooldown VIP | `credits.low` | `rate_limited` |
| Simulador admin | `simulate: true` | Ações com `simulated: true` |
| Theorist elegível | `theory.first_created` + `engagementTier: Theorist` | Badge + missão avançada + créditos |
| Visitor sem bônus | `theory.first_created` + `engagementTier: Visitor` | Apenas badge primeira teoria |

## Handoff para IDE (Code GTA6 Community)

1. Rode `npm run community:pipeline` até `Ready`
2. Baixe `CODE_GTA6_COMMUNITY_PIPELINE_IMPLEMENTATION_CONTEXT.md`
3. Cole na IDE com: *implemente só o validado; reproduza os casos seed como testes unitários*
4. Não inventar payloads, regras ou endpoints fora da evidência

## Arquivos sugeridos no projeto destino

```txt
/lib/community-bot-engine.ts
/lib/bot-rules-engine.ts
/services/event-tracking.service.ts
/app/api/events/track/route.ts
/app/admin/bots/page.tsx
/prisma/schema.prisma
/tests/community-bot-engine.test.ts
```

## Não implementar no MVP

```txt
IA generativa | Chatbot conversacional | Discord bot | Machine learning
```

## Referência

- `docs/ALGORITHM_TEST_PLAN.md` — padrão de validação de algoritmos
- `core/community_bot_engine.py` — implementação de referência Python
- `tests/test_community_bot_engine.py` — testes unitários