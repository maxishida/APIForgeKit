# APIForgeKit MVP Test Checklist

Use este checklist para validar o MVP antes de demo, release, gravação ou mudança grande.

Última execução registrada: 2026-06-20.

## 1. Ambiente

- [x] Docker Desktop ativo.
- [x] PostgreSQL online com `npm run db`.
- [x] `.env` presente quando testes reais de provider forem usados.
- [x] `XAI_API_KEY` presente para xAI Voice e Responses API.
- [x] Se o host não tiver Python real, usar Docker `python:3.13-slim` como runner de validação.

## 2. Sequência Base

Comando recomendado:

```bash
npm run validate:mvp
```

Este comando usa Docker `python:3.13-slim`, sobe PostgreSQL, roda testes, compile, Algorithm Suite, ACP workflow, UI smoke local e limpeza em dry-run.

Quando Python local estiver funcional e você quiser rodar manualmente:

```bash
npm run db
python -m pytest -q
python -m compileall app.py core ui agents scripts run_algorithm_lab.py run_acp_prompt.py run_acp_workflow.py run_xai_voice.py
git diff --check
npm run algorithm:suite
npm run acp:workflow
npm run ui:smoke:local
```

Fallback usado em 2026-06-20, porque `python` no host Windows apontava para alias da Microsoft Store:

```bash
docker run --rm -v "${PWD}:/app" -w /app \
  -e DATABASE_URL="postgresql+psycopg://apiforgekit:apiforgekit@host.docker.internal:5432/apiforgekit" \
  python:3.13-slim bash -lc \
  "python -m pip install --no-cache-dir -r requirements.txt >/tmp/pip-install.log \
  && python -m pytest -q \
  && python -m compileall app.py core ui agents scripts run_algorithm_lab.py run_acp_prompt.py run_acp_workflow.py run_xai_voice.py \
  && python run_algorithm_lab.py --suite lead_score --export \
  && python run_acp_workflow.py \
  && python scripts/ui_smoke_local.py"
```

Resultado de 2026-06-20:

- [x] Pytest: `147 passed`.
- [x] Compile: OK.
- [x] Algorithm suite: `17/17 passed`.
- [x] ACP workflow: `9/9 prompts passed`.
- [x] UI smoke local: 9/9 rotas HTTP 200.
- [x] `git diff --check`: OK.

## 2.1 Provider Real Opcional

```bash
npm run validate:mvp:provider
```

Esse comando roda a validação base e depois executa xAI Voice REST + xAI Responses API real. Use apenas com `XAI_API_KEY`, orçamento e aprovação explícita.

## 3. Features Canônicas

- [x] Home carrega e mostra Project Health.
- [x] Tutorial carrega a jornada oficial.
- [x] Algorithm Test Lab valida `lead_score` e grava `seed_validation`.
- [x] Generic API Lab valida WhatsApp pack em `dry_run_contract`.
- [x] Generic API Lab bloqueia HTTP real sem permissão explícita.
- [x] Token Calculator tem modo `seeded_estimate` e `docs_verified`.
- [x] Context Builder exporta Markdown, JSON, HTML e ZIP.
- [x] Context Builder gera AI Prompt sem inventar payloads, regras ou endpoints.
- [x] Logs filtram provider, módulo, status, evidência, latência e busca.
- [x] Live Dashboard mostra eventos, evidence modes, falhas recentes e latência.
- [x] ACP executa `SKILL.md` sem gerar código de produto.

## 4. Provider Real

- [x] xAI Voice REST: `python run_xai_voice.py --export-report`.
- [x] Voice run de 2026-06-20: `874ee302-a3cb-484d-9a98-2205f862b7a0`.
- [x] Voice registrou 9 eventos `real_http`.
- [x] Eventos obrigatórios presentes: `lead_received`, `user_message_received`, `tts_audio_received`, `transcript_received`, `agent_response_received`, `voice_call_completed`.
- [x] xAI Responses API smoke: `responses_api/basic` com endpoint `https://api.x.ai/v1/responses`.
- [x] Responses API retornou preview `api-lab-ok`.

## 5. Evidência e Limpeza

- [x] Evidence Packs gerados em `exports/reports/`.
- [x] `npm run demo:clean:dry` lista caches e exports sem apagar.
- [x] `.env`, banco Docker e `tests/` não entram na limpeza.
- [x] Before running `npm run demo:clean`, preserve exports if Project Health depends on them.
- [x] Segredos não devem aparecer em logs, commits ou exports.

## 6. Pendências Operacionais

- [ ] Corrigir Python local no Windows ou documentar Docker runner como caminho oficial de teste.
- [ ] Rodar `npm run demo:clean` apenas antes de demo limpa, sabendo que remove exports gerados.
- [ ] Manter xAI Voice/Responses real atrás de orçamento e aprovação explícita.
