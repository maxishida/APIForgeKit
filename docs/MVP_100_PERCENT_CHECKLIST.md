# APIForgeKit MVP 100% Functional Checklist

Use este checklist antes de apresentação, release ou gravação.

## Ambiente

- [ ] Banco online com `npm run db`.
- [ ] `.env` configurado quando testes reais de provider forem usados.
- [ ] UI abre com `npm run dev` ou `python app.py`.
- [ ] Nenhum segredo aparece em logs, prints ou exports.

## Validação automática

- [ ] `python -m pytest -q` passa.
- [ ] `python -m compileall app.py core ui agents run_algorithm_lab.py run_acp_prompt.py` passa.
- [ ] `git diff --check` passa.
- [ ] `npm run algorithm:suite` passa com 17/17 casos.
- [ ] Com a UI rodando, `npm run ui:smoke` retorna HTTP 200 para as páginas principais.

## Labs

- [ ] Algorithm Test Lab executa `lead_score` e grava `seed_validation`.
- [ ] Generic API Lab executa WhatsApp pack e grava `dry_run_contract`.
- [ ] Generic API Lab separa `Run Contract Dry-run` de `Run Real HTTP`.
- [ ] `Run Real HTTP` exige confirmação e URL `http://` ou `https://`.
- [ ] Token Calculator mostra `pricing_mode=seeded_estimate` ou `docs_verified`.
- [ ] `docs_verified` grava `pricing_verified_at` e `pricing_verified_source_url`.
- [ ] Generic API Lab importa suite JSON pelo wizard visual.
- [ ] Live Dashboard registra `real_http` quando provider real roda.
- [ ] Live Dashboard mostra Evidence Modes, P95 Latency, Recent Failures e Last Event.
- [ ] Voice/Agents aparecem como `blocked` até V2.

## Contexto e logs

- [ ] Context Builder exportando Markdown, JSON, HTML e ZIP.
- [ ] Context Builder mostra `Ready`, `Needs tests` ou `Has failures`.
- [ ] Logs filtráveis por provider, módulo, status, evidência, latência e busca.
- [ ] Todo mock/dry-run rotulado como `dry_run_contract`.
- [ ] Evidence Pack inclui caminhos e metadata.

## ACP

- [ ] `/validate-lead-score` retorna `end_turn`, `runId`, `contextPath` e `evidenceZip`.
- [ ] `/validate-api-suite whatsapp_validation_pack --http-real` emite `session/request_permission`.
- [ ] Caminho de permissão retorna `stopReason=refusal`.
- [ ] Sessões/prompts ACP aparecem em `acp_sessions` e `acp_events`.
- [ ] Context Builder mostra `ACP Evidence` quando o harness ACP foi usado.

## Produto e docs

- [ ] Nenhuma página principal usa texto ambíguo de mock ou dry-run.
- [ ] Lead Algorithm Lab está marcado como legacy ou fora do menu principal.
- [ ] Blueprint Archive está marcado como legacy/futuro.
- [ ] README tem passo a passo curto.
- [ ] SKILL está alinhado com evidência antes de implementação.
- [ ] `docs/MVP_100_PERCENT_MAP.md` está atualizado.
- [ ] `docs/SYSTEM_DIAGRAM.md` mostra ACP, SKILL, labs, PostgreSQL, Context Builder e Evidence Pack.
- [ ] `docs/DEMO_SCRIPT.md` guia a demo sem chamar dry-run de API real.
