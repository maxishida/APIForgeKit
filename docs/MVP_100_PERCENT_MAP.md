# APIForgeKit MVP 100% Functional Map

Este mapa define o que está funcional no MVP, o que é contrato local, o que é seed validation, o que é legado e o que está bloqueado para V2.

## Fluxo oficial

```txt
1. Abrir Tutorial
2. Rodar Algorithm Suite
3. Rodar API Contract Dry-run
4. Ver Dashboard
5. Abrir Logs
6. Gerar Context Builder
7. Baixar Evidence Pack
8. Usar contexto com IA
```

Este fluxo ainda segue a tese técnica: `Teste -> Log estruturado -> PostgreSQL -> Dashboard -> Context Builder -> Evidence Pack -> IA implementa depois`.

## Modos de evidência

- `real_http`: chamada real de API, SDK ou HTTP externo/local.
- `dry_run_contract`: validação local de contrato usando expected vs actual/mock response.
- `seed_validation`: suite canônica com casos seedados e deterministicamente reproduzíveis.
- `protocol_trace`: rastro ACP/CLI/IDE com sessão, prompt, resposta final e gates de permissão.
- `legacy`: recurso preservado para referência, fora do caminho canônico do MVP.
- `blocked`: recurso não executado por falta de credencial, permissão, fixture, orçamento ou escopo V2.

## Status por módulo

| Módulo | Status | Evidência | Observação |
| --- | --- | --- | --- |
| Algorithm Test Lab | Funcional real local | `seed_validation` | Caminho canônico para `lead_score` e `community_bot_engine`, expected vs actual, diff e invariantes. |
| Community Bot Lab | Funcional real local | `seed_validation` | UI `/community-bot-lab` para Vice City NPC Engine: sandbox, suíte 15/15, export e download de contexto. |
| Generic API Lab | Funcional | `dry_run_contract` e `real_http` | Dry-run valida contrato; HTTP real exige casos com URL real e confirmação. |
| Live Dashboard / xAI compact runner | Funcional com credencial | `real_http` e `blocked` | Responses API, connectivity, chat legacy, structured outputs, streaming e tools rodam com `XAI_API_KEY`. |
| xAI Voice Lab REST | Funcional com credencial | `real_http` | TTS gera áudio, STT transcreve, agente responde e eventos entram em Logs/Dashboard/Context Builder. |
| Logs | Funcional | todos os modos | Filtro por provider, módulo, status, evidência, latência e busca JSON. |
| Token Calculator | Funcional como estimativa | `seeded_estimate` | Decisão financeira exige conferir docs oficiais e registrar fonte. |
| Context Builder | Funcional | todos os modos | Readiness: `Ready`, `Needs tests`, `Has failures`; inclui `ACP Evidence` e `Generate AI Prompt`. |
| Project Health | Funcional | todos os modos | Home mostra PostgreSQL, último run xAI, último export de contexto, falhas e modos de evidência. |
| ACP Executor | Funcional local | `protocol_trace`, `seed_validation`, `dry_run_contract`, `blocked` | Executa skill gates, persiste sessão/prompt/resposta e exporta evidência; HTTP real pede permissão. |
| Lead Algorithm Lab | Legacy | `legacy` | Mantido como referência; use Algorithm Test Lab no MVP. |
| Blueprint Archive | Legacy/futuro | `legacy` | Não faz parte do fluxo atual de validação. |
| Voice Agent realtime / Agents xAI | Bloqueado/V2 | `blocked` | WebSocket realtime e Multi Agent exigem orçamento, privacidade, fixtures e critérios dedicados. |

## Tabelas PostgreSQL usadas

- `algorithm_definitions`
- `algorithm_test_cases`
- `algorithm_test_runs`
- `algorithm_test_results`
- `api_test_suites`
- `api_test_cases`
- `api_test_runs`
- `api_test_results`
- `test_runs`
- `test_events`
- `api_requests`
- `api_responses`
- `token_usage_estimates`
- `context_exports`
- `acp_sessions`
- `acp_events`
- `voice_tests`
- `agent_tests`

## Comandos de operação

```bash
npm run db
npm run dev
npm run test
npm run validate:mvp
npm run algorithm:suite
npm run acp
npm run demo:clean:dry
npm run demo:clean
```

`npm run demo:clean` remove somente artefatos gerados/ignorados e preserva código, `tests/*.py`, docs, `.env`, `.context`, banco e `.gitkeep`.

## O que pode ser demonstrado hoje

- Rodar `lead_score` no Algorithm Test Lab com 17 casos canônicos.
- Rodar `community_bot_engine` no Community Bot Lab com 15 casos seed e sandbox de eventos.
- Baixar contexto de implementação via `/download/reports/CODE_GTA6_COMMUNITY_BOT_ENGINE_IMPLEMENTATION_CONTEXT.md`.
- Rodar WhatsApp validation pack como `dry_run_contract`.
- Rodar xAI compact runner com `XAI_API_KEY` configurada.
- Ver `responses_api/basic` como evidência preferida para xAI text.
- Rodar xAI Voice Lab REST com `XAI_API_KEY` configurada.
- Filtrar logs por `evidence_mode`.
- Gerar Context Builder em Markdown, JSON, HTML e ZIP.
- Gerar AI Prompt final baseado em evidências.
- Baixar `Download .md` para contexto rápido.
- Confirmar que Markdown, JSON, HTML e ZIP foram registrados em `context_exports`.
- Executar `/validate-lead-score` via ACP e obter evidence ZIP.
- Ver rastro ACP no Context Builder como `ACP Evidence`.

## O que não deve ser prometido ainda

- WhatsApp real sem credenciais e casos HTTP reais configurados.
- Voice Agent realtime WebSocket ou Multi Agent como validação concluída.
- Custo financeiro exato sem conferência manual dos docs oficiais.
- Implementação Next.js automática.
- Blueprint como produto final.
