# APIForgeKit MVP 100% Functional Map

Este mapa define o que está funcional no MVP, o que é contrato local, o que é seed validation, o que é legado e o que está bloqueado para V2.

## Fluxo oficial

```txt
Teste
↓
Log estruturado
↓
PostgreSQL
↓
Dashboard
↓
Context Builder
↓
Evidence Pack
```

## Modos de evidência

- `real_http`: chamada real de API, SDK ou HTTP externo/local.
- `dry_run_contract`: validação local de contrato usando expected vs actual/mock response.
- `seed_validation`: suite canônica com casos seedados e deterministicamente reproduzíveis.
- `legacy`: recurso preservado para referência, fora do caminho canônico do MVP.
- `blocked`: recurso não executado por falta de credencial, permissão, fixture, orçamento ou escopo V2.

## Status por módulo

| Módulo | Status | Evidência | Observação |
| --- | --- | --- | --- |
| Algorithm Test Lab | Funcional real local | `seed_validation` | Caminho canônico para `lead_score`, expected vs actual, diff e invariantes. |
| Generic API Lab | Funcional | `dry_run_contract` e `real_http` | Dry-run valida contrato; HTTP real exige casos com URL real e confirmação. |
| Live Dashboard / xAI compact runner | Funcional com credencial | `real_http` e `blocked` | Connectivity, chat, structured outputs, streaming e tools rodam com `XAI_API_KEY`. |
| Logs | Funcional | todos os modos | Filtro por provider, módulo, status, evidência, latência e busca JSON. |
| Token Calculator | Funcional como estimativa | `seeded_estimate` | Decisão financeira exige conferir docs oficiais e registrar fonte. |
| Context Builder | Funcional | todos os modos | Readiness: `Ready`, `Needs tests`, `Has failures`. |
| ACP Executor | Funcional local | `seed_validation`, `dry_run_contract`, `blocked` | Executa skill gates e exporta evidência; HTTP real pede permissão. |
| Lead Algorithm Lab | Legacy | `legacy` | Mantido como referência; use Algorithm Test Lab no MVP. |
| Blueprint Archive | Legacy/futuro | `legacy` | Não faz parte do fluxo atual de validação. |
| Voice/Agents xAI | Bloqueado/V2 | `blocked` | Exige fixtures, orçamento e critérios dedicados. |

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
- `voice_tests`
- `agent_tests`

## Comandos de operação

```bash
npm run db
npm run dev
npm run test
npm run algorithm:suite
npm run acp
```

## O que pode ser demonstrado hoje

- Rodar `lead_score` no Algorithm Test Lab com 17 casos canônicos.
- Rodar WhatsApp validation pack como `dry_run_contract`.
- Rodar xAI compact runner com `XAI_API_KEY` configurada.
- Filtrar logs por `evidence_mode`.
- Gerar Context Builder em Markdown, JSON, HTML e ZIP.
- Executar `/validate-lead-score` via ACP e obter evidence ZIP.

## O que não deve ser prometido ainda

- WhatsApp real sem credenciais e casos HTTP reais configurados.
- Voice/Agents xAI como validação concluída.
- Custo financeiro exato sem conferência manual dos docs oficiais.
- Implementação Next.js automática.
- Blueprint como produto final.
