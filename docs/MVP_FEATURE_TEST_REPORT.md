# MVP Feature Test Report

Este relatório resume a validação operacional do MVP e aponta onde otimizar antes de uma release pública maior.

## Test Sequence

Sequência recomendada para validar o projeto inteiro:

```bash
npm run db
python -m pytest -q
python -m compileall app.py core ui agents run_algorithm_lab.py run_acp_prompt.py run_acp_workflow.py run_xai_voice.py
git diff --check
npm run algorithm:suite
npm run acp:workflow
npm run voice:run
```

Smokes de UI:

```txt
GET / -> 200
GET /algorithm-test-lab -> 200
GET /api-test-lab -> 200
GET /voice-lab -> 200
GET /live-dashboard -> 200
GET /logs -> 200
GET /token-calculator -> 200
GET /context-builder -> 200
GET /tutorial -> 200
```

## Current Feature Map

| Area | Status | Evidence |
| --- | --- | --- |
| Algorithm Test Lab | Functional | `seed_validation`, expected vs actual, invariants and evidence ZIP. |
| Generic API Lab | Functional | `dry_run_contract`; `real_http` requires URL and confirmation. |
| Live Dashboard | Functional | Observability events with `evidence_mode` filters. |
| Logs | Functional | Search and filters by provider, status, module and `evidence_mode`. |
| Token Calculator | Functional | `seeded_estimate`; financial decisions require official pricing docs. |
| Context Builder | Functional | Markdown, JSON, HTML and ZIP exports with readiness. |
| ACP Harness | Functional | stdio server plus `run_acp_prompt.py` for CLI/IDE smoke prompts. |
| xAI Voice Lab REST | Functional with credential | TTS, STT, agent response and voice events saved as `real_http`. |
| xAI Voice Agent realtime / Agents | Blocked/V2 | Needs fixtures, budget, privacy rules and realtime/agent acceptance criteria. |

## Latest Checklist Run

Executed on June 5, 2026:

- Pytest: `118 passed`
- Compile: OK
- Algorithm suite: `17/17 passed`
- UI smoke: 9/9 routes returned HTTP 200
- ACP workflow: 6/6 prompts passed
- xAI Voice REST: success, 9 `real_http` events, classification `sales_intent`
- Docs cleanup: removed obsolete `VALIDATION_CHECKLIST.md` and internal historical implementation plan

## Optimization Backlog

1. Add a small persisted table for ACP sessions if auditability of editor runs becomes important.
2. Add a UI import wizard for Generic API suites so users can paste endpoint contracts without touching JSON files.
3. Add a lightweight fixture manager for voice/audio so REST voice regressions can run without spending API credits.
4. Extend Token Calculator beyond text-token pricing into provider-specific tools, batch, voice and media costs.
5. Add CI jobs for PostgreSQL integration tests and NiceGUI route smokes.
6. Add a release checklist that verifies no `legacy`, `blocked` or `dry_run_contract` evidence is presented as real production behavior.

## Code Review Notes

- Keep `Algorithm Test Lab` as the canonical score path; avoid reviving the legacy lead form as a primary route.
- Keep `dry_run_contract` visible in API results and context exports.
- Treat `run_acp_prompt.py` as the simplest local harness bridge for IDE or CLI usage.
- Keep generated evidence in ignored `exports/reports/`; commit only docs, tests and source code.

## Next Adjustments

- Improve dashboard density once more providers are validated.
- Add automated reminders to re-check official provider pricing docs before financial decisions.
- Add sample MCP stdio configuration snippets for editor clients that support MCP through ACP.
