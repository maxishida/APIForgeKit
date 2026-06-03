# MVP Feature Test Report

Este relatório resume a validação operacional do MVP e aponta onde otimizar antes de uma release pública maior.

## Test Sequence

Sequência recomendada para validar o projeto inteiro:

```bash
npm run db
python -m pytest -q
python -m compileall app.py core ui agents run_algorithm_lab.py run_acp_prompt.py
git diff --check
npm run algorithm:suite
python run_acp_prompt.py "/validate-lead-score"
python run_acp_prompt.py "/validate-api-suite whatsapp_validation_pack --http-real"
```

Smokes de UI:

```txt
GET / -> 200
GET /algorithm-test-lab -> 200
GET /api-test-lab -> 200
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
| xAI Voice/Agents | Blocked/V2 | Needs fixtures, budget, privacy rules and official endpoint validation. |

## Optimization Backlog

1. Add a small persisted table for ACP sessions if auditability of editor runs becomes important.
2. Add a UI import wizard for Generic API suites so users can paste endpoint contracts without touching JSON files.
3. Add a lightweight fixture manager for voice/audio before enabling real voice validation.
4. Add provider pricing verification timestamps when a user confirms `docs_verified` costs.
5. Add CI jobs for PostgreSQL integration tests and NiceGUI route smokes.
6. Add a release checklist that verifies no `legacy`, `blocked` or `dry_run_contract` evidence is presented as real production behavior.

## Code Review Notes

- Keep `Algorithm Test Lab` as the canonical score path; avoid reviving the legacy lead form as a primary route.
- Keep `dry_run_contract` visible in API results and context exports.
- Treat `run_acp_prompt.py` as the simplest local harness bridge for IDE or CLI usage.
- Keep generated evidence in ignored `exports/reports/`; commit only docs, tests and source code.

## Next Adjustments

- Improve dashboard density once more providers are validated.
- Add a `docs_verified` pricing mode workflow tied to official provider URLs.
- Add sample MCP stdio configuration snippets for editor clients that support MCP through ACP.
