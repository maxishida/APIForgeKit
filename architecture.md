# APIForgeKit Architecture

## Product Intent

APIForgeKit Studio is a local-first observability environment for API and algorithm validation.

Its purpose is to collect evidence before implementation:

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

The current delivery is not a code generator. It is a visual lab for telemetry, logs, reports and technical context.

The platform should let a user insert an API, webhook, site endpoint or algorithm into a harness and receive evidence that can be reused by an implementation AI.

## Current Runtime

```txt
Docker PostgreSQL
↓
NiceGUI App
↓
Core Python Services
↓
xAI Test Runner
↓
PostgreSQL Observability Tables
↓
Live Dashboard / Logs / Context Builder / Reports
```

The Lead Algorithm Lab remains available as a local deterministic module:

```txt
Lead Algorithm Lab
↓
lead_tests table
↓
logs/lead_tests.jsonl
```

Future generic algorithm/API harness:

```txt
User-defined case
↓
HTTP endpoint or Python function
↓
Expected vs actual comparison
↓
Structured event
↓
Dashboard / Logs / Context Builder
```

## Main Directories

- `core/`: database, models, repositories, observability, xAI runner, context and report generation.
- `ui/`: NiceGUI shell, live dashboard, logs, context builder, charts, cards, tables and theme.
- `labs/`: legacy provider validation scripts.
- `logs/`: local JSONL runtime logs for legacy/local modules.
- `exports/reports/`: generated observability reports.
- `exports/contexts/`: generated context files.
- `exports/blueprints/`: archived future implementation references.

## Data Model

Live observability uses PostgreSQL as the source of truth:

- `test_runs`: one row per test sequence.
- `test_events`: timeline of structured events.
- `api_requests`: sanitized request payloads and endpoint/SDK path.
- `api_responses`: sanitized response payloads, tokens and cost.
- `voice_tests`: future voice validation metadata.
- `agent_tests`: future multi-agent validation metadata.
- `context_exports`: exported context/report records.

Next algorithm-specific tables should be:

- `algorithm_definitions`: algorithm name, purpose, input schema and output schema.
- `algorithm_test_cases`: manual and suite test cases.
- `algorithm_test_runs`: one execution batch.
- `algorithm_test_results`: expected vs actual result, diff and recommendation.

Implemented Algorithm Test Lab flow:

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
Context Builder
```

## Event Contract

```json
{
  "event_id": "uuid",
  "timestamp": "",
  "provider": "xai",
  "module": "",
  "test_name": "",
  "status": "",
  "latency_ms": 0,
  "tokens": {},
  "cost": 0,
  "request": {},
  "response": {},
  "error": null,
  "recommendation": ""
}
```

## xAI Runner

The UI-triggered compact runner currently validates:

- connectivity/auth
- chat
- structured outputs
- streaming
- function calling

Agents and Voice are represented as blocked evidence until the dedicated validation plan has fixtures, cost boundaries and acceptance criteria.

## Context And Reports

Reports are generated from real database events:

```txt
exports/reports/*.md
exports/reports/*.json
exports/reports/*.html
```

The Context Builder summarizes:

- what was tested
- what worked
- what failed
- payloads
- response shapes
- latencies
- limitations
- recommendations

For algorithms, Context Builder should also summarize:

- business objective
- input contract
- output contract
- expected vs actual behavior
- cases that passed
- cases that failed
- examples ready to paste into an implementation AI

## Implementation Boundary

Production implementation must not start from docs alone.

It must start from:

- at least one real test result
- structured PostgreSQL events
- observed failures
- generated technical context
- report recommendations

## xAI Design Implications

- Use official xAI docs as source of truth.
- Prefer Responses API concepts for future integrations.
- Use `xai-sdk` where it gives cleaner Python validation and structured parsing.
- Capture streaming chunk count and first-chunk latency.
- Treat Multi Agent as beta and more expensive/slower than compact single-model tests.
- Treat Voice APIs as a separate track with explicit budget, synthetic audio fixtures and privacy controls.
