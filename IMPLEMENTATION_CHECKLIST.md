# APIForgeKit Studio V1 Implementation Checklist

## O que foi implementado

- NiceGUI local app em `app.py`.
- Shell visual com sidebar, header, cards e tema Dark/Neon Blue.
- Live Dashboard como tela principal.
- xAI compact runner acionado pela UI.
- Live Event Stream com atualização periódica.
- Algorithm Test Lab em `/algorithm-test-lab`.
- Tabelas: `algorithm_definitions`, `algorithm_test_cases`, `algorithm_test_runs`, `algorithm_test_results`.
- Suíte `lead_score` com 8 casos prontos.
- Validador esperado x recebido com diff estruturado.
- Context Builder integrado aos resultados de algoritmo.
- Gráficos Plotly para status, módulos, latência e volume de eventos.
- PostgreSQL Docker com SQLAlchemy.
- Tabelas de observabilidade: `test_runs`, `test_events`, `api_requests`, `api_responses`, `voice_tests`, `agent_tests`, `context_exports`.
- Tela Logs baseada em eventos de observabilidade, com filtros, busca, AG Grid, JSON completo e export CSV/JSONL.
- Context Builder baseado em logs reais.
- Exportação de relatórios Markdown, JSON e HTML.
- Lead Algorithm Lab preservado.
- Blueprint Archive preservado como referência legada.
- `USER_GUIDE.md` criado para explicar o uso da ferramenta.
- `OPEN_SOURCE_TUTORIAL.md` criado para usuários GitHub/open source.
- `ALGORITHM_TEST_PLAN.md` criado para orientar validação de algoritmos por site/API.
- Testes unitários com Pytest.

## Como rodar

```bash
python -m pip install -r requirements.txt
copy .env.example .env
npm run db
python app.py
```

Abra `http://localhost:8080`.

## Bibliotecas usadas

- `nicegui`
- `plotly`
- `pandas`
- `sqlalchemy`
- `psycopg[binary]`
- `python-dotenv`
- `pydantic-settings`
- `loguru`
- `pytest`
- `xai-sdk`

## Como testar

```bash
python -m pytest -q
```

Testes focados:

```bash
python -m pytest tests/test_observability.py tests/test_xai_live_runner.py -q
```

## Como ver o dashboard live

1. Suba o banco com `npm run db`.
2. Rode `python app.py`.
3. Acesse `http://localhost:8080`.
4. Abra Live Dashboard.
5. Clique em `Executar xAI Compact`.

## Como ler logs

- Pela UI: página Logs.
- No banco: `test_runs`, `test_events`, `api_requests`, `api_responses`.
- Exports locais: `exports/logs/`.

## Como gerar contexto

1. Execute a sequência xAI no Live Dashboard.
2. Abra Context Builder.
3. Revise o contexto técnico gerado dos eventos reais.
4. Clique em Exportar Relatórios.

## Como gerar relatórios

Use Live Dashboard ou Context Builder:

```txt
exports/reports/
```

Arquivos gerados:

- `observability_report_*.md`
- `observability_report_*.json`
- `observability_report_*.html`

## Como usar o Lead Algorithm Lab

1. Abra Lead Algorithm Lab.
2. Execute um teste local.
3. O resultado grava em `lead_tests` e `logs/lead_tests.jsonl`.

## Como usar o Algorithm Test Lab

1. Abra `http://localhost:8080/algorithm-test-lab`.
2. Selecione `lead_score`.
3. Revise ou crie um caso com input JSON e resultado esperado JSON.
4. Clique em `Executar teste único` ou `Executar suite completa`.
5. Veja passed/failed, score, classificação, latência e diff.
6. Abra Context Builder para gerar contexto técnico para IA.

## Como entender a ferramenta

Leia:

- `USER_GUIDE.md`
- `OPEN_SOURCE_TUTORIAL.md`
- `ALGORITHM_TEST_PLAN.md`

Resumo:

```txt
API ou algoritmo entra no harness
↓
Teste real é executado
↓
JSON estruturado é salvo
↓
Dashboard mostra comportamento
↓
Context Builder gera contexto para IA
```

Ideia central:

```txt
Test Lab simples
↓
Menos tentativa-e-erro
↓
Menos tokens de LLM
↓
Implementação mais rápida
```

## Próximos passos V2

- Separar runner xAI em fases executáveis: connectivity, chat, structured outputs, streaming, agents, voice e benchmark.
- Expandir Algorithm Test Lab para algoritmos customizados por API HTTP.
- Criar harness HTTP para testar APIs de WhatsApp, webhooks e endpoints de SaaS.
- Criar dashboard de taxa de aprovação por algoritmo.
- Adicionar teste real de `/v1/models` e endpoints REST de Responses API.
- Implementar Voice Lab com áudio sintético, STT, TTS, Voice Agent WebSocket e métricas.
- Implementar benchmark com repetições, p95, erro, custo e reliability score.
- Adicionar migrations formais com Alembic.
- Adicionar paginação server-side para volumes altos.
- Adicionar screenshots/e2e de UI.

## Bugs conhecidos

- A UI depende do PostgreSQL para executar live runs; sem banco, abre em modo degradado.
- Export CSV/JSONL grava arquivo local e mostra o caminho, sem download automático pelo navegador.
- O runner compacto usa `xai-sdk`; endpoints REST completos ainda ficam para V2.
- Agents e Voice aparecem como fases bloqueadas até haver fixtures, orçamento e critérios próprios.

## Pendências

- Rodar sequência xAI completa após cada mudança relevante.
- Definir orçamento máximo de chamadas antes dos benchmarks.
- Criar fixture sintética de áudio para Voice Lab.
- Registrar custo real quando a API retornar metadados suficientes.
- Adicionar retenção/limpeza de eventos antigos.
