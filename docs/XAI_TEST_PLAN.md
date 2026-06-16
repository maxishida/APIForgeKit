# xAI Test Lab Plan

## Goal

Validate the xAI API with real calls and live observability before any product implementation.

Priority:

```txt
Logs -> Evidências -> Contexto -> Implementação futura
```

## Sources Reviewed

- https://docs.x.ai/overview
- https://docs.x.ai/developers/model-capabilities/text/generate-text
- https://docs.x.ai/developers/model-capabilities/text/structured-outputs
- https://docs.x.ai/developers/model-capabilities/text/streaming
- https://docs.x.ai/developers/tools/function-calling
- https://docs.x.ai/developers/model-capabilities/text/multi-agent
- https://docs.x.ai/developers/model-capabilities/audio/text-to-speech
- https://docs.x.ai/developers/model-capabilities/audio/speech-to-text
- https://docs.x.ai/developers/model-capabilities/audio/voice-agent
- https://docs.x.ai/developers/rest-api-reference/inference/models
- https://docs.x.ai/developers/rate-limits
- https://docs.x.ai/developers/debugging

## Current Implementation

The NiceGUI Live Dashboard includes a compact xAI runner.

Implemented compact coverage:

- Responses API basic call through `POST /v1/responses` with `store=false`
- authentication/readiness
- basic chat legacy compatibility
- structured output parsing with Pydantic
- streaming response and chunk logging
- function calling loop
- blocked events for Agents and realtime Voice Agent until dedicated tests are approved
- REST Voice Lab for TTS -> STT -> agent response when `XAI_API_KEY` is configured

Command path:

```bash
npm run db
python app.py
```

Then open Live Dashboard and click `Executar xAI Compact`.

## Phase 0 - Readiness

- Verify `XAI_API_KEY` presence without printing it.
- Confirm model override via `XAI_MODEL`.
- Confirm PostgreSQL is online.
- Confirm output directories exist.
- Confirm reports/context directories exist.
- Confirm provider outputs are not committed.

Evidence:

- readiness event
- DB status
- selected model
- blocked reason when key or DB is unavailable

## Phase 1 - Connectivity

Tests:

- authentication
- health-style minimal request
- `/v1/models`
- `/v1/language-models`
- model detail lookup
- invalid key error
- invalid model error
- rate-limit metadata or documented limitation capture

Evidence:

- HTTP status
- endpoint
- response shape
- accessible model IDs
- pricing fields when returned
- error shape for 401/404/429 style failures

## Phase 2 - Chat / Responses

Tests:

- simple prompt
- complex prompt
- system prompt
- Responses API basic call
- conversation chaining with `previous_response_id`
- JSON object mode
- long context smoke test

Evidence:

- request payload
- response object shape
- parsed text extraction path
- usage/tokens
- latency
- limitations or unsupported parameters

Important rule:

Use Responses API first for future integrations. Chat Completions and `xai-sdk` validation remain useful as `chat_legacy` compatibility evidence only.

## Phase 3 - Structured Outputs

Tests:

- Pydantic schema parsing through `xai-sdk`
- `response_format` JSON schema through OpenAI-compatible client or REST
- invalid schema failure
- schema conformance validation
- optional field and nullable field behavior

Evidence:

- schema
- parsed object
- raw response
- validation error shape
- latency
- recommendation

## Phase 4 - Streaming

Tests:

- streaming text response
- first-chunk latency
- total latency
- chunk count
- usage metadata in final response if present
- interruption/cancel behavior
- reconnect strategy documentation

Evidence:

- chunk event shape
- final assembled text
- first chunk timing
- termination signal
- error shape on interruption

## Phase 5 - Agents

The Multi Agent feature is beta and can cost more because it may invoke built-in tools and run longer.

Tests:

- minimal multi-agent request
- 4-agent low-effort request
- optional 16-agent high-effort request only with explicit budget
- tool invocation metadata
- encrypted content behavior when available

Evidence:

- model
- agent count / reasoning effort
- tools used
- latency
- token/cost metadata
- limitations
- beta behavior notes

## Phase 6 - Voice

Voice must be validated carefully because it can involve cost, private audio and larger artifacts.

Implemented REST roundtrip:

- TTS generation from a synthetic lead message
- STT upload of the generated MP3
- transcript-based intent classification
- text agent response using the transcript
- structured logs for lead, user message, API error, latency, voice status, origin and previous page

Remaining tests:

- STT upload with known synthetic sample fixture
- transcription accuracy
- transcript-based intent analysis
- transcript-based classification
- transcript summary
- realtime Voice Agent feasibility over WebSocket
- event stream from `wss://api.x.ai/v1/realtime`

Evidence:

- audio file metadata, not raw private content
- endpoint
- MIME type
- transcript
- confidence or quality fields if returned
- latency
- cost estimate
- event types
- error cases for unsupported media or account limits

Privacy rule:

Do not commit audio files or raw private transcripts. Use synthetic samples for committed fixtures.

## Phase 7 - Benchmark

Capture:

- latency
- first chunk latency for streaming
- tokens
- cost estimate
- response quality notes
- error rate
- retry behavior
- rate-limit observations
- reliability across repeated runs

Benchmark output:

```json
{
  "provider": "xai",
  "model": "",
  "endpoint": "",
  "test": "",
  "runs": 3,
  "success_rate": 1.0,
  "latency_ms_avg": 0,
  "latency_ms_p95": 0,
  "tokens_avg": {},
  "cost_avg": 0,
  "errors": [],
  "recommendation": ""
}
```

## Structured Event Format

```json
{
  "event_id": "uuid",
  "timestamp": "",
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

## Context Builder Output

After each sequence, generate:

- what was validated
- what failed
- correct payloads
- response shapes
- limits found
- error handling rules
- cost and rate-limit notes
- recommendations
- blockers

## Reports

Export each sequence to:

- Markdown
- JSON
- HTML

Report sections:

- executive summary
- metrics
- errors
- evidence references
- recommendations
- future implementation impact

## Completion Criteria

A phase is complete only when:

- each planned test has a structured event
- failures are documented
- context is generated
- report is exported
- next phase risks are named

No production implementation should begin before the relevant feature phase has real evidence.
