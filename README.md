# APIForgeKit Studio

APIForgeKit Studio is a local-first harness for validating deterministic business logic before implementing it in Next.js.

V1 focuses on a Lead Algorithm Lab:

```txt
Docker PostgreSQL
↓
APIForgeKit Studio
↓
Lead Algorithm Lab
↓
Structured Logs
↓
Dashboard Visual
↓
Context Builder
↓
Next.js Blueprint
↓
Implementation with Prisma / Next.js
```

No LLM, external API, agent, voice, or vision is used in this MVP.

## Stack

- NiceGUI for the local Python interface
- Plotly and Pandas for interactive charts
- PostgreSQL via Docker
- SQLAlchemy 2.x with `psycopg`
- Pydantic Settings and python-dotenv for configuration
- Loguru for application logs
- Pytest for tests

## Quick Start

```bash
python -m pip install -r requirements.txt
copy .env.example .env
docker compose up -d
python app.py
```

Open:

```txt
http://localhost:8080
```

Optional npm helpers:

```bash
npm run db
npm run dev
npm run test
```

## Pages

- Dashboard: metrics, latest tests, classification donut, score histogram, leads by source, test evolution, score by channel.
- Lead Algorithm Lab: run deterministic scoring and persist the result.
- Logs: inspect history, filter/search, view full JSON, export CSV/JSONL.
- Context Builder: generate technical Markdown context for implementation agents.
- Next.js Blueprint: generate a Prisma/Next.js implementation blueprint without full code.
- Settings: database status and operational commands.

## Lead Score Rules

Strong keywords add 10 points each:

- comprar
- preço / preco
- orçamento / orcamento
- urgente
- hoje
- agora
- WhatsApp
- ligação / ligacao

Source:

- WhatsApp: +25
- Ligação: +30
- Landing Page: +20
- Instagram: +15
- LinkedIn: +10

Urgency:

- alta: +25
- média: +15
- baixa: +5

Interest:

- alto: +25
- médio: +15
- baixo: +5

Contact and history:

- phone: +10
- email: +5
- previous customer: +20

Penalties:

- empty message: `invalid_lead`
- spam pattern: `invalid_lead`
- no phone and no email: -20
- very short message: -10

Classification:

- 0-30: `cold_lead`
- 31-60: `warm_lead`
- 61-80: `hot_lead`
- 81-100: `urgent_lead`
- invalid input: `invalid_lead`

## PostgreSQL

Start local PostgreSQL:

```bash
docker compose up -d
```

The app creates the `lead_tests` table automatically on startup when the database is online.

If PostgreSQL is offline, the UI opens in degraded mode. Dashboard and Logs show offline status, and the Lead Lab blocks real execution until the database is available.

## Structured Logs

Every persisted test appends a JSONL record to:

```txt
logs/lead_tests.jsonl
```

The database remains the source of truth; JSONL is a local audit trail.

## Exports

Generated context files are written to:

```txt
exports/contexts/
```

Generated Next.js blueprints are written to:

```txt
exports/blueprints/
```

Logs page exports are written to:

```txt
exports/logs/
```

## Tests

```bash
python -m pytest -q
```

The test suite covers:

- scoring rules
- invalid/spam cases
- penalties
- classification boundaries
- JSONL logging
- SQLAlchemy repository behavior
- Context Builder output
- Blueprint Generator output
- legacy provider lab contract tests

## Legacy Provider Lab

The original API Builder Lab is preserved for future provider validation. It is separate from Studio V1 and uses `requirements-legacy.txt`.

See:

```txt
legacy/README.md
run_lab.py
labs/
providers.md
workflow.md
```
