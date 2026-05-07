---
name: api-builder-lab
description: Use when an agent needs to validate real AI provider API behavior before main-project integration, especially auth, SDK setup, streaming, tools/function calling, structured outputs, vision/VLM, web search, or TypeScript adapter planning for OpenAI, Gemini, Anthropic, or xAI.
---

# API Builder Lab

## Finalidade

Use this skill to validate real provider behavior in a local Python lab before any main-project integration.

The goal is token economy for the IDE or coding agent: stop guessing provider payloads inside the app, run a short proof command with the current repository `.env`, save the real response shape, then use that evidence to plan TypeScript.

API Builder Lab is not production implementation. It is an isolated testing surface for SDK calls, auth, streaming, tools/functions, structured output, vision/VLM, web search, and future adapter planning.

## When to use

- A provider integration may touch OpenAI, Gemini, Anthropic, or xAI.
- SDK behavior, payload shape, streaming events, tool calls, or structured output are uncertain.
- The user wants to test an API with the repository's current local key.
- TypeScript implementation depends on a real provider response.
- The main workspace must stay clean while the API is being explored.

## When not to use

- The task is only a mock, fixture, UI, or business-logic change.
- The provider behavior is already validated by a current real output.
- The user explicitly asks to skip real API calls.
- You are implementing the final production TypeScript adapter.

## Operating modes

### Execution mode

Use this mode when the provider case already exists in `labs/` and the goal is to get a fresh result, avoid rework, and save tokens.

```txt
Python lab -> real output -> technical feedback -> TypeScript plan -> main implementation
```

In execution mode, do not re-read official provider docs every time. Run the focused lab case, inspect the saved JSON, and use the real output as the practical source of truth.

Use official provider docs in execution mode only when:

- the case has no previous real output
- the case fails with auth, SDK, payload, streaming, tool call, model, or structured-output errors
- the lab code needs to be created, fixed, or adapted
- the output shape conflicts with the current TypeScript plan

### Investigation mode

Use this mode when a case is new, broken, or uncertain.

```txt
Official docs -> Python lab -> real output -> technical feedback -> TypeScript plan -> main implementation
```

1. Read `providers.md` and the official provider docs.
2. Configure `.env` from `.env.example`.
3. Create or adjust the focused lab case.
4. Run exactly one focused lab case.
5. Inspect the saved JSON in `outputs/`.
6. Report the command, status, model, response shape, latency, and failure mode.
7. Plan TypeScript only after a real output exists.

## Commands

Run from `api-lab-kit/`:

```bash
python run_lab.py --provider <provider> --case <case>
```

The executor follows this skill's reporting contract and is the default command for repeat execution. It does not print secrets and it reads the JSON output after the lab script runs.

Direct provider scripts remain available for debugging:

```bash
python labs/<provider>_lab.py --case <case>
```

Readiness without API calls:

```bash
python run_lab.py --status
```

Available cases:

| Provider | Cases |
| --- | --- |
| `openai` | `auth`, `basic`, `stream`, `tools`, `structured` |
| `gemini` | `auth`, `basic`, `stream`, `tools`, `vision` |
| `anthropic` | `auth`, `basic`, `stream`, `tools` |
| `xai` | `auth`, `basic`, `stream`, `tools` |

## Required evidence

Do not proceed to main implementation unless the lab has evidence:

- command executed
- output JSON path
- `status` value
- `model_used`
- request summary
- response summary or exact failure
- TypeScript implication

No real output means stop. A missing API key, auth failure, SDK mismatch, unclear streaming event shape, missing tool call, or invalid structured output is a blocker.

If one provider case passes through `run_lab.py`, the lab harness is proven for the shared workflow: local `.env`, isolated Python call, JSON output, redaction, summary, and TypeScript handoff evidence. Other providers are structurally ready, but each provider is API-validated only after its own real output exists.

## Technical response template

Use this format after running or reviewing a lab:

```txt
Provider:
Case:
Command:
Output file:
Status:
Model:
Finding:
Failure mode:
TypeScript implication:
Next action:
```

## Safety rules

- Never hardcode API keys.
- Never print complete API keys.
- Never save secrets in outputs.
- Keep `.env`, `.venv`, caches, and output JSON local.
- Do not move experimental provider code into the main app.
- Use official docs as the source of truth; blogs are secondary only.

## Common mistakes

- Implementing TypeScript before a real Python output exists.
- Trusting old docs or model-invented payloads.
- Testing provider behavior inside the production app.
- Committing `.env` or raw provider outputs.
- Mixing lab exploration with app business logic.
- Treating a passing auth test as proof that streaming, tools, or structured output works.
