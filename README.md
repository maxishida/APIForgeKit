# APIForgeKit Studio

APIForgeKit Studio is a local-first observability lab for validating AI APIs with real tests, structured logs and reusable technical context.

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

The Lead Algorithm Lab still exists, but the current V1 focus is live observability, xAI validation, reports and context building.

## Stack

- NiceGUI for the local Python interface
- Plotly and Pandas for interactive charts
- PostgreSQL via Docker
- SQLAlchemy 2.x with `psycopg`
- `xai-sdk` for real xAI validation
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
npm run dev
npm run test
```

## xAI Key

Set the key only in `.env`:

```txt
XAI_API_KEY=
XAI_MODEL=grok-4.3
```

Never commit `.env` or raw provider outputs with secrets.

## Pages

- Live Dashboard: real-time test metrics, event stream, charts, filters and xAI compact runner.
- Lead Algorithm Lab: deterministic local lead-score module preserved from the first MVP.
- Logs: observability event table with filters, search, JSON detail and CSV/JSONL export.
- Context Builder: converts real events into technical context and exports reports.
- Blueprint Archive: legacy future-implementation reference, not the current focus.
- Settings: database status and operational commands.

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

If PostgreSQL is offline, the UI opens in degraded mode and live runs are blocked until the database returns.

## Live xAI Runner

From the Live Dashboard, click:

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

## Legacy Lead Logs

Lead Algorithm Lab still writes a JSONL audit trail to:

```txt
logs/lead_tests.jsonl
```

The live xAI observability flow uses PostgreSQL as the source of truth.

## Documentation

Start here before adding provider features:

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
- xAI live runner missing-key behavior
- legacy provider lab contract tests

## Legacy Provider Lab

The original CLI provider lab is preserved:

```bash
python -m pip install -r requirements-legacy.txt
python run_lab.py --status
```

It remains useful for isolated provider checks, but the Studio UI is now the primary observability surface.
