# APIForgeKit Docs Summary

Este diretório guarda a documentação detalhada do APIForgeKit Studio.

A raiz do repositório deve ficar simples:

- `README.md`: guia rápido para instalar, rodar e entender.
- `SKILL.md`: contrato operacional para agentes.

## Comece por aqui

1. [User Guide](./USER_GUIDE.md): explicação simples da ferramenta.
2. [Open Source Tutorial](./OPEN_SOURCE_TUTORIAL.md): passo a passo para economizar tokens usando evidências.
3. [MVP 100% Map](./MVP_100_PERCENT_MAP.md): separa real, dry-run, seed, legacy e blocked.
4. [MVP 100% Checklist](./MVP_100_PERCENT_CHECKLIST.md): checklist antes de apresentação/release.
5. [MVP Feature Test Report](./MVP_FEATURE_TEST_REPORT.md): sequência de testes e backlog de otimização.
6. [System Diagram](./SYSTEM_DIAGRAM.md): fluxo completo de ACP/SKILL até Evidence Pack.
7. [Demo Script](./DEMO_SCRIPT.md): roteiro curto para vídeo, onboarding e validação visual.
8. [Workflow](./workflow.md): fluxo `teste -> logs -> evidências -> contexto`.
9. [Architecture](./architecture.md): arquitetura local-first com NiceGUI, PostgreSQL e labs.
10. [Implementation Checklist](./IMPLEMENTATION_CHECKLIST.md): o que já existe e como testar.

## Labs

- [Algorithm Test Plan](./ALGORITHM_TEST_PLAN.md): validação de algoritmos determinísticos, com foco em `lead_score`.
- [xAI Test Plan](./XAI_TEST_PLAN.md): fases de validação da API xAI.
- [Providers](./providers.md): notas de provedores e documentação externa.

## ACP

- [ACP Agent Architecture](./ACP_AGENT_ARCHITECTURE.md): executor ACP, comandos, permissões e integração com o fluxo da skill.

## Fluxo recomendado para novos usuários

```txt
README
↓
System Diagram
↓
MVP 100% Map
↓
MVP 100% Checklist
↓
User Guide
↓
Open Source Tutorial
↓
Algorithm Test Lab
↓
Context Builder
↓
Evidence Pack
```

O `Context Builder` agora mostra readiness antes do export:

- `Ready`: contexto suficiente para orientar uma IA.
- `Needs tests`: faltam suites/evidências.
- `Has failures`: existem diffs ou erros a corrigir.

Use `Algorithm + API` quando quiser validar uma futura feature de SaaS com regra de negócio e payload externo; use `Algorithm only` para score/regras determinísticas; use `API only` para webhooks/endpoints; use `ACP Evidence` para revisar como o harness ACP/CLI/IDE executou a skill.

Na UI, `Download .md` baixa o contexto técnico atual para uso imediato. `Export Markdown/JSON/HTML/ZIP` grava o pacote em `exports/reports/` com metadata para auditoria.

O botão `Generate AI Prompt` cria um prompt curto para outra IA, limitado ao que foi validado. Ele instrui explicitamente a não inventar payloads, regras ou endpoints.

O `Project Health` aparece na Home e resume PostgreSQL, último run xAI, último export de contexto, eventos com falha e modos de evidência.

Para xAI, o caminho preferido de texto é Responses API (`/v1/responses`). Chat Completions permanece como evidência `chat_legacy` para compatibilidade.

Para limpar artefatos antes de demo:

```bash
npm run demo:clean:dry
npm run demo:clean
```

Para voz, use `/voice-lab` ou `npm run voice:run`. O fluxo REST atual gera áudio via xAI TTS, transcreve via xAI STT, registra resposta do agente e salva tudo como `real_http` no PostgreSQL. Voice Agent realtime WebSocket continua como V2.

Para conferir a UI durante release local, rode a app e execute:

```bash
npm run ui:smoke
```

Para custo de tokens, `docs_verified` exige conferência manual na fonte oficial, aceita preços verificados de input/output/cache e salva `pricing_verified_at` + `pricing_verified_source_url` no histórico quando a estimativa é persistida.

## Fluxo recomendado para agentes

```txt
SKILL.md
↓
docs/workflow.md
↓
docs/MVP_100_PERCENT_CHECKLIST.md
↓
docs/ALGORITHM_TEST_PLAN.md
↓
docs/ACP_AGENT_ARCHITECTURE.md
```
