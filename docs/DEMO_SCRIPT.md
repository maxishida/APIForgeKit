# Demo Script

Roteiro curto para demonstrar o APIForgeKit Studio sem chamar `seed_validation` ou `dry_run_contract` de API real.

## Preparar ambiente

```bash
npm run db
python app.py
```

Abra `http://127.0.0.1:8080`.

## Jornada oficial

### 1. Abrir Tutorial

Abra `/tutorial` e mostre o mapa:

```txt
ACP/CLI/IDE -> SKILL.md -> Labs -> PostgreSQL -> Dashboard -> Context Builder -> Evidence Pack
```

Explique que o produto economiza tokens porque valida antes de pedir implementação para IA.

### 2. Rodar Algorithm Suite

Abra `/algorithm-test-lab` e rode a canonical suite `lead_score`.

Resultado esperado:

- `17/17 passed`
- invariantes OK
- evidence_mode `seed_validation`

Opcional via CLI:

```bash
npm run algorithm:suite
python run_acp_prompt.py "/validate-lead-score"
```

### 3. Rodar API Contract Dry-run

Abra `/api-test-lab`.

- Rode `Run Contract Dry-run` na suite `whatsapp_validation_pack`.
- Mostre que o resultado fica marcado como `dry_run_contract`.
- Explique que `Run Real HTTP` exige URL real, credenciais e confirmação.

### 4. Ver Dashboard

Abra `/live-dashboard`.

Mostre:

- total de testes
- latência média/P95
- modos de evidência
- falhas recentes
- último evento

### 5. Abrir Logs

Abra `/logs`.

Mostre:

- filtros por provider, módulo, status e evidência
- busca por payload
- JSON estruturado com request, response, erro e recomendação

### 6. Gerar Context Builder

Abra `/context-builder`.

- Selecione `Algorithm + API` ou `Full evidence`.
- Verifique readiness: `Ready`, `Needs tests` ou `Has failures`.
- Mostre as abas de contexto, métricas, fontes e JSON exportável.

Opcional via ACP:

```bash
python run_acp_prompt.py "/build-context"
```

### 7. Baixar Evidence Pack

No `/context-builder`:

- Use `Download .md` para baixar contexto rápido para colar em uma IA.
- Use `Export ZIP` para pacote auditável com metadata.
- Use JSON/HTML quando precisar revisar fontes ou compartilhar relatório.
- Mostre que o export também fica registrado em `context_exports`.

### 8. Usar contexto com IA

Feche com um prompt curto:

```txt
Use este contexto técnico validado pelo APIForgeKit.
Implemente somente a lógica confirmada pelos testes.
Não invente endpoints, payloads ou regras.

[cole o contexto gerado]
```

## Tese final

```txt
Teste real ou contrato explícito
-> log estruturado
-> evidência
-> contexto técnico compacto
-> implementação futura com menos retrabalho
```
