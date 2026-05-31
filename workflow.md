# APIForgeKit Validation Workflow

## Goal

Validate real behavior before building production code.

APIForgeKit is not a shortcut for guessing SDK payloads. It is an evidence pipeline:

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

## Current Tracks

### Live Studio Track

The NiceGUI app is the main observability surface.

```bash
npm run db
python app.py
```

Use this for:

- xAI compact runner
- live event stream
- PostgreSQL event persistence
- dashboard metrics
- logs table
- report export
- Context Builder

### Lead Algorithm Track

The deterministic Lead Algorithm Lab remains available for local business-rule testing.

Use this for:

- lead scoring
- `lead_tests`
- `logs/lead_tests.jsonl`

### Legacy Provider Track

The CLI provider lab remains available for isolated checks.

```bash
python run_lab.py --status
python run_lab.py --provider xai --case auth
```

The existing CLI runner is intentionally small. Expanded xAI validation phases are documented in `XAI_TEST_PLAN.md`.

## Required Provider Flow

1. Read official docs for any new, changed, or failing case.
2. Verify local readiness without printing secrets.
3. Run one focused real test.
4. Save structured output without secrets.
5. Inspect the output JSON/event.
6. Generate or update technical context.
7. Export report.
8. Only then propose implementation.

## Output Rules

Live Studio outputs use PostgreSQL:

```txt
test_runs
test_events
api_requests
api_responses
voice_tests
agent_tests
context_exports
```

Reports use:

```txt
exports/reports/
```

Compact legacy outputs are saved in:

```txt
outputs/YYYY-MM-DD_provider_testname_result.json
```

Minimum event contract:

```json
{
  "event_id": "uuid",
  "provider": "xai",
  "module": "voice",
  "test_name": "voice_transcription",
  "status": "success",
  "latency_ms": 0,
  "tokens": {},
  "cost": 0,
  "request": {},
  "response": {},
  "error": null,
  "recommendation": ""
}
```

## Evidence Rules

Evidence must be specific enough to implement against later:

- endpoint, SDK path or method
- model
- request body or multipart fields
- response body shape
- streaming event shape
- error status and message
- latency
- usage/tokens/cost if exposed
- account limitation if discovered

## xAI Validation Sequence

Follow `XAI_TEST_PLAN.md`:

1. Readiness
2. Connectivity
3. Chat / Responses
4. Structured Outputs
5. Streaming
6. Agents
7. Voice
8. Benchmark

Do not start Voice until connectivity, model access, basic text calls and budget boundaries are proven.

## Environment Rules

Required for xAI:

```txt
XAI_API_KEY=
XAI_MODEL=
```

Never hardcode keys. Never print full keys. Never commit raw provider outputs unless they are intentionally redacted fixtures.

## Implementation Boundary

Do not implement production code from docs alone.

Implementation can begin only after:

- at least one real successful test exists for the target endpoint
- failures are logged
- context is generated
- a report explains limitations and recommendations

Failure is useful evidence. Preserve it.
