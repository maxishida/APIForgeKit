# APIForgeKit MVP 100% Functional Checklist

Use este checklist antes de apresentação, release ou gravação.

Última validação completa: 2026-06-22.

Evidência desta rodada:

- `npm run db`: PostgreSQL online em Docker.
- `npm run validate:mvp`: comando único recomendado para validação local via Docker Python.
- `npm run validate:mvp:unix`: equivalente Linux/macOS via `scripts/validate_mvp.sh`.
- `python -m pytest -q`: 177 passed, executado em container Python 3.13.
- `python -m compileall app.py core ui agents scripts run_algorithm_lab.py run_acp_prompt.py run_acp_workflow.py run_xai_voice.py`: OK.
- `git diff --check`: OK.
- `npm run algorithm:suite`: 17/17 passed.
- `npm run acp:workflow`: 9/9 prompts passed.
- UI smoke: 9/9 rotas HTTP 200.
- `npm run demo:clean:dry`: lista artefatos sem apagar.
- Observação de ambiente: `python` no host Windows aponta para alias da Microsoft Store; validação Python foi rodada via Docker `python:3.13-slim`.

Evidência de provider registrada anteriormente, mas não reexecutada nesta validação básica para evitar chamadas pagas:

- `npm run voice:run`: success, 9 eventos `real_http`, run `874ee302-a3cb-484d-9a98-2205f862b7a0`.
- xAI Responses API smoke: `responses_api/basic` success, endpoint `/v1/responses`, preview `api-lab-ok`.

## Ambiente

- [x] Banco online com `npm run db`.
- [x] `.env` configurado quando testes reais de provider forem usados.
- [x] UI abre com `npm run dev` ou `python app.py`.
- [x] Nenhum segredo aparece em logs, prints ou exports.

## Validação automática

- [x] `python -m pytest -q` passa.
- [x] `python -m compileall app.py core ui agents run_algorithm_lab.py run_acp_prompt.py run_acp_workflow.py run_xai_voice.py` passa.
- [x] `git diff --check` passa.
- [x] `npm run algorithm:suite` passa com 17/17 casos.
- [x] `npm run acp:workflow` passa com todas as seções da `SKILL.md`.
- [x] `npm run voice:run` passa quando `XAI_API_KEY` está configurada e há orçamento aprovado.
- [x] Com a UI rodando, `npm run ui:smoke` retorna HTTP 200 para as páginas principais.
- [x] Sem UI aberta, `npm run ui:smoke:local` sobe o app temporariamente e valida as páginas principais.
- [x] `npm run validate:mvp` cobre testes, compile, algoritmo, ACP, UI smoke e limpeza dry-run.
- [x] `npm run validate:mvp:unix` cobre o mesmo fluxo em Linux/macOS via Bash.

## Labs

- [x] Algorithm Test Lab executa `lead_score` e grava `seed_validation`.
- [x] Generic API Lab executa WhatsApp pack e grava `dry_run_contract`.
- [x] Generic API Lab separa `Run Contract Dry-run` de `Run Real HTTP`.
- [x] `Run Real HTTP` exige confirmação e URL `http://` ou `https://`.
- [x] Token Calculator mostra `pricing_mode=seeded_estimate` ou `docs_verified`.
- [x] `docs_verified` usa preços verificados de input/output/cache e grava `pricing_verified_at` + `pricing_verified_source_url` quando salvo.
- [x] Generic API Lab importa suite JSON pelo wizard visual.
- [x] Live Dashboard registra `real_http` quando provider real roda.
- [x] Live Dashboard registra `responses_api/basic` para xAI quando `XAI_API_KEY` está configurada.
- [x] Live Dashboard mostra Evidence Modes, P95 Latency, Recent Failures e Last Event.
- [x] Home mostra Project Health com PostgreSQL, último run xAI, último context export, falhas e evidence modes.
- [x] xAI Voice Lab REST registra `lead_received`, `tts_audio_received`, `transcript_received`, `agent_response_received` e `voice_call_completed`.
- [x] Voice Agent realtime WebSocket e Agents aparecem como `blocked` até V2.

## Contexto e logs

- [x] Context Builder exportando Markdown, JSON, HTML e ZIP.
- [x] Context Builder permite baixar o contexto atual como `.md` direto pela UI.
- [x] Context Builder gera `AI Prompt` final sem inventar payloads, regras ou endpoints.
- [x] Sem Context Builder Ready = não implementar.
- [x] Context Builder mostra `Ready`, `Needs tests` ou `Has failures`.
- [x] Logs filtráveis por provider, módulo, status, evidência, latência e busca.
- [x] Todo mock/dry-run rotulado como `dry_run_contract`.
- [x] Evidence Pack inclui caminhos e metadata.

## ACP

- [x] `/validate-lead-score` retorna `end_turn`, `runId`, `contextPath` e `evidenceZip`.
- [x] `/validate-token-cost` calcula custo/token sem quebrar `/token-cost`.
- [x] `/validate-context-readiness` retorna `Ready`, `Needs tests` ou `Has failures` pelo Context Builder.
- [x] `/validate-context-readiness` grava caminhos Markdown, JSON, HTML e ZIP em `context_exports`.
- [x] `/validate-voice-roundtrip` valida a última evidência de voz salva sem chamar provider real.
- [x] `/validate-voice-roundtrip --run-real` emite `session/request_permission`.
- [x] `npm run acp:workflow` passa com 9 prompts seguindo `SKILL.md` seção por seção.
- [x] `npm run acp:workflow` exige `tool_call_update.rawOutput.status=success` nas etapas de validação; `end_turn` sozinho não basta.
- [x] `/validate-api-suite whatsapp_validation_pack --http-real` emite `session/request_permission`.
- [x] Caminho de permissão retorna `stopReason=refusal`.
- [x] Sessões/prompts ACP aparecem em `acp_sessions` e `acp_events`.
- [x] Context Builder mostra `ACP Evidence` quando o harness ACP foi usado.

## Produto e docs

- [x] Home mostra a jornada oficial de 8 passos.
- [x] Tutorial mostra os 8 passos na mesma ordem da Home.
- [x] README e Demo Script explicam `Download .md` versus `Export ZIP`.
- [x] Nenhuma página principal usa texto ambíguo de mock ou dry-run.
- [x] Lead Algorithm Lab está marcado como legacy ou fora do menu principal.
- [x] Blueprint Archive está marcado como legacy/futuro.
- [x] README tem passo a passo curto.
- [x] README documenta `demo:clean:dry`, `demo:clean`, Responses API e Project Health.
- [x] SKILL está alinhado com evidência antes de implementação.
- [x] `docs/MVP_100_PERCENT_MAP.md` está atualizado.
- [x] `docs/SYSTEM_DIAGRAM.md` mostra ACP, SKILL, labs, PostgreSQL, Context Builder e Evidence Pack.
- [x] `docs/DEMO_SCRIPT.md` guia a demo sem chamar dry-run de API real.
