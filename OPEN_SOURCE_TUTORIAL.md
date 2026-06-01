# APIForgeKit Open Source Tutorial

## Ideia simples

APIForgeKit é um Test Lab local para economizar tempo e tokens de LLM durante desenvolvimento.

Em vez de pedir para uma IA adivinhar uma API, webhook ou algoritmo, você roda testes reais primeiro.

```txt
Teste real
↓
JSON estruturado
↓
Relatório curto
↓
Contexto técnico
↓
Prompt menor e melhor para LLM
```

## Por que isso economiza tokens

Sem o lab, o desenvolvedor geralmente cola muita documentação, código parcial, prints, erros soltos e tentativas anteriores no chat.

Com o lab, o desenvolvedor entrega para a IA um contexto menor:

- payload real
- resposta real
- erro real
- latência
- diff esperado x recebido
- custo estimado por usuário
- recomendações
- arquivos sugeridos

Isso reduz conversa repetida e evita que a IA implemente em cima de suposição.

## Para quem é

- Devs construindo SaaS com APIs externas.
- Devs validando algoritmo antes de transformar em endpoint.
- Devs testando WhatsApp API, webhooks, CRM, pagamentos ou IA.
- Devs que querem gerar contexto confiável antes de pedir código para uma LLM.

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

O mesmo conteúdo também aparece dentro do app em:

```txt
http://localhost:8080/tutorial
```

## Tutorial 1 - Testar algoritmo puro

1. Abra `Algorithm Test Lab`.
2. Selecione `lead_score`.
3. Clique em `Run Demo Suite`.
4. Veja os casos `passed` e `failed`.
5. Abra o JSON estruturado.
6. Abra `Context Builder`.
7. Copie o contexto para sua IA.

Fluxo:

```txt
Test Case
↓
Algorithm Runner
↓
Expected Output Validator
↓
Structured Log
↓
PostgreSQL
↓
Context Builder
```

## Tutorial 2 - Testar xAI

1. Adicione `XAI_API_KEY` no `.env`.
2. Abra `Live Dashboard`.
3. Clique em `Executar xAI Compact`.
4. Veja o Live Event Stream.
5. Exporte relatório.
6. Use o relatório como contexto para futura implementação.

## Tutorial 3 - Testar API ou webhook

1. Abra `Generic API Lab`.
2. Selecione `whatsapp_validation_pack`.
3. Clique em `Executar Suite`.
4. Abra o JSON estruturado de cada caso.
5. Confira request, response, status HTTP, diff e recomendação.
6. Exporte a suite JSON para versionar no GitHub.

Fluxo:

```txt
API Test Case
↓
HTTP/Dry-run Runner
↓
Expected Output Validator
↓
Structured Log
↓
PostgreSQL
↓
Context Builder
```

## Tutorial 4 - Calcular custo antes de implementar

1. Abra `Token Calculator`.
2. Escolha provider e modelo.
3. Informe usuários, requests por usuário/dia, dias, input tokens e output tokens.
4. Clique em `Calcular e salvar`.
5. Use `Context Savings` para comparar prompt cru versus contexto técnico.

Essa tela ajuda a responder:

- quanto custa por usuário?
- quanto custa repetir esse prompt por mês?
- quanto o Context Builder economiza em tokens?
- vale usar modelo maior ou menor?

## Tutorial 5 - Usar contexto em uma LLM

Depois de gerar contexto, use um prompt curto:

```txt
Use este contexto técnico validado pelo APIForgeKit.
Implemente somente a lógica confirmada pelos testes.
Não invente endpoints, payloads ou regras.

[cole o contexto gerado]
```

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
- Criar harness HTTP genérico.
- Adicionar import/export de suites.
- Melhorar gráficos do Algorithm Test Lab.
- Adicionar novos API packs: WhatsApp, Stripe, Supabase, CRM.
- Adicionar presets de preço por provider/model.
- Criar fixtures sintéticas para Voice Lab.
- Adicionar exemplos de WhatsApp API.

Antes de abrir PR:

```bash
python -m pytest -q
```

Inclua no PR:

- o que foi validado
- qual JSON foi gerado
- qual relatório/contexto saiu
- prints ou resumo do dashboard quando fizer sentido
