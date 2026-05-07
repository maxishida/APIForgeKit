---
name: api-builder-lab
description: Use when validating real AI provider APIs before integrating them into a main project, especially OpenAI, Gemini, Anthropic, or xAI calls involving auth, streaming, tools/function calling, structured outputs, vision, or future TypeScript adapters.
---

# API Builder Lab

## Core rule

Do not implement a provider integration in the main project until the provider has passed a real Python lab.

Use this skill to save IDE and agent tokens. The lab replaces repeated prompt-side guessing with local proof: run the provider SDK with the current `.env`, capture the response shape, then use that evidence for the TypeScript plan.

In Portuguese: o API Builder existe para economizar tokens da IDE. A IDE executa uma pipeline curta de testes com a API real, usando as ferramentas e SDKs que voce pretende usar, direto com a chave atual do repositorio. Depois disso, o app principal nao fica poluido com tentativas, caches, virtualenvs ou payloads experimentais.

Required flow:

```txt
Official docs -> Python lab -> real output -> technical feedback -> TypeScript plan -> main implementation
```

## Use the lab

1. Read `providers.md` and the relevant official docs.
2. Configure `.env` from `.env.example`.
3. Run one focused case from `labs/`.
4. Check the saved JSON in `outputs/`.
5. Report the exact SDK, endpoint, model, payload shape, response shape, latency, and failure mode.
6. Only plan TypeScript after a real output exists.

Keep the main workspace clean. Do not move experimental provider code into the app while the lab is still discovering auth, payloads, event shapes, tool calls, or structured output behavior.

## Provider commands

```bash
python labs/openai_lab.py --case auth
python labs/openai_lab.py --case basic
python labs/openai_lab.py --case stream
python labs/openai_lab.py --case tools
python labs/openai_lab.py --case structured

python labs/gemini_lab.py --case auth
python labs/gemini_lab.py --case basic
python labs/gemini_lab.py --case stream
python labs/gemini_lab.py --case tools
python labs/gemini_lab.py --case vision

python labs/anthropic_lab.py --case auth
python labs/anthropic_lab.py --case basic
python labs/anthropic_lab.py --case stream
python labs/anthropic_lab.py --case tools

python labs/xai_lab.py --case auth
python labs/xai_lab.py --case basic
python labs/xai_lab.py --case stream
python labs/xai_lab.py --case tools
```

Run commands from the `api-lab-kit/` directory.

## Output rule

Every real run must save a JSON file in `outputs/` with:

```txt
provider
test_name
timestamp
status
model_used
latency_ms
request_summary
response_summary
error_message
raw_response_without_secrets
```

Never hardcode API keys. Never print complete keys. Never save secrets in outputs.

Real output JSON files are local runtime artifacts and are ignored by git by default.

## Stop conditions

Stop before main implementation when:

- the official docs do not match the SDK behavior
- auth fails
- streaming event shapes are unclear
- tool/function call payloads are not captured
- structured output does not validate
- no real output has been saved
