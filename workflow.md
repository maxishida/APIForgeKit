# APIForgeKit Validation Workflow

## Goal

Validate real behavior before building production code.

APIForgeKit is not a shortcut for guessing SDK payloads or algorithm behavior. It is an evidence pipeline:

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

The practical open source promise is token economy for developers:

```txt
Run local test lab
↓
Generate compact evidence
↓
Paste less into LLM
↓
Get better implementation faster
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

### Generic Algorithm/API Harness Track

This track is now started with Algorithm Test Lab.

Use it when the user wants to validate:

- a WhatsApp API
- a webhook
- a site endpoint
- a local Python algorithm
- a scoring/classification/recommendation function

Target flow:

```txt
User defines input
↓
Harness calls API or algorithm
↓
Studio records expected vs actual
↓
Dashboard shows pass/fail and behavior
↓
Context Builder creates AI-ready context
```

Current implementation:

- Route: `/algorithm-test-lab`
- Algorithm: `lead_score`
- Tables: `algorithm_definitions`, `algorithm_test_cases`, `algorithm_test_runs`, `algorithm_test_results`
- Validation: expected JSON vs actual JSON with structured diff
- Context: generated in Algorithm Test Lab and Context Builder

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

## Required Algorithm Flow

1. Explain the algorithm objective in plain language.
2. Define inputs and outputs.
3. Create at least three cases: success, edge case and invalid case.
4. Run one case manually.
5. Compare expected output with actual output.
6. Save structured JSON.
7. Add the case to a repeatable suite.
8. Generate context only from observed behavior.

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

Algorithm evidence must also include:

- algorithm name
- input payload
- expected output
- actual output
- diff
- pass/fail status
- explanation visible to a non-technical user

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

See:

- `USER_GUIDE.md`
- `OPEN_SOURCE_TUTORIAL.md`
- `ALGORITHM_TEST_PLAN.md`
