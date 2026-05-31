---
name: apiforgekit-operational-brain
description: Use when an agent works in APIForgeKit and needs to validate APIs or algorithms, collect evidence, reduce LLM token waste, operate live logs, build reports, or prepare implementation context without guessing behavior.
---

# APIForgeKit Operational Brain

APIForgeKit exists to turn uncertain API or algorithm behavior into observable evidence before any product implementation.

The repo should teach a simple open source idea: a small local test lab can save LLM tokens for developers by replacing long speculative chats with compact validated context.

Primary flow:

```txt
Teste Real
↓
Logs Estruturados
↓
Evidências
↓
Contexto Técnico
↓
Implementação futura
```

Do not jump directly to app code. First run a focused test, collect logs, inspect evidence, build context, and only then recommend implementation work.

The user-facing promise is:

```txt
Insert API or algorithm into the harness
↓
Run validation
↓
Get JSON behavior evidence
↓
Generate AI-ready context
↓
Build the SaaS with fewer assumptions
```

## Core Rule

No implementation without evidence.

Evidence means:

- command or UI action executed
- sanitized input payload
- sanitized output payload
- status
- latency
- provider, model, endpoint or SDK path
- token/cost metadata when available
- error details when failed
- recommendation

## Token Economy Rule

Use the lab to shrink prompts before asking a LLM to implement.

Do:

1. Run the smallest real test.
2. Save structured JSON.
3. Generate context.
4. Give the LLM the context, not the whole debugging story.

Avoid:

- pasting full docs when a validated payload is enough
- asking a LLM to guess API behavior
- repeating failed attempts without structured logs
- implementing before expected-vs-actual behavior is known

Good implementation prompt:

```txt
Use este contexto técnico validado pelo APIForgeKit.
Implemente somente a lógica confirmada pelos testes.
Não invente endpoints, payloads ou regras.
```

## Current Product Focus

The current APIForgeKit Studio focus is observability for APIs and algorithms:

- live dashboard
- real-time event stream
- structured PostgreSQL logs
- request/response evidence
- xAI test runner
- Algorithm Test Lab for deterministic Python logic
- Context Builder from real logs
- Markdown, JSON and HTML reports

Algorithm Test Lab now validates `lead_score` with seed cases, expected output validation and structured PostgreSQL results. Future harnesses should support WhatsApp APIs, webhooks, local algorithms and site/API endpoints using the same evidence pattern.

## Operating Modes

### 1. Live Observability Mode

Use the NiceGUI Studio to run and inspect live provider tests.

```bash
npm run db
python app.py
```

Open `http://localhost:8080`, then use Live Dashboard -> Executar xAI Compact.

This path writes to PostgreSQL tables:

- `test_runs`
- `test_events`
- `api_requests`
- `api_responses`
- `voice_tests`
- `agent_tests`
- `context_exports`

### 2. Provider Validation Mode

Use for direct API/provider exploration, especially xAI.

The agent must:

1. Read current official provider docs when the endpoint is new, changed, or failing.
2. Verify local readiness without printing secrets.
3. Run the smallest focused real test possible.
4. Persist structured logs and request/response evidence.
5. Generate context and reports.
6. Stop before implementation unless the user explicitly approves a later build phase.

Legacy compact runner remains available:

```bash
python run_lab.py --provider xai --case auth
python run_lab.py --provider xai --case basic
python run_lab.py --provider xai --case stream
python run_lab.py --provider xai --case tools
```

### 3. Algorithm Validation Mode

Use when validating a business algorithm before turning it into a SaaS feature.

Examples:

- lead score
- WhatsApp lead qualification
- ticket classification
- spam detection
- recommendation logic
- pricing or eligibility rules

The agent must:

1. Define the algorithm objective in plain language.
2. Define required inputs and expected outputs.
3. Create manual cases first.
4. Compare expected output with actual output.
5. Save JSON evidence.
6. Generate context that explains the behavior to an implementation AI.

Preferred output:

```json
{
  "case_id": "uuid",
  "algorithm": "lead_score",
  "status": "passed",
  "input": {},
  "expected": {},
  "actual": {},
  "diff": {},
  "latency_ms": 0,
  "recommendation": ""
}
```

Open source tutorial:

```txt
README.md -> OPEN_SOURCE_TUTORIAL.md -> Algorithm Test Lab -> Context Builder
```

## xAI Validation Priority

Use official xAI docs as source of truth:

- Overview: https://docs.x.ai/overview
- Text / Responses: https://docs.x.ai/developers/model-capabilities/text/generate-text
- Structured Outputs: https://docs.x.ai/developers/model-capabilities/text/structured-outputs
- Streaming: https://docs.x.ai/developers/model-capabilities/text/streaming
- Function Calling: https://docs.x.ai/developers/tools/function-calling
- Multi Agent: https://docs.x.ai/developers/model-capabilities/text/multi-agent
- Voice: https://docs.x.ai/developers/model-capabilities/audio/voice
- Speech to Text: https://docs.x.ai/developers/model-capabilities/audio/speech-to-text
- Models: https://docs.x.ai/developers/rest-api-reference/inference/models
- Rate Limits: https://docs.x.ai/developers/rate-limits
- Debugging: https://docs.x.ai/developers/debugging

Current practical stance:

- Prefer Responses API concepts for future integrations, but use `xai-sdk` where it gives cleaner Python validation.
- Validate structured outputs with schemas before trusting parser behavior.
- Capture streaming chunks, first-chunk latency and final response shape.
- Treat Multi Agent as beta and record additional cost/latency risk.
- Treat Voice as a separate validation track with explicit budget, audio fixtures and privacy rules.

## Structured Event Contract

Every live test event should follow this shape:

```json
{
  "event_id": "uuid",
  "timestamp": "",
  "provider": "xai",
  "module": "",
  "test_name": "",
  "status": "running | success | failed | blocked",
  "latency_ms": 0,
  "tokens": {},
  "cost": 0,
  "request": {},
  "response": {},
  "error": null,
  "recommendation": ""
}
```

Never log full API keys, bearer tokens, private audio, raw private transcripts or user secrets. If an artifact is sensitive, log metadata and a local artifact path instead.

## Context Builder Contract

After each test sequence, generate context containing:

- what was tested
- what worked
- what failed
- correct payloads
- response shapes
- expected vs actual behavior for algorithms
- latency and reliability observations
- token/cost observations
- limitations discovered
- recommendations
- implementation blockers

## Report Contract

Reports export to:

- Markdown
- JSON
- HTML

Each report should include:

- executive summary
- metrics
- errors
- evidence references
- recommendations
- implementation impact for a future phase

## Stop Conditions

Stop and ask before continuing when:

- no real output exists
- `XAI_API_KEY` is missing
- PostgreSQL is offline for live runs
- docs conflict with observed behavior
- voice tests require real or private audio not approved by the user
- a test may generate meaningful cost
- rate limit or account permission blocks validation

## Safety Rules

- Never hardcode API keys.
- Never print complete secrets.
- Never commit `.env`, provider outputs, audio samples or sensitive responses.
- Use official docs over memory.
- Prefer small tests over broad exploratory calls.
- Record failures as evidence instead of hiding them.

## Response Template After Validation

```txt
Provider:
Phase:
Test:
Action:
Report:
Status:
Model or endpoint:
Latency:
Tokens/cost:
Finding:
Failure mode:
Evidence:
Next action:
```
