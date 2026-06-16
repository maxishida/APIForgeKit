# APIForgeKit Open Source Tutorial

## Ideia simples

APIForgeKit é um Test Lab local para economizar tempo e tokens de LLM durante desenvolvimento.

Em vez de pedir para uma IA adivinhar uma API, webhook ou algoritmo, você roda validações primeiro.

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
↓
IA implementa depois
```

## Para quem é

- Devs construindo SaaS com APIs externas.
- Devs validando algoritmo antes de transformar em endpoint.
- Devs testando WhatsApp API, webhooks, CRM, pagamentos ou IA.
- Devs que querem contexto confiável antes de pedir código para uma LLM.

## Instalação local

```bash
git clone https://github.com/maxishida/APIForgeKit.git
cd APIForgeKit
python -m pip install -r requirements.txt
copy .env.example .env
npm run db
python app.py
```

Abra:

```txt
http://localhost:8080
```

## Jornada oficial de 8 passos

### 1. Abrir Tutorial

Abra `/tutorial` para entender a ordem do produto antes de rodar testes.

### 2. Rodar Algorithm Suite

Abra `Algorithm Test Lab`, selecione `lead_score` e clique em `Run Canonical Suite`.

Via CLI:

```bash
npm run algorithm:suite
```

Evidência esperada: `seed_validation`, expected vs actual, diff, invariantes e `17/17 passed`.

### 3. Rodar API Contract Dry-run

Abra `Generic API Lab`, selecione `whatsapp_validation_pack` e clique em `Run Contract Dry-run`.

Evidência esperada: `dry_run_contract`, request, response, diff e recomendação sem chamar API real.

### 4. Ver Dashboard

Abra `API Provider Lab` ou `/live-dashboard`.

Confira métricas, latência, modos de evidência, falhas recentes e último evento.

### 5. Abrir Logs

Abra `Logs`.

Use filtros e busca para inspecionar JSON estruturado com request, response, erro, latência e `evidence_mode`.

### 6. Gerar Context Builder

Abra `Context Builder`.

Escolha `Algorithm + API`, `Algorithm only`, `API only`, `ACP Evidence` ou `Full evidence`.

O readiness deve mostrar:

- `Ready`: evidência suficiente.
- `Needs tests`: falta rodar suite.
- `Has failures`: existem diffs ou erros.

Via ACP:

```bash
python run_acp_prompt.py "/build-context"
```

### 7. Baixar Evidence Pack

No `Context Builder`:

- `Download .md`: contexto rápido para colar em uma IA.
- `Export ZIP`: pacote auditável com metadata.
- `Export JSON/HTML`: revisão técnica e compartilhamento.
- `context_exports`: trilha no PostgreSQL com os caminhos Markdown, JSON, HTML e ZIP.

### 8. Usar contexto com IA

Use um prompt curto:

```txt
Use este contexto técnico validado pelo APIForgeKit.
Implemente somente a lógica confirmada pelos testes.
Não invente endpoints, payloads ou regras.

[cole o contexto gerado]
```

## Por que isso economiza tokens

Sem o lab, o desenvolvedor geralmente cola documentação, código parcial, prints, erros soltos e tentativas anteriores no chat.

Com o lab, o desenvolvedor entrega para a IA um contexto menor:

- payload real ou contrato explícito
- resposta real ou resposta esperada
- erro real
- latência
- diff esperado x recebido
- custo estimado por usuário
- recomendações
- arquivos sugeridos

## Regra de ouro

Não peça implementação antes de ter evidência.

```txt
Validar primeiro
↓
Implementar depois
```

## Como contribuir

Boas primeiras issues:

- Adicionar novo algoritmo seed.
- Criar novo validation pack de API.
- Melhorar filtros de logs.
- Criar relatório de custo por provider.
