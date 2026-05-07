# API Lab Kit

Compact lab for validating real AI provider APIs in Python before implementing them in the main project.

## Por que isso existe

API Builder Lab e uma camada de economia de tokens para sua IDE, coding agent ou automacao local.

Em vez de fazer a IDE gastar contexto lendo documentacao repetidamente, inventando payload, tentando parametros antigos e depurando SDK dentro da aplicacao principal, o fluxo manda a IDE executar uma pipeline curta de testes no API Builder primeiro. O resultado deixa de ser tentativa e passa a ser evidencia: documentacao oficial, teste Python focado e output real salvo.

O valor principal e operacional:

- rodar exatamente as ferramentas de API que voce quer usar antes da integracao
- executar os testes direto com a chave atual do seu `.env`
- validar auth, streaming, tools/functions, structured output e vision em isolamento
- salvar o formato real da resposta para planejar o adapter TypeScript depois
- evitar que codigo experimental do provider polua o workspace principal
- manter secrets, virtualenvs, caches e outputs reais fora do git

O lab fica dentro do repositorio para viajar junto com o projeto, mas os artefatos de runtime nao precisam subir. O que sobe no commit sao a skill, a documentacao, o `requirements.txt` e os scripts reutilizaveis. O que fica local sao `.env`, `.venv`, caches e JSONs reais gerados em `outputs/`.

The lab covers four primary providers:

- OpenAI
- Gemini / Google GenAI
- Anthropic / Claude
- xAI / Grok

## Setup

```bash
cd api-lab-kit
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Fill the API keys in `.env`.

Optional model overrides:

```txt
OPENAI_MODEL=
GEMINI_MODEL=
ANTHROPIC_MODEL=
XAI_MODEL=
```

## Run labs

```bash
python labs/openai_lab.py --case basic
python labs/gemini_lab.py --case basic
python labs/anthropic_lab.py --case basic
python labs/xai_lab.py --case basic
```

Outputs are saved in `outputs/` as JSON.

JSONs de output real sao ignorados pelo git por padrao. Mantenha esses arquivos locais quando eles tiverem respostas especificas da conta ou metadados temporarios do provider.

## Rules

- Use official docs first.
- Use Python before TypeScript.
- Keep each lab case focused.
- Use `.env` only for secrets.
- Save real outputs.
- Do not implement provider logic in the main system until the lab result is validated.
