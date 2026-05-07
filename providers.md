# Providers

Official documentation is the source of truth. Blogs can help with context, but must not define payloads, SDK usage, or compatibility decisions.

## Provider Matrix

| Provider | Python SDK | TypeScript SDK | Streaming | Tools / Functions | Structured Output | Vision / VLM | Web Search | Live / Realtime | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| OpenAI | `openai` | `openai` | Yes | Yes | Yes | Yes, by supported model | Yes, with tools | Realtime API separately | Lab scaffolded |
| Gemini | `google-genai` | `@google/genai` | Yes | Yes | Yes | Yes | Google Search tools | Live API | Lab scaffolded |
| Anthropic | `anthropic` | `@anthropic-ai/sdk` | Yes | Yes | Schema-like tool input | Yes, by supported model | Yes | No primary live API in this kit | Lab scaffolded |
| xAI | `xai-sdk` | `@ai-sdk/xai` or OpenAI-compatible SDK | Yes | Yes | Responses API support | Yes, by supported model | Yes | Voice Agent API separately | Lab scaffolded |

## OpenAI

- Main docs: https://platform.openai.com/docs
- Quickstart: https://platform.openai.com/docs/quickstart?api-mode=responses&lang=python
- Python SDK: https://github.com/openai/openai-python
- TypeScript SDK: https://github.com/openai/openai-node
- Streaming: https://platform.openai.com/docs/guides/streaming-responses
- Function calling: https://platform.openai.com/docs/guides/function-calling?api-mode=responses
- Tools: https://platform.openai.com/docs/guides/tools?api-mode=responses
- Structured outputs: https://platform.openai.com/docs/guides/structured-outputs?api-mode=responses

Lab coverage:

- `auth`
- `basic`
- `stream`
- `tools`
- `structured`

## Gemini / Google GenAI

- Main docs: https://ai.google.dev/gemini-api/docs
- API reference: https://ai.google.dev/api
- Quickstart: https://ai.google.dev/gemini-api/docs/quickstart
- Text generation and streaming: https://ai.google.dev/gemini-api/docs/text-generation
- Function calling: https://ai.google.dev/gemini-api/docs/function-calling
- Structured outputs: https://ai.google.dev/gemini-api/docs/structured-output
- Vision / image understanding: https://ai.google.dev/gemini-api/docs/vision
- Live API: https://ai.google.dev/gemini-api/docs/live
- Live API tool use: https://ai.google.dev/gemini-api/docs/live-tools

Lab coverage:

- `auth`
- `basic`
- `stream`
- `tools`
- `vision`

Live API is documented here but not executed by the compact lab.

## Anthropic / Claude

- Main docs: https://docs.anthropic.com
- Client SDKs: https://docs.anthropic.com/en/api/client-sdks
- Messages API: https://docs.anthropic.com/en/api/messages
- Streaming: https://docs.anthropic.com/en/docs/build-with-claude/streaming
- Tool use: https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/implement-tool-use
- Fine-grained tool streaming: https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/fine-grained-tool-streaming
- Errors: https://docs.anthropic.com/en/api/errors

Lab coverage:

- `auth`
- `basic`
- `stream`
- `tools`

## xAI / Grok

- Main docs: https://docs.x.ai
- Getting started: https://docs.x.ai/docs/tutorial
- API reference: https://docs.x.ai/docs/api-reference
- Streaming: https://docs.x.ai/docs/guides/streaming-response
- Function calling: https://docs.x.ai/developers/tools/function-calling
- Streaming and sync tools: https://docs.x.ai/developers/tools/streaming-and-sync
- Web search: https://docs.x.ai/developers/tools/web-search
- Realtime / voice agent: https://docs.x.ai/developers/models/realtime-api

Lab coverage:

- `auth`
- `basic`
- `stream`
- `tools`

Web search is documented here but not required as a compact lab case.
