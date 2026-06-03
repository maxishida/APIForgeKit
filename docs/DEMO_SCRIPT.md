# Demo Script

Roteiro curto para demonstrar o APIForgeKit Studio sem prometer mock como API real.

## 1. Preparar ambiente

```bash
npm run db
python app.py
```

Abra `http://127.0.0.1:8080`.

## 2. Mostrar o mapa

Abra `/tutorial` e explique o fluxo:

```txt
ACP/CLI/IDE -> SKILL.md -> Labs -> PostgreSQL -> Dashboard -> Context Builder -> Evidence Pack
```

## 3. Validar algoritmo

Abra `/algorithm-test-lab` e rode a canonical suite `lead_score`.

Resultado esperado:

- `17/17 passed`
- invariantes OK
- contexto e Evidence Pack disponíveis

Opcional via CLI:

```bash
npm run algorithm:suite
python run_acp_prompt.py "/validate-lead-score"
```

## 4. Validar contrato de API

Abra `/api-test-lab`.

- Rode `Run Contract Dry-run` na suite `whatsapp_validation_pack`.
- Mostre que o resultado fica marcado como `dry_run_contract`.
- Explique que `Run Real HTTP` exige URL real, credenciais e confirmação.

## 5. Calcular uso de tokens

Abra `/token-calculator`.

- Escolha provider/model.
- Use `seeded_estimate` para planejamento.
- Use `docs_verified` somente depois de conferir a fonte oficial.
- Mostre o JSON com `pricing_verified_at` e `pricing_verified_source_url`.

Exemplo ACP:

```bash
python run_acp_prompt.py "/token-cost provider=xai model=grok-4.3 users=10 requests=20 input=1000 output=500 days=30"
```

## 6. Gerar contexto

Abra `/context-builder`.

- Selecione `Full evidence` ou `Algorithm only`.
- Verifique readiness.
- Exporte Markdown, JSON, HTML e ZIP.

## 7. Mostrar observabilidade

Abra `/live-dashboard` e `/logs`.

Mostre:

- Evidence modes
- P95 latency
- Recent failures
- JSON estruturado
- filtros por status/origem/evidência

## 8. Fechar com a tese

O valor do projeto é economizar tempo e token de LLM:

```txt
Teste real ou contrato explícito
-> log estruturado
-> evidência
-> contexto técnico compacto
-> implementação futura com menos retrabalho
```
