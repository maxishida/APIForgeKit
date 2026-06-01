# APIForgeKit Studio

APIForgeKit Studio is a local-first observability lab for validating APIs, webhooks and algorithms with real tests, structured logs, token/cost estimates and reusable technical context.

Current operating principle:

```txt
Teste Python
↓
API xAI
↓
Resposta
↓
Log Estruturado
↓
PostgreSQL
↓
Dashboard Live
↓
Context Builder
```

The product goal is evidence before implementation:

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

The Lead Algorithm Lab still exists, but the current V1 focus is observability, generic API validation, algorithm validation, token economy, reports and context building.

The long-term product idea is simple: the user inserts an API, webhook, SaaS integration or algorithm into the harness, runs tests, receives JSON evidence, and gives that context to an AI before building the final SaaS.

This saves LLM tokens because the AI receives a compact evidence report instead of a long trial-and-error conversation with copied docs, screenshots and uncertain assumptions.

Examples:

- xAI API behavior validation.
- WhatsApp API payload and webhook validation.
- Lead scoring algorithm validation.
- Any site/API endpoint that returns a decision, classification, score or recommendation.
- Token and cost planning by provider/model/user volume.

## Stack

- NiceGUI for the local Python interface
- Plotly and Pandas for interactive charts
- PostgreSQL via Docker
- SQLAlchemy 2.x with `psycopg`
- `xai-sdk` for real xAI validation
- Alembic for optional versioned PostgreSQL migrations
- Pydantic Settings and python-dotenv for configuration
- Loguru for application logs
- Pytest for tests

## Quick Start

```bash
python -m pip install -r requirements.txt
copy .env.example .env
npm run db
python app.py
```

Open:

```txt
http://localhost:8080
```

Optional npm helpers:

```bash
npm run db
npm run db:logs
npm run db:reset
npm run db:migrate
npm run dev
npm run test
npm run algorithm:suite
```

## 5 Minute Tutorial

1. Start PostgreSQL with `npm run db`.
2. Run `python app.py`.
3. Open `http://localhost:8080`.
4. Click `Run Full Demo`.
5. Inspect `Algorithm Test Lab` and `Generic API Lab`.
6. Open `Token Calculator` to estimate cost per user.
7. Open `Context Builder`.
8. Copy the generated context into your LLM before asking for implementation.

Short prompt:

```txt
Use este contexto técnico validado pelo APIForgeKit.
Implemente somente a lógica confirmada pelos testes.
Não invente endpoints, payloads ou regras.
```

## xAI Key

Set the key only in `.env`:

```txt
XAI_API_KEY=
XAI_MODEL=grok-4.3
```

Never commit `.env` or raw provider outputs with secrets.

## Pages

- Home: clean demo dashboard with quick actions for the two main tracks.
- API Provider Lab: real-time test metrics, event stream, charts, filters and xAI compact runner.
- Generic API Lab: HTTP or dry-run contract testing for APIs, webhooks and WhatsApp-style payloads.
- Algorithm Test Lab: deterministic Python algorithm validation with expected-vs-actual diff.
- Token Calculator: provider/model cost projection per user, request volume and context savings.
- Lead Algorithm Lab: deterministic local lead-score module preserved from the first MVP.
- Logs: observability event table with filters, search, JSON detail and CSV/JSONL export.
- Context Builder: converts real events into technical context and exports reports.
- Tutorial: in-app open source tutorial for saving LLM tokens with the lab.
- Blueprint Archive: legacy future-implementation reference, not the current focus.
- Settings: database status and operational commands.

## How The Harness Works

Any future API or algorithm should follow the same contract:

```txt
Input
↓
Runner
↓
Request or function call
↓
Response
↓
Structured JSON event
↓
PostgreSQL
↓
Dashboard + Context Builder
```

For an API, the runner records method, URL/SDK path, sanitized headers, payload, status, latency, response and error.

For an algorithm, the runner records input, expected output, actual output, diff, status, latency and recommendation.

That means a WhatsApp integration, a custom lead score endpoint, or a local Python algorithm can all produce context for the same dashboard and report system.

## PostgreSQL Tables

The app creates tables automatically on startup when PostgreSQL is online:

- `lead_tests`
- `test_runs`
- `test_events`
- `api_requests`
- `api_responses`
- `voice_tests`
- `agent_tests`
- `context_exports`
- `algorithm_definitions`
- `algorithm_test_cases`
- `algorithm_test_runs`
- `algorithm_test_results`
- `api_test_suites`
- `api_test_cases`
- `api_test_runs`
- `api_test_results`
- `token_usage_estimates`

If PostgreSQL is offline, the UI opens in degraded mode and live runs are blocked until the database returns.

## Live xAI Runner

Open:

```txt
http://localhost:8080/live-dashboard
```

Then click:

```txt
Executar xAI Compact
```

The compact sequence currently validates:

- connectivity/auth
- basic chat
- structured outputs with Pydantic schema parsing
- streaming chunks
- function calling loop
- blocked placeholders for Agents and Voice until dedicated fixtures/budget exist

Every event is persisted in PostgreSQL and appears in the Live Event Stream.

## Algorithm Test Lab

Open:

```txt
http://localhost:8080/algorithm-test-lab
```

The flow is:

```txt
Test Case
↓
Algorithm Runner
↓
Expected Output Validator
↓
Structured Log
↓
PostgreSQL
↓
Dashboard
↓
Context Builder
```

The first registered algorithm is `lead_score`.

The lab supports:

- selecting an algorithm
- creating a test case
- defining input JSON
- defining expected output JSON
- running one test
- running the full suite
- viewing passed/failed status
- viewing expected-vs-actual diff
- saving structured logs in PostgreSQL
- generating technical context for AI

Seed cases:

1. lead frio Instagram
2. lead morno Landing Page
3. lead quente WhatsApp
4. lead urgente ligação
5. lead inválido mensagem vazia
6. lead spam
7. lead sem contato
8. cliente anterior com alta intenção

No LLM is used. The lab validates pure deterministic Python logic.

CLI:

```bash
npm run algorithm:suite
```

This runs the `lead_score` suite and exports context/suite JSON to `exports/reports/`.

## Generic API Lab

Open:

```txt
http://localhost:8080/api-test-lab
```

Use it to validate APIs, webhooks and payload contracts before building an integration.

The seed suite is `whatsapp_validation_pack`, a dry-run pack for:

- valid outbound text payload
- lead intent webhook payload
- missing phone contract failure
- spam-like payload classification

Each result stores request, sanitized headers, response, diff, status, latency and recommendation in PostgreSQL.

Suites can be exported/imported as JSON so examples can live in GitHub and be reused by other users.

## Token Calculator

Open:

```txt
http://localhost:8080/token-calculator
```

Use it to estimate:

- cost per request
- cost per user
- monthly/projected cost
- raw prompt vs structured context savings

Pricing seeds include doc links for:

- xAI: https://docs.x.ai/developers/models
- OpenAI: https://platform.openai.com/docs/pricing
- Anthropic: https://docs.anthropic.com/en/docs/about-claude/pricing
- Gemini: https://ai.google.dev/gemini-api/docs/pricing

Always check official pricing before making a financial decision. The calculator is a planning harness, not billing truth.

## Reports

The Context Builder and Live Dashboard export reports to:

```txt
exports/reports/
```

Formats:

- Markdown
- JSON
- HTML

Reports are generated from real runs and events, not from assumptions.

Context Builder also exports a ZIP bundle with Markdown, JSON and HTML.

## Legacy Lead Logs

Lead Algorithm Lab still writes a JSONL audit trail to:

```txt
logs/lead_tests.jsonl
```

The live xAI observability flow uses PostgreSQL as the source of truth.

## Documentation

Start here before adding provider features:

- [USER_GUIDE.md](./USER_GUIDE.md): simple explanation of how the tool works for users.
- [OPEN_SOURCE_TUTORIAL.md](./OPEN_SOURCE_TUTORIAL.md): GitHub/open source usage flow focused on saving LLM tokens.
- [ALGORITHM_TEST_PLAN.md](./ALGORITHM_TEST_PLAN.md): plan for validating algorithms through forms, sites or APIs.
- [SKILL.md](./SKILL.md): operational brain for evidence-first APIForgeKit work.
- [workflow.md](./workflow.md): validation workflow.
- [architecture.md](./architecture.md): current Studio architecture.
- [providers.md](./providers.md): provider documentation index.
- [XAI_TEST_PLAN.md](./XAI_TEST_PLAN.md): phased xAI validation plan.
- [VALIDATION_CHECKLIST.md](./VALIDATION_CHECKLIST.md): checklist for real API validation.

Official xAI docs reviewed for this track:

- https://docs.x.ai/overview
- https://docs.x.ai/developers/model-capabilities/text/generate-text
- https://docs.x.ai/developers/model-capabilities/text/structured-outputs
- https://docs.x.ai/developers/model-capabilities/text/streaming
- https://docs.x.ai/developers/tools/function-calling
- https://docs.x.ai/developers/model-capabilities/text/multi-agent
- https://docs.x.ai/developers/model-capabilities/audio/voice
- https://docs.x.ai/developers/model-capabilities/audio/speech-to-text
- https://docs.x.ai/developers/rest-api-reference/inference/models
- https://docs.x.ai/developers/rate-limits
- https://docs.x.ai/developers/debugging

## Tests

```bash
python -m pytest -q
```

The test suite covers:

- lead scoring rules
- JSONL logging
- SQLAlchemy repository behavior
- Context Builder output
- Blueprint Generator output
- observability repository, metrics and report exports
- Algorithm Test Lab repository, runner, diff validator and context export
- Generic API Lab repository, dry-run runner, diff validator, WhatsApp pack and suite import/export
- Token Calculator cost projection, context savings and persistence
- Demo Mode
- report bundle ZIP export
- Algorithm CLI parser
- xAI live runner missing-key behavior
- legacy provider lab contract tests

## Legacy Provider Lab

The original CLI provider lab is preserved:

```bash
python -m pip install -r requirements-legacy.txt
python run_lab.py --status
```

It remains useful for isolated provider checks, but the Studio UI is now the primary observability surface.
