# APIForgeKit Studio

APIForgeKit Studio é um laboratório local-first para validar APIs, webhooks e algoritmos antes de gastar tempo e tokens implementando uma feature final.

Ideia principal:

```txt
Teste real
↓
Logs estruturados
↓
Evidências
↓
Contexto técnico
↓
Implementação mais rápida com IA
```

O projeto não tenta gerar código de produto primeiro. Ele testa o comportamento, grava evidências em PostgreSQL, mostra métricas no dashboard e gera contexto reutilizável.

## O que dá para fazer

- Validar algoritmos determinísticos, como `lead_score`.
- Testar contratos de APIs e webhooks em modo dry-run ou HTTP real com permissão.
- Rodar validações xAI e registrar telemetria.
- Calcular uso e custo de tokens por provider/modelo/usuário.
- Ver logs, métricas e relatórios em uma UI local.
- Exportar contexto técnico em Markdown, JSON, HTML e ZIP.
- Distinguir evidência `real_http`, `dry_run_contract`, `seed_validation`, `legacy` e `blocked`.

## Stack

- Python + NiceGUI
- PostgreSQL via Docker
- SQLAlchemy
- Plotly/Pandas
- Pytest
- ACP Skill Executor opcional para clientes/agentes

## Instalação

```bash
python -m pip install -r requirements.txt
copy .env.example .env
npm run db
python app.py
```

Abra:

```txt
http://localhost:8080
```

No Linux/macOS, troque `copy .env.example .env` por:

```bash
cp .env.example .env
```

## Comandos úteis

```bash
npm run db              # sobe PostgreSQL
npm run db:logs         # mostra logs do banco
npm run db:reset        # recria banco local
npm run dev             # roda app NiceGUI
npm run test            # roda testes
npm run algorithm:suite # valida lead_score e exporta evidências
npm run acp             # inicia executor ACP via stdio
npm run acp:prompt -- "/validate-lead-score" # smoke local ACP via CLI
```

## Fluxo recomendado

1. Suba o banco com `npm run db`.
2. Rode a UI com `python app.py`.
3. Abra `http://localhost:8080`.
4. Entre em `Algorithm Test Lab`.
5. Selecione `lead_score`.
6. Execute a canonical suite.
7. Veja passed/failed, diff, invariantes e `seed_validation`.
8. Abra `Context Builder`.
9. Exporte o relatório para usar como contexto em uma IA.

## Context Builder

O `Context Builder` é o gate antes de qualquer implementação. Ele não inventa comportamento; ele junta evidências reais e informa se o contexto está pronto.

Modos disponíveis:

- `Algorithm + API`: exige evidência de algoritmo e contrato de API.
- `Algorithm only`: ideal para validar score, regras e classificações determinísticas.
- `API only`: ideal para webhooks, payloads e endpoints.
- `Full evidence`: junta algoritmo, API, live logs e cálculo de tokens.

Readiness:

- `Ready`: há evidência suficiente para orientar uma IA.
- `Needs tests`: falta rodar suite ou registrar evidência.
- `Has failures`: existem diffs/falhas que precisam ser corrigidos ou documentados.

Exports gerados em `exports/reports/`:

- Markdown
- JSON com metadata
- HTML
- ZIP bundle

## Páginas principais

- Home: visão geral e ações de seed validation.
- Live Dashboard: observabilidade e eventos.
- Algorithm Test Lab: testes de algoritmos determinísticos.
- Generic API Lab: contratos de APIs/webhooks.
- Token Calculator: estimativa de tokens, custo e economia de contexto.
- Logs: busca, filtros e JSON completo dos eventos.
- Context Builder: contexto técnico baseado em evidências reais.

## Algorithm Test Lab

O primeiro algoritmo pronto é `lead_score`.

Ele valida:

- origem do lead
- urgência
- interesse
- telefone/e-mail
- cliente anterior
- mensagem vazia
- spam
- penalidades
- classificação final

A suite atual tem 17 casos prontos e grava no PostgreSQL:

- input JSON
- expected output JSON
- actual output JSON
- diff
- status passed/failed
- latência
- invariantes do score

Rode pela CLI:

```bash
npm run algorithm:suite
```

## ACP Skill Executor

Para operar o lab por um cliente compatível com ACP:

```bash
npm run acp
```

Para rodar um prompt ACP completo sem montar JSON-RPC manualmente:

```bash
python run_acp_prompt.py "/validate-lead-score"
python run_acp_prompt.py "/token-cost provider=xai model=grok-4.3 users=10 requests=20"
```

Esse helper cria uma sessão local, envia `ContentBlock[]` de texto e imprime a resposta final junto das notificações `session/update`.

### ACP stdio quickstart

Suba dependências primeiro:

```bash
python -m pip install -r requirements.txt
copy .env.example .env
npm run db
npm run acp
```

Configure um cliente ACP/IDE para abrir o executor como subprocesso stdio:

```json
{
  "command": "npm",
  "args": ["run", "acp"],
  "cwd": "D:\\myworksapce\\Apiforgekit\\APIForgeKit",
  "transport": "stdio"
}
```

O cliente deve enviar um JSON-RPC por linha. A ordem é `initialize`, depois `session/new` com `cwd` absoluto, depois `session/prompt`.

O executor envia progresso em notificações `session/update` antes da resposta final. Leia `agent_message_chunk` para o JSON completo do resultado; trate `PromptResponse` como metadata de parada e caminhos em `_meta`.

Comandos principais:

```txt
/validate-lead-score
/validate-algorithm lead_score
/validate-api-suite whatsapp_validation_pack
/token-cost provider=xai model=grok-4.3 users=10 requests=20
/build-context
/export-evidence
```

Use `/validate-lead-score` quando quiser rodar a validação canônica de leads. Ele executa a suite, verifica invariantes e exporta um `lead_score_evidence_pack`.

No ACP v1, os comandos anunciados em `available_commands_update` não usam `/`, mas o prompt do usuário usa:

```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "session/prompt",
  "params": {
    "sessionId": "SESSION_ID",
    "prompt": [
      {
        "type": "text",
        "text": "/validate-lead-score"
      }
    ]
  }
}
```

O resultado completo sai em `session/update -> agent_message_chunk`. Caminhos como `contextPath` e `evidenceZip` também aparecem em `_meta`.

## Testes

```bash
python -m pytest -q
python -m compileall app.py core ui agents run_algorithm_lab.py run_acp_prompt.py
```

## Documentação

A raiz do projeto fica curta de propósito:

- [README.md](./README.md): guia rápido.
- [SKILL.md](./SKILL.md): contrato operacional para agentes.

Todo o restante está em [docs/SUMMARY.md](./docs/SUMMARY.md).

Leitura recomendada:

1. [docs/MVP_100_PERCENT_MAP.md](./docs/MVP_100_PERCENT_MAP.md)
2. [docs/MVP_100_PERCENT_CHECKLIST.md](./docs/MVP_100_PERCENT_CHECKLIST.md)
3. [docs/MVP_FEATURE_TEST_REPORT.md](./docs/MVP_FEATURE_TEST_REPORT.md)
4. [docs/USER_GUIDE.md](./docs/USER_GUIDE.md)
5. [docs/OPEN_SOURCE_TUTORIAL.md](./docs/OPEN_SOURCE_TUTORIAL.md)
6. [docs/ALGORITHM_TEST_PLAN.md](./docs/ALGORITHM_TEST_PLAN.md)
7. [docs/ACP_AGENT_ARCHITECTURE.md](./docs/ACP_AGENT_ARCHITECTURE.md)
8. [docs/IMPLEMENTATION_CHECKLIST.md](./docs/IMPLEMENTATION_CHECKLIST.md)

## Status

V1 está focada em validação, observabilidade e contexto técnico. Next.js/Prisma aparecem apenas como destino futuro para implementação depois que os testes já geraram evidência.
