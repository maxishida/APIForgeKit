# APIForgeKit Studio V1 Implementation Checklist

## O que foi implementado

- NiceGUI local app em `app.py`.
- Shell visual com sidebar, header, cards e tema Dark/Neon Blue.
- Home demo dashboard como tela principal.
- API Provider Lab separado em `/live-dashboard`.
- Tutorial open source dentro da UI em `/tutorial`.
- xAI compact runner acionado pela UI.
- Live Event Stream com atualização periódica.
- Algorithm Test Lab em `/algorithm-test-lab`.
- Generic API Lab em `/api-test-lab`.
- Token Calculator em `/token-calculator`.
- Tabelas: `algorithm_definitions`, `algorithm_test_cases`, `algorithm_test_runs`, `algorithm_test_results`.
- Tabelas: `api_test_suites`, `api_test_cases`, `api_test_runs`, `api_test_results`.
- Tabela: `token_usage_estimates`.
- Suíte `lead_score` com 17 casos prontos, incluindo bordas, conflitos e overrides inválidos.
- Validação forte de payload no Algorithm Test Lab.
- Invariantes de `lead_score` registradas nos logs estruturados.
- Erros de input do algoritmo registrados como evidência estruturada.
- Suite `whatsapp_validation_pack` com casos dry-run prontos.
- Validador esperado x recebido com diff estruturado.
- API harness genérico com método, URL, headers, body, expected output, dry-run e HTTP real.
- Import/export de suites JSON para algoritmo e API.
- Demo Mode para rodar algoritmo, API pack e estimativa de tokens.
- Calculadora de tokens/custo por usuário com preços seedados de docs oficiais.
- Token Calculator com presets de uso, cards de pricing, economia de contexto e histórico.
- Context savings calculator para comparar prompt cru vs contexto técnico.
- Context Builder integrado aos resultados de algoritmo.
- Context Builder integrado a API Lab e Token Calculator.
- Gráficos Plotly para status, módulos, latência e volume de eventos.
- Gráficos de evidência para pass/fail, latência e score no Algorithm/API Lab.
- PostgreSQL Docker com SQLAlchemy.
- Tabelas de observabilidade: `test_runs`, `test_events`, `api_requests`, `api_responses`, `voice_tests`, `agent_tests`, `context_exports`.
- Tela Logs baseada em eventos de observabilidade, com filtros, busca, AG Grid, JSON completo e export CSV/JSONL.
- Context Builder baseado em logs reais.
- Exportação de relatórios Markdown, JSON e HTML.
- Exportação de bundle ZIP com Markdown, JSON e HTML.
- CLI `run_algorithm_lab.py`.
- ACP Skill Executor em `python -m agents.acp_agent`.
- npm helper `npm run acp`.
- ACP `session/new` com comandos disponíveis, `plan`, `agent_message_chunk`, `_meta` e `session/request_permission`.
- ACP `/validate-lead-score` para suite canônica, invariantes e evidence pack.
- Configuração Alembic opcional.
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
- `alembic`
- `agent-client-protocol`

## Como testar

```bash
python -m pytest -q
```

Testes focados:

```bash
python -m pytest tests/test_observability.py tests/test_xai_live_runner.py -q
```

CLI de algoritmo:

```bash
npm run algorithm:suite
```

ACP executor:

```bash
npm run acp
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

## Como usar o Generic API Lab

1. Abra `http://localhost:8080/api-test-lab`.
2. Selecione `whatsapp_validation_pack`.
3. Clique em `Executar Suite`.
4. Veja pass/fail, status HTTP, latência, diff e JSON estruturado.
5. Exporte a suite JSON para compartilhar no GitHub.

## Como usar o Token Calculator

1. Abra `http://localhost:8080/token-calculator`.
2. Escolha provider e modelo.
3. Informe usuários, requests por usuário/dia, dias, input tokens e output tokens.
4. Clique em `Calcular e salvar`.
5. Use `Context Savings` para comparar prompt cru versus contexto técnico.

## Como usar Demo Mode

1. Abra Home.
2. Clique em `Run Full Demo`.
3. O app executa `lead_score`, `whatsapp_validation_pack` e salva uma estimativa de custo.
4. Abra Context Builder para exportar o bundle.

## Como usar o ACP Skill Executor

1. Rode `npm run acp`.
2. Conecte por cliente ACP via stdio.
3. Envie `initialize`.
4. Crie sessão com `session/new` usando `cwd` absoluto.
5. Execute comandos em `session/prompt`, por exemplo `/validate-algorithm lead_score`.
6. Para lead score, prefira `/validate-lead-score` para gerar contexto e bundle de evidências.

O executor segue o `SKILL.md`, grava evidências pelos repositórios existentes e não gera código de produto.

## Como entender a ferramenta

Leia nesta ordem no GitHub:

1. `README.md`
2. `USER_GUIDE.md`
3. `OPEN_SOURCE_TUTORIAL.md`
4. `workflow.md`
5. `architecture.md`
6. `ALGORITHM_TEST_PLAN.md`
7. `XAI_TEST_PLAN.md`
8. `VALIDATION_CHECKLIST.md`
9. `ACP_AGENT_ARCHITECTURE.md`
10. `SKILL.md`
11. Generic API Lab
12. Algorithm Test Lab
13. Token Calculator

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
- Expandir o Generic API Lab com variáveis de ambiente seguras e autenticação guiada.
- Adicionar provider pricing refresh manual com confirmação do usuário.
- Criar dashboard de taxa de aprovação por algoritmo.
- Adicionar teste real de `/v1/models` e endpoints REST de Responses API.
- Implementar Voice Lab com áudio sintético, STT, TTS, Voice Agent WebSocket e métricas.
- Implementar benchmark com repetições, p95, erro, custo e reliability score.
- Adicionar migrations formais com Alembic.
- Evoluir Alembic para cobrir todas as tabelas antigas como baseline versionada.
- Adicionar paginação server-side para volumes altos.
- Adicionar screenshots/e2e de UI.

## Bugs conhecidos

- A UI depende do PostgreSQL para executar live runs; sem banco, abre em modo degradado.
- Export CSV/JSONL grava arquivo local e mostra o caminho, sem download automático pelo navegador.
- O runner compacto usa `xai-sdk`; endpoints REST completos ainda ficam para V2.
- Os preços do Token Calculator são seeds de documentação e devem ser conferidos antes de decisões financeiras.
- O WhatsApp pack é dry-run por padrão; chamadas reais dependem de credenciais e setup do usuário.
- Agents e Voice aparecem como fases bloqueadas até haver fixtures, orçamento e critérios próprios.

## Pendências

- Rodar sequência xAI completa após cada mudança relevante.
- Definir orçamento máximo de chamadas antes dos benchmarks.
- Criar fixture sintética de áudio para Voice Lab.
- Registrar custo real quando a API retornar metadados suficientes.
- Adicionar override de preços por provider/model pela UI.
- Adicionar import de suites pela UI além das funções core.
- Adicionar retenção/limpeza de eventos antigos.
