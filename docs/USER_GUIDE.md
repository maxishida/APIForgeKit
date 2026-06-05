# APIForgeKit Studio User Guide

## O que a ferramenta faz

APIForgeKit Studio é um laboratório local para testar APIs e algoritmos antes de construir um SaaS em cima deles.

Ele não começa gerando código. Ele começa gerando evidência.

Isso economiza tokens de LLM porque o usuário entrega para a IA um contexto curto, validado e estruturado, em vez de uma conversa longa com tentativas, prints, docs soltas e suposições.

Fluxo principal:

```txt
Usuário escolhe API ou algoritmo
↓
Harness executa teste real
↓
API ou algoritmo responde
↓
Studio salva JSON estruturado
↓
Dashboard mostra comportamento ao vivo
↓
Token Calculator estima custo quando houver uso de LLM
↓
Context Builder transforma evidência em texto técnico
↓
IA recebe contexto real para implementar com menos chute
```

## O que entra no harness

O usuário pode validar dois tipos principais de coisa:

1. Uma API externa

Exemplos:

- xAI
- WhatsApp API
- gateway de pagamento
- CRM
- webhook
- qualquer endpoint HTTP
- contrato dry-run de webhook ou payload

2. Um algoritmo próprio

Exemplos:

- lead score
- classificação de atendimento
- roteamento de tickets
- recomendação de próxima ação
- detecção de spam
- priorização de vendas

## O que sai do harness

Cada teste gera um evento JSON com:

```json
{
  "event_id": "uuid",
  "timestamp": "",
  "provider": "xai",
  "module": "streaming",
  "test_name": "stream",
  "status": "success",
  "latency_ms": 1200,
  "tokens": {},
  "cost": 0,
  "request": {},
  "response": {},
  "error": null,
  "recommendation": ""
}
```

Esse JSON responde perguntas práticas:

- Qual payload foi enviado?
- Qual resposta voltou?
- Quanto demorou?
- Deu erro?
- O erro veio em qual formato?
- O resultado bate com o esperado?
- O que precisa ser feito na próxima implementação?

## Como o usuário usa

1. Rodar o Studio:

```bash
npm run db
python app.py
```

2. Abrir:

```txt
http://localhost:8080
```

3. Escolher o laboratório:

- Home para apresentação limpa e ações rápidas.
- API Provider Lab para APIs de IA e logs ao vivo.
- Generic API Lab para APIs, webhooks, contratos e WhatsApp pack.
- Algorithm Test Lab para validar algoritmo determinístico com input, expected output e diff.
- xAI Voice Lab para validar TTS, STT, resposta do agente e logs de contato.
- Token Calculator para custo por usuário e economia de contexto.
- Lead Algorithm Lab legado para referência local antiga.
- Logs para ver JSON completo.
- Context Builder para gerar contexto técnico.

4. Executar o teste.

5. Ler o resultado no dashboard.

6. Exportar relatório.

## Como isso ajuda a construir SaaS

Antes de criar telas, banco definitivo, filas, workers ou integrações de produção, o Studio mostra como a API ou algoritmo se comporta de verdade.

Com isso, a IA recebe contexto melhor:

- payloads reais
- respostas reais
- erros reais
- latências reais
- contratos esperados
- limitações conhecidas
- recomendações técnicas

Esse contexto pode ser colado em uma IA para pedir implementação de SaaS com mais precisão.

## Exemplo: xAI

Hoje o Studio já executa uma sequência compacta xAI:

- autenticação
- chat básico
- structured output
- streaming
- function calling

O resultado aparece no Live Event Stream e é salvo no PostgreSQL.

## Exemplo: algoritmo de lead

No Algorithm Test Lab, o usuário seleciona `lead_score` e pode clicar em `Run Canonical Suite` para rodar a suíte pronta com:

1. lead frio Instagram
2. lead morno Landing Page
3. lead quente WhatsApp
4. lead urgente ligação
5. lead inválido mensagem vazia
6. lead spam
7. lead sem contato
8. cliente anterior com alta intenção

Cada caso compara:

```txt
input JSON
↓
resultado esperado JSON
↓
resultado real do algoritmo
↓
diff
↓
passed/failed
```

No Lead Algorithm Lab antigo, o usuário também pode preencher:

- origem
- mensagem
- orçamento
- urgência
- interesse
- telefone/e-mail
- histórico

O Studio retorna:

- score
- classificação
- motivos
- recomendação
- JSON estruturado

Isso permite validar se o algoritmo é bom antes de transformar em endpoint, dashboard comercial ou automação.

## Exemplo: WhatsApp API ou webhook

No Generic API Lab, o usuário seleciona `whatsapp_validation_pack` e roda uma suite dry-run.

Ela valida:

- payload de mensagem outbound
- payload de webhook com intenção de lead
- erro de contrato sem telefone
- risco de spam

Cada caso compara:

```txt
request JSON
↓
expected response
↓
actual/mock response
↓
diff
↓
passed/failed
```

Isso permite desenhar a integração antes de gastar chamadas reais ou pedir para a IA adivinhar o payload.

## Exemplo: custo por usuário

No Token Calculator, o usuário escolhe provider/modelo e informa:

- usuários
- requests por usuário por dia
- dias
- tokens de input por request
- tokens de output por request
- tokens em cache, quando existir
- fonte oficial e preços verificados quando usar `docs_verified`

O Studio estima:

- requests totais
- tokens totais
- custo total
- custo por usuário
- economia ao trocar prompt cru por contexto técnico compacto

Use `seeded_estimate` para planejamento rápido. Use `docs_verified` somente depois de conferir a página oficial do provider e revisar os preços de input, output e cache.

## Regra operacional

Não construir em cima de suposição.

Sempre seguir:

```txt
Teste
↓
Log
↓
Evidência
↓
Contexto
↓
Implementação
```
