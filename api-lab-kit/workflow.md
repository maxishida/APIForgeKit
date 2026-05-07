# API Lab Workflow

## Goal

Validate real provider behavior before implementation in the main project.

Esse tambem e um fluxo de economia de tokens para a IDE ou coding agent. O lab transforma trabalho incerto de provider em testes curtos e repetiveis, em vez de ciclos longos de prompt onde o agent fica lendo docs, chutando chamadas de SDK e mexendo no app principal. Rode o API Builder primeiro, capture o output real, depois use essa evidencia para planejar o adapter TypeScript.

O lab deve rodar com o `.env` local atual do repositorio, dentro desta pasta isolada. Ele pode criar um virtualenv local, executar chamadas reais dos SDKs dos providers e salvar outputs JSON sem poluir a superficie do app principal. Arquivos de runtime ficam locais por padrao.

## Required flow

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

## Implementation boundary

This kit is isolated. Do not add:

- app frontend
- app backend
- app database
- app authentication
- business logic
- production TypeScript adapter

TypeScript is planned only after the Python lab has a real output.
