# Providers

Official documentation is the source of truth. Blogs can help with context, but must not define payloads, SDK usage, compatibility, or pricing decisions.

## Provider Matrix

| Provider | Current Role | Python SDK | TypeScript Path | Status |
| --- | --- | --- | --- | --- |
| xAI | Priority validation provider for APIForgeKit Observability Lab | `xai-sdk` and OpenAI-compatible client | Future only | Live compact runner implemented; expanded plan documented |
| OpenAI | Legacy comparison provider | `openai` | `openai` | Compact lab scaffolded |
| Gemini | Legacy comparison provider | `google-genai` | `@google/genai` | Compact lab scaffolded |
| Anthropic | Legacy comparison provider | `anthropic` | `@anthropic-ai/sdk` | Compact lab scaffolded |

## xAI / Grok

Primary docs:

- Overview: https://docs.x.ai/overview
- Generate Text / Responses API: https://docs.x.ai/developers/model-capabilities/text/generate-text
- Chat Completions legacy endpoint: https://docs.x.ai/developers/model-capabilities/text/chat-completions
- Structured Outputs: https://docs.x.ai/developers/model-capabilities/text/structured-outputs
- Streaming: https://docs.x.ai/developers/model-capabilities/text/streaming
- Function Calling: https://docs.x.ai/developers/tools/function-calling
- Multi Agent: https://docs.x.ai/developers/model-capabilities/text/multi-agent
- Voice Overview: https://docs.x.ai/developers/model-capabilities/audio/voice
- Speech to Text: https://docs.x.ai/developers/model-capabilities/audio/speech-to-text
- Voice Agent API: https://docs.x.ai/docs/guides/voice/agent
- Rate Limits: https://docs.x.ai/developers/rate-limits
- Errors / Debugging: https://docs.x.ai/developers/debugging
- Models API reference: https://docs.x.ai/developers/rest-api-reference/inference/models

Important current findings from docs:

- New text work should prefer the Responses API; Chat Completions is legacy.
- Responses API supports conversation continuation with `previous_response_id`.
- Structured outputs support JSON schema via `response_format` and JSON object mode.
- Streaming text uses SSE and requires `stream: true`.
- Function calling uses JSON Schema parameters and can pause execution for custom tool handling.
- Multi Agent is beta and should be treated as a separate benchmark/cost track.
- Models can be listed through `/v1/models`; richer language model metadata is available through `/v1/language-models`.
- Rate limits are per team and per model using RPM and TPM.
- Voice APIs are separate from text inference: Voice Agent realtime over WebSocket, Text to Speech, and Speech to Text.

Current Live Studio compact coverage:

- `auth`
- `basic`
- `schema_parse`
- `stream`
- `tools`
- blocked placeholder events for `agents` and `voice`

Expanded planned xAI coverage:

- connectivity and model metadata
- Responses API text tests
- JSON mode
- structured output
- streaming latency and interruption behavior
- STT upload
- voice intent/classification using transcript
- TTS generation
- realtime voice agent feasibility
- benchmark and report generation

## OpenAI

- Main docs: https://platform.openai.com/docs
- Python SDK: https://github.com/openai/openai-python
- TypeScript SDK: https://github.com/openai/openai-node

Compact lab coverage:

- `auth`
- `basic`
- `stream`
- `tools`
- `structured`

## Gemini / Google GenAI

- Main docs: https://ai.google.dev/gemini-api/docs
- API reference: https://ai.google.dev/api

Compact lab coverage:

- `auth`
- `basic`
- `stream`
- `tools`
- `vision`

## Anthropic / Claude

- Main docs: https://docs.anthropic.com
- Client SDKs: https://docs.anthropic.com/en/api/client-sdks

Compact lab coverage:

- `auth`
- `basic`
- `stream`
- `tools`
