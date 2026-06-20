---
name: apiforgekit-operational-brain
version: 1
description: Use when an agent operates APIForgeKit to validate APIs, algorithms, token cost, logs, evidence, Context Builder exports or ACP commands before suggesting implementation.
---

# APIForgeKit Operational Brain
Short execution contract for ACP and human agents. Keep details in `docs/`.

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
| Voice lead/contact validation | xAI Voice Lab REST |
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
- `protocol_trace`: ACP/CLI/IDE trace of gate, command, response and permission path
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
8. Treat final `PromptResponse` as stop metadata; risky prompts emit `session/request_permission` then `stopReason=refusal` (continuation disabled; use UI/CLI); ACP traces persist as `protocol_trace` with the `SKILL.md` version/SHA-256.

Quick local harness:

```bash
python run_acp_prompt.py "/validate-lead-score"
python run_acp_prompt.py "/build-context"
python run_acp_prompt.py "/validate-token-cost provider=xai model=grok-4.3 users=10 requests=20"
python run_acp_prompt.py "/validate-context-readiness"
python run_acp_prompt.py "/validate-voice-roundtrip"
```

Implemented commands:

```txt
/validate-lead-score
/validate-algorithm lead_score
/validate-api-suite whatsapp_validation_pack
/validate-token-cost provider=xai model=grok-4.3 users=10 requests=20
/token-cost provider=xai model=grok-4.3 users=10 requests=20
/validate-context-readiness
/validate-voice-roundtrip
/build-context
/export-evidence
```

ACP limitations:

- v1-only: return `protocolVersion=1`.
- Accept text `ContentBlock[]`; keep legacy string prompt support.
- Refuse image/audio/resource blocks until a specific resource validation path exists.
- For real HTTP/provider-paid paths, emit `session/request_permission` and return `stopReason="refusal"`.
- Full result JSON belongs in `agent_message_chunk`; `_meta` includes session, command, run ID, context path and evidence ZIP when available.

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
- use `docs_verified` only after checking official pricing docs and entering verified prices
- never present seeded pricing as billing truth
- include source URL and verification timestamp when `docs_verified`
- ACP `/token-cost` calculates without saving; add `save=true` only for PostgreSQL evidence
- ACP `/validate-token-cost` is the preferred validation alias; `/token-cost` remains compatible
- recommend Context Builder to shrink prompts before implementation

Provider pricing docs: xAI https://docs.x.ai/developers/pricing; OpenAI https://platform.openai.com/docs/pricing; Anthropic https://docs.anthropic.com/en/docs/about-claude/pricing; Gemini https://ai.google.dev/gemini-api/docs/pricing.

## Provider Validation

For provider behavior, use official docs when endpoints, models, pricing or limits may have changed. Start small, log sanitized evidence and never print secrets.

xAI default: check current docs; prefer Responses API (`/v1/responses`); keep Chat Completions as `chat_legacy`; log response id, output preview, usage/tokens, endpoint, latency and docs source; use `store=false` unless state is tested. Official refs: https://docs.x.ai/developers/model-capabilities/text/comparison, https://docs.x.ai/developers/model-capabilities/text/generate-text, https://docs.x.ai/developers/model-capabilities/text/structured-outputs, https://docs.x.ai/developers/model-capabilities/text/streaming.

xAI details live in `docs/XAI_TEST_PLAN.md`; ACP details live in `docs/ACP_AGENT_ARCHITECTURE.md`.

## Voice Validation Path

Use `/voice-lab` or `npm run voice:run` for approved xAI REST voice validation. Log lead, user message, TTS, STT, agent response, API error, latency, origin and previous page as `real_http`. Realtime WebSocket, private audio and benchmarks require approval.

ACP `/validate-voice-roundtrip` validates the latest saved voice evidence only, including required events `lead_received`, `user_message_received`, `tts_audio_received`, `transcript_received`, `agent_response_received` and `voice_call_completed`. ACP `/validate-voice-roundtrip --run-real` must request permission and refuse by default until the client permission flow approves paid provider execution.

## Context Builder Gate

Before implementation, Context Builder must say `Ready` or the missing evidence/failures must be explicit.

Use ACP `/validate-context-readiness` to verify this gate from IDE/CLI before handing context to another AI.

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

Use `Generate AI Prompt` for the final handoff to another AI. That prompt must be short, evidence-bounded and say not to invent payloads, rules or endpoints.

## Stop Conditions

Stop or request permission when real output is missing, PostgreSQL is offline for a persisted run, credentials/fixtures are missing, cost may be generated, docs conflict with observed behavior, pricing docs cannot be verified for a financial decision, voice/audio/private data lacks approval, or implementation is requested before context exists.

## Safety

- Never hardcode or print API keys.
- Never commit `.env`, provider raw outputs, private audio or secrets.
- Prefer small validations over broad exploratory calls.
- Record failures as evidence.
- Keep generated artifacts in ignored `exports/` unless the user asks otherwise.

## Reference Docs

Use `docs/SUMMARY.md` and `docs/MVP_100_PERCENT_MAP.md` for docs. Obsidian: sync then read `00 - Retomar Agora.md` and `00 - Mapa do Projeto.md`; preserve non-generated vault text. See `docs/OBSIDIAN_CONTEXT_BRAIN.md`.
