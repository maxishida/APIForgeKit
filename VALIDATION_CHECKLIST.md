# APIForgeKit Validation Checklist

## Documentation Review

- [x] README aligned to live observability.
- [x] workflow aligned to evidence-first flow.
- [x] providers updated for xAI observability priority.
- [x] SKILL rewritten as operational brain.
- [x] architecture.md aligned to PostgreSQL event architecture.
- [x] IMPLEMENTATION_CHECKLIST updated.
- [x] XAI_TEST_PLAN updated.
- [x] Algorithm Test Lab documentation added.

## Algorithm Test Lab

- [x] `algorithm_definitions` table.
- [x] `algorithm_test_cases` table.
- [x] `algorithm_test_runs` table.
- [x] `algorithm_test_results` table.
- [x] `lead_score` algorithm registered.
- [x] 8 seed cases registered.
- [x] Expected-vs-actual validator implemented.
- [x] Suite execution implemented.
- [x] Structured result log persisted.
- [x] Context Builder includes algorithm evidence.
- [ ] Add HTTP harness for site/API algorithms.
- [ ] Add algorithm charts to main dashboard.

## xAI Documentation Review

- [x] Overview reviewed.
- [x] Generate Text / Responses reviewed.
- [x] Structured Outputs reviewed.
- [x] Streaming reviewed.
- [x] Function Calling reviewed.
- [x] Multi Agent reviewed.
- [x] Voice overview reviewed.
- [x] Speech to Text reviewed.
- [x] Voice Agent API reviewed.
- [x] Models endpoint reviewed.
- [x] Rate limits reviewed.
- [x] Error/debugging docs reviewed.

## Before Real xAI Tests

- [x] Add `XAI_API_KEY` to local `.env`.
- [ ] Run `npm run db`.
- [ ] Run `python app.py`.
- [ ] Click `Executar xAI Compact` in Live Dashboard.
- [ ] Confirm no secrets are printed.
- [ ] Confirm events appear in `test_events`.
- [ ] Define max spend / number of calls for expanded benchmarks.
- [ ] Use synthetic audio for Voice tests.

## Compact Live Runner

- [x] Auth/readiness event.
- [x] Basic chat event.
- [x] Structured output parse event.
- [x] Streaming chunk/final events.
- [x] Function calling event.
- [x] Agents blocked event.
- [x] Voice blocked event.
- [x] Report export path.

## Phase 1 - Connectivity

- [ ] Auth test.
- [ ] Minimal health-style request.
- [ ] List models.
- [ ] List language models.
- [ ] Invalid key error.
- [ ] Invalid model error.
- [ ] Rate limit/error behavior documented.

## Phase 2 - Chat / Responses

- [ ] Simple prompt.
- [ ] Complex prompt.
- [ ] System prompt.
- [ ] Responses API call.
- [ ] Conversation chaining.
- [ ] JSON object mode.
- [ ] Long context smoke test.

## Phase 3 - Structured Outputs

- [x] Pydantic schema parse via compact runner.
- [ ] REST/OpenAI-compatible JSON schema response_format.
- [ ] Invalid schema failure.
- [ ] Optional/nullable behavior.

## Phase 4 - Streaming

- [x] Streaming response via compact runner.
- [x] Chunk logging.
- [ ] First-chunk latency benchmark.
- [ ] Interruption behavior.
- [ ] Reconnect recommendation.

## Phase 5 - Agents

- [ ] Minimal multi-agent request.
- [ ] 4-agent low-effort run.
- [ ] Tool metadata capture.
- [ ] Cost/latency warning.

## Phase 6 - Voice

- [ ] Synthetic STT upload.
- [ ] Transcription accuracy.
- [ ] Intent analysis from transcript.
- [ ] Classification from transcript.
- [ ] Summary from transcript.
- [ ] Metrics extraction.
- [ ] TTS generation.
- [ ] Realtime Voice Agent feasibility.

## Phase 7 - Benchmark

- [ ] Latency captured.
- [ ] Tokens captured.
- [ ] Cost estimated.
- [ ] Quality notes recorded.
- [ ] Errors summarized.
- [ ] Reliability summarized.

## Reports

- [x] Markdown report export implemented.
- [x] JSON report export implemented.
- [x] HTML report export implemented.
- [x] Context Builder output generated from events.
- [ ] Expanded phase report generated after real full run.
