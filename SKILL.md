---
name: apiforgekit-operational-brain
description: Use when an agent operates APIForgeKit to validate APIs, algorithms, token cost, logs, evidence, Context Builder exports or ACP commands before suggesting implementation.
---

# APIForgeKit Operational Brain

Use this file as the short execution contract for ACP and human-driven agents. Keep detailed explanations in `docs/`; keep this skill small enough to load in prompt context.

## Prime Directive

No implementation without evidence.

Official flow:

```txt
Test -> Structured Log -> PostgreSQL -> Dashboard -> Context Builder -> Evidence Pack -> Implementation later
```

If evidence is missing, answer:

```txt
Ainda nao validado pelo APIForgeKit. Proximo passo: executar teste/log/contexto antes de implementar.
```

## Decision Gates

1. Classify the request.
2. Execute the smallest relevant validation.
3. Persist structured evidence.
4. Build or reference Context Builder output.
5. Only then recommend implementation work.

Route by intent:

| Intent | Required path |
| --- | --- |
| Deterministic scoring or business logic | Algorithm Test Lab |
| API, webhook or SaaS payload | Generic API Lab |
| xAI/OpenAI/Gemini/Anthropic behavior | Provider validation |
| Cost, token usage or price per user | Token Calculator |
| Implementation request | Context Builder first |
| IDE/client protocol | ACP Execution Contract |

## Evidence Contract

Every validated test must have:

- input/request payload, sanitized
- expected output when applicable
- actual output/response
- status and latency
- error if failed
- recommendation
- context/export path when generated
- `evidence_mode`

Evidence modes:

- `real_http`: real external/local HTTP or SDK call
- `dry_run_contract`: local contract validation with expected vs actual
- `seed_validation`: canonical deterministic seed suite
- `blocked`: not executed because permission, credential, cost, fixture or V2 scope is missing
- `legacy`: preserved feature outside the canonical MVP

Never hide dry-run or seed evidence as real production behavior.

## ACP Execution Contract

ACP is a protocol layer around the same labs; it must not bypass evidence gates or generate product code.

Handshake for IDE/CLI clients:

1. Start PostgreSQL: `npm run db`.
2. Start ACP stdio subprocess: `npm run acp`.
3. Send `initialize`.
4. Send `session/new` with absolute `cwd`.
5. Read `available_commands_update`; command names are announced without `/`.
6. Send `session/prompt` with text `ContentBlock[]`.
7. Read `session/update` notifications for `plan`, `tool_call`, `tool_call_update` and `agent_message_chunk`.
8. Treat final `PromptResponse` as stop metadata and `_meta` paths only.

Quick local harness:

```bash
python run_acp_prompt.py "/validate-lead-score"
python run_acp_prompt.py "/build-context"
python run_acp_prompt.py "/token-cost provider=xai model=grok-4.3 users=10 requests=20"
```

Implemented commands:

```txt
/validate-lead-score
/validate-algorithm lead_score
/validate-api-suite whatsapp_validation_pack
/token-cost provider=xai model=grok-4.3 users=10 requests=20
/build-context
/export-evidence
```

ACP limitations:

- v1-only: return `protocolVersion=1`.
- Accept text `ContentBlock[]`; keep legacy string prompt support.
- Refuse image/audio/resource blocks until a specific resource validation path exists.
- For real HTTP/provider-paid paths, emit `session/request_permission` and return `stopReason="refusal"`.
- Full result JSON belongs in `agent_message_chunk`; `_meta` should include session, command, run ID, context path and evidence ZIP when available.

## Algorithm Path

Use `Algorithm Test Lab` for deterministic logic. `lead_score` is the canonical MVP algorithm.

Required behavior:

- run canonical suite before implementation
- compare expected vs actual
- fail on mismatch, not warn
- persist run/results in PostgreSQL
- export context/evidence pack
- classify score without LLM involvement

Lead score invariants:

- payload validated
- deterministic output for same input
- score clamped 0-100
- invalid status overrides score classification
- reasons include contributions and penalties

Prefer `/validate-lead-score` through ACP for lead qualification work.

## API Path

Use `Generic API Lab` for APIs, webhooks and SaaS contracts.

Rules:

- prefer `dry_run_contract` until credentials and cost are clear
- require explicit permission for `real_http`
- redact secrets before logs
- compare expected status/body against actual response
- store request, response, diff, error and recommendation

## Token Economy Path

Use Token Calculator when the user asks about price, usage, monthly cost or cost per user.

Rules:

- record `pricing_mode`
- use `seeded_estimate` for local catalog estimates
- use `docs_verified` only after checking current official pricing docs
- never present seeded pricing as billing truth
- include source URL and verification timestamp when `docs_verified`
- recommend Context Builder to shrink prompts before implementation

Provider pricing docs:

- xAI: https://docs.x.ai/developers/models
- OpenAI: https://platform.openai.com/docs/pricing
- Anthropic: https://docs.anthropic.com/en/docs/about-claude/pricing
- Gemini: https://ai.google.dev/gemini-api/docs/pricing

## Provider Validation

For provider behavior, use official docs when the endpoint, model, pricing or limits may have changed. Start with the smallest safe test and log all request/response evidence. Do not print secrets.

xAI references live in `docs/XAI_TEST_PLAN.md`; ACP architecture details live in `docs/ACP_AGENT_ARCHITECTURE.md`.

## Context Builder Gate

Before implementation, Context Builder must say `Ready` or the missing evidence/failures must be explicit.

Modes:

- `Algorithm only`
- `API only`
- `Algorithm + API`
- `Full evidence`

Readiness:

- `Ready`: enough evidence exists
- `Needs tests`: required evidence is missing
- `Has failures`: diffs/errors must be fixed or documented

Exports should include Markdown, JSON, HTML and ZIP when requested.

## Stop Conditions

Stop or request permission when:

- no real output exists
- PostgreSQL is offline for a run that must persist
- credentials or fixtures are missing
- a call may generate cost
- docs conflict with observed behavior
- pricing docs cannot be verified for a financial decision
- voice/audio/private data is involved without approval
- user asks for implementation before context exists

## Safety

- Never hardcode or print API keys.
- Never commit `.env`, provider raw outputs, private audio or secrets.
- Prefer small validations over broad exploratory calls.
- Record failures as evidence.
- Keep generated artifacts in ignored `exports/` unless the user asks otherwise.

## Reference Docs

- MVP map: `docs/MVP_100_PERCENT_MAP.md`
- MVP checklist: `docs/MVP_100_PERCENT_CHECKLIST.md`
- Feature test report: `docs/MVP_FEATURE_TEST_REPORT.md`
- User tutorial: `docs/OPEN_SOURCE_TUTORIAL.md`
- Algorithm plan: `docs/ALGORITHM_TEST_PLAN.md`
- ACP details: `docs/ACP_AGENT_ARCHITECTURE.md`
- Architecture: `docs/architecture.md`
