# API Lab Workflow

## Goal

Validate real provider behavior before implementation in the main project.

Esse tambem e um fluxo de economia de tokens para a IDE ou coding agent. O lab transforma trabalho incerto de provider em testes curtos e repetiveis, em vez de ciclos longos de prompt onde o agent fica lendo docs, chutando chamadas de SDK e mexendo no app principal. Rode o API Builder primeiro, capture o output real, depois use essa evidencia para planejar o adapter TypeScript.

O lab deve rodar com o `.env` local atual do repositorio, dentro desta pasta isolada. Ele pode criar um virtualenv local, executar chamadas reais dos SDKs dos providers e salvar outputs JSON sem poluir a superficie do app principal. Arquivos de runtime ficam locais por padrao.

## Required flow

### Repeat execution

Use repeat execution when a focused case already exists and the goal is to get a fresh result without spending tokens on documentation review.

```txt
1. Pick provider and case
2. Configure .env
3. Run python run_lab.py --provider <provider> --case <case>
4. Inspect output JSON
5. Record status, model, response shape, latency, and errors
6. Plan TypeScript adapter only after real output exists
```

`run_lab.py --status` checks readiness without API calls. It reports only whether keys are present or missing; it never prints key values.

### Investigation or repair

```txt
1. Pick provider
2. Read official docs in providers.md
3. Configure .env
4. Run auth case
5. Run basic case
6. Run stream/tools/structured/vision case as needed
7. Inspect output JSON
8. Record SDK, model, endpoint, payload, response shape, latency, and errors
9. Plan TypeScript adapter only after real output exists
```

Use investigation or repair when a case is new, fails, or has uncertain SDK/payload behavior. Official docs are required in this mode.

## Environment rules

Required variables:

```txt
OPENAI_API_KEY=
GEMINI_API_KEY=
ANTHROPIC_API_KEY=
XAI_API_KEY=
```

Optional model overrides:

```txt
OPENAI_MODEL=
GEMINI_MODEL=
ANTHROPIC_MODEL=
XAI_MODEL=
```

Never hardcode keys. Never print full keys. Never save secrets in output files.

## Output rules

Files are saved in:

```txt
outputs/YYYY-MM-DD_provider_testname_result.json
```

JSONs de output sao ignorados pelo git. Commite templates, docs e scripts do lab; mantenha respostas reais dos providers localmente, salvo quando houver uma decisao explicita de compartilhar uma fixture redigida.

Each output contains:

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

Allowed statuses:

- `ok`
- `error`
- `skipped_missing_env`
- `missing_dependency`

## Harness proof

When one provider passes a real case through the executor, the shared lab harness is working: `.env` loading, isolated SDK call, output JSON, secret redaction, summary, and TypeScript handoff evidence. That proves the lab workflow. It does not mark every provider API as validated; each provider still needs its own real output when its key is available.

## Implementation boundary

This kit is isolated. Do not add:

- app frontend
- app backend
- app database
- app authentication
- business logic
- production TypeScript adapter

TypeScript is planned only after the Python lab has a real output.
