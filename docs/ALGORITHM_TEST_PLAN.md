# Algorithm Validation Plan

## Objetivo

Transformar o APIForgeKit Studio em um jeito simples de validar algoritmos usando site, formulário ou API.

Status atual:

- Algorithm Test Lab implementado em `/algorithm-test-lab`.
- Algoritmos canônicos: `lead_score` (17 casos) e `community_bot_engine` (15 casos — Vice City NPC Engine).
- Casos seed com bordas, idempotência, cooldown, condições e overrides inválidos.
- Persistência em PostgreSQL.
- Diff esperado x recebido.
- Validação forte de payload antes de executar o algoritmo.
- Erros de input são gravados como evidência estruturada, sem derrubar a suíte.
- Context Builder integrado.
- API harness genérico implementado em `/api-test-lab`.
- Import/export de suites JSON.
- Dashboard de evidência com pass/fail, score e latência.
- ACP Skill Executor disponível em `npm run acp`.
- Boas práticas ACP para score/leads documentadas em `SKILL.md` e `ACP_AGENT_ARCHITECTURE.md`.

O usuário deve conseguir entender:

- quais entradas o algoritmo recebe
- qual saída ele gera
- por que ele tomou aquela decisão
- quais casos funcionam
- quais casos falham
- se o algoritmo está pronto para virar produto

## Fluxo ideal

```txt
Usuário escolhe algoritmo
↓
Define entradas
↓
Roda casos de teste
↓
Recebe score/classificação/decisão
↓
Vê motivos e JSON completo
↓
Compara comportamento esperado x real
↓
Gera relatório técnico
```

## Fluxo ACP para lead score

Quando o usuário validar score de leads via agente/editor, o fluxo deve ser:

```txt
/validate-lead-score
↓
ACP session/new com cwd absoluto
↓
available_commands_update
↓
plan: classificar, rodar suite, verificar invariantes, comparar, exportar evidence pack
↓
Algorithm Test Lab
↓
PostgreSQL evidence
↓
agent_message_chunk com resumo
↓
Context Builder + Lead Score Evidence Pack
```

Regra:

```txt
ACP não implementa Next.js.
ACP executa validação, coleta evidência e entrega contexto técnico.
```

## Tipos de algoritmo que o Studio deve suportar

### 1. Algoritmo local Python

Exemplo atual:

- Lead Score

Execução:

```txt
NiceGUI form
↓
Python function
↓
JSON output
↓
PostgreSQL logs
↓
Dashboard
```

### 2. Algoritmo exposto por API

Exemplo futuro:

```txt
POST https://meusite.com/api/score
```

Payload:

```json
{
  "lead_name": "Maria",
  "source": "WhatsApp",
  "message": "Quero orçamento hoje",
  "urgency": "alta",
  "interest": "alto"
}
```

Resposta esperada:

```json
{
  "score": 85,
  "classification": "hot",
  "reasons": ["Mensagem contém orçamento", "Urgência alta"],
  "recommended_action": "Enviar para atendimento humano"
}
```

### 3. Algoritmo usado dentro de um site

Exemplo:

- formulário de captura de lead
- quiz
- simulador
- calculadora
- triagem de atendimento

Execução:

```txt
Usuário preenche site
↓
Site chama API
↓
API roda algoritmo
↓
Studio registra request/response
↓
Dashboard mostra comportamento
```

## Fase 1 - Explicar o algoritmo para o usuário

Criar uma tela "Algorithm Lab" com linguagem simples:

- Nome do algoritmo
- O que ele decide
- Entradas necessárias
- Saídas esperadas
- Regras principais
- Casos de exemplo

Critério de aceite:

- Um usuário não técnico entende para que o algoritmo serve.
- Um desenvolvedor entende quais campos precisa enviar.

## Fase 2 - Rodar casos manuais

Permitir que o usuário preencha um formulário e rode um caso.

Campos mínimos:

- nome do caso
- origem do dado
- payload de entrada
- resultado esperado
- observações

Saída:

```json
{
  "case_id": "uuid",
  "algorithm": "lead_score",
  "status": "passed",
  "input": {},
  "expected": {},
  "actual": {},
  "diff": {},
  "latency_ms": 0,
  "recommendation": ""
}
```

Critério de aceite:

- O usuário consegue ver claramente se o resultado passou ou falhou.

## Fase 3 - Rodar bateria de testes

Adicionar botão:

```txt
Executar suíte de algoritmo
```

Casos iniciais para Lead Score:

- lead quente
- lead morno
- lead frio
- lead inválido por mensagem vazia
- lead inválido por spam
- lead sem contato
- lead com urgência alta
- lead de ligação
- lead de WhatsApp
- cliente recorrente

Casos de borda cobertos no seed atual:

- score 30 deve continuar `cold_lead`
- primeiro score prático acima de 30 deve virar `warm_lead`
- score 60 deve continuar `warm_lead`
- primeiro score prático acima de 60 deve virar `hot_lead`
- score 80 deve continuar `hot_lead`
- primeiro score prático acima de 80 deve virar `urgent_lead`
- alta intenção sem contato deve aplicar penalidade
- cliente anterior com baixa intenção deve continuar explicável pelos motivos
- mensagem inválida deve sobrescrever qualquer score
- spam deve sobrescrever qualquer score

Critério de aceite:

- A suíte gera múltiplos eventos.
- O dashboard mostra taxa de aprovação.
- O relatório aponta os casos que falharam.

## Fase 4 - Testar algoritmo por API

Status: implementado como Generic API Lab para endpoints HTTP ou dry-run contract tests.

Campos:

- nome do algoritmo
- método HTTP
- URL
- headers seguros
- payload JSON
- caminho da resposta onde está a decisão
- resultado esperado

Exemplo:

```json
{
  "name": "Lead Score API",
  "method": "POST",
  "url": "http://localhost:3000/api/leads/score",
  "payload": {
    "message": "Quero comprar agora pelo WhatsApp",
    "source": "WhatsApp"
  },
  "expected": {
    "classification": "hot"
  }
}
```

Critério de aceite:

- O Studio valida APIs locais ou remotas sem precisar alterar o código do algoritmo.
- O usuário pode validar webhook/payload antes de ter credencial real.

## Fase 5 - Criar comparação esperado x real

Para cada caso, mostrar:

- passou/falhou
- campo esperado
- valor esperado
- valor real
- diferença
- impacto

Exemplo:

```txt
Esperado: classification = hot
Real: classification = warm
Impacto: regra de urgência ou origem pode estar fraca
```

Critério de aceite:

- Usuário entende por que o teste falhou.

## Fase 6 - Dashboard de algoritmo

Cards:

- total de casos
- passou
- falhou
- inválidos
- latência média
- taxa de aprovação
- score médio
- última execução

Gráficos:

- status dos casos
- distribuição de score
- falhas por regra
- latência por execução
- evolução de aprovação

Critério de aceite:

- O usuário consegue decidir se o algoritmo está pronto.

Métricas que devem aparecer para uma apresentação gravável:

- total de testes executados
- total passed/failed
- taxa de aprovação
- score médio
- latência média
- última execução
- distribuição por classificação
- casos com diff

## Fase 7 - Context Builder para algoritmo

Gerar contexto técnico com:

- objetivo do algoritmo
- entradas
- saídas
- regras validadas
- casos que passaram
- casos que falharam
- exemplos de payload
- recomendações
- contrato sugerido para API

Formato:

```txt
Contexto Técnico - Algorithm Validation Lab

Objetivo
Entradas
Saídas
Regras
Casos de Teste
Falhas
Payloads
Comportamentos Esperados
Recomendações
```

Critério de aceite:

- O contexto pode ser colado em uma IA para pedir implementação de site, API ou SaaS.

## Primeira suíte recomendada: Lead Score

Invariantes obrigatórios:

- mesmo input gera mesmo output
- score fica entre 0 e 100
- `invalid_lead` tem prioridade sobre qualquer pontuação
- cada ponto positivo ou penalidade aparece em `reasons`
- diff esperado x recebido reprova o caso
- payload inválido reprova o caso e gera erro estruturado
- nenhuma LLM decide o score no MVP determinístico

### Caso 1 - Lead quente

Entrada:

```json
{
  "source": "WhatsApp",
  "message": "Quero comprar hoje, preciso de orçamento urgente",
  "urgency": "alta",
  "interest": "alto",
  "has_phone": true,
  "has_email": true,
  "previous_customer": false
}
```

Esperado:

```json
{
  "classification": "urgent_lead",
  "min_score": 80
}
```

### Caso 2 - Lead morno

Entrada:

```json
{
  "source": "Instagram",
  "message": "Tenho interesse, queria saber melhor como funciona",
  "urgency": "media",
  "interest": "medio",
  "has_phone": false,
  "has_email": true,
  "previous_customer": false
}
```

Esperado:

```json
{
  "classification": "warm_lead",
  "min_score": 31,
  "max_score": 60
}
```

### Caso 3 - Lead inválido

Entrada:

```json
{
  "source": "Landing Page",
  "message": "",
  "urgency": "baixa",
  "interest": "baixo",
  "has_phone": false,
  "has_email": false,
  "previous_customer": false
}
```

Esperado:

```json
{
  "classification": "invalid_lead"
}
```

## Próxima entrega sugerida

Expandir a página existente:

```txt
Algorithm Validation Lab
```

Com:

- UI para importar suites JSON pelo navegador
- variáveis seguras por suite
- validação por JSONPath
- packs prontos para WhatsApp, Stripe, Supabase e CRMs
- relatórios comparando custo/token por algoritmo quando usar LLM

## Próxima entrega recomendada para ficar 100%

1. Exibir invariantes no dashboard do Algorithm Test Lab.
2. Criar tela comparativa de regras: origem, urgência, interesse, contato, histórico e penalidades.
3. Adicionar benchmark local com média, p95 e maior latência.
4. Publicar exemplos JSON em GitHub para usuários copiarem e adaptarem.
5. Adicionar import/export pela UI, não apenas pelas funções core/CLI.
6. Criar versionamento de pesos para comparar `lead_score` V1, V2 e experimentos.
