# APIForgeKit Studio

APIForgeKit Studio é um laboratório local-first para validar APIs, webhooks, custos de tokens e algoritmos antes de pedir implementação para IA.

Em vez de começar pelo código final, o projeto segue este fluxo:

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

O objetivo é simples: **economizar tempo e tokens de LLM usando evidência real ou contrato explícito antes de implementar**.

## Para Quem É

- Devs criando SaaS com APIs externas.
- Devs validando regra de negócio, score ou classificação.
- Devs testando webhooks, WhatsApp, CRM, pagamentos ou provedores de IA.
- Devs que querem entregar contexto menor e confiável para uma LLM.

## O Que Dá Para Fazer

- **Algorithm Test Lab:** valida algoritmos determinísticos, como `lead_score` e `community_bot_engine`, com input, expected output, actual output, diff e invariantes.
- **Community Bot Lab:** testa o Vice City NPC Engine — eventos, regras, bots oficiais, sandbox, pipeline Score→Bot e suíte 17/17 sem IA.
- **Generic API Lab:** testa contratos de APIs/webhooks em `dry_run_contract` ou HTTP real com permissão.
- **Live Dashboard:** mostra métricas, eventos, latência, falhas recentes e modos de evidência.
- **Logs:** permite buscar e filtrar JSON estruturado por provider, módulo, status, latência e `evidence_mode`.
- **Context Builder:** transforma evidências em contexto técnico para IA, com readiness `Ready`, `Needs tests`, `Has failures` e `Generate AI Prompt`.
- **Evidence Pack:** exporta Markdown, JSON, HTML e ZIP; `Download .md` serve para uso rápido e exports auditáveis ficam em `context_exports`.
- **Token Calculator:** estima custo por provider/modelo/usuário, diferencia `seeded_estimate` de `docs_verified` e salva no histórico só quando solicitado.
- **Project Health:** resume PostgreSQL, último run xAI, último export de contexto, falhas e modos de evidência.
- **xAI Responses API:** o runner compacto prioriza `/v1/responses` para novas validações e mantém Chat Completions como compatibilidade legado.
- **xAI Voice Lab:** executa roundtrip real TTS -> STT -> resposta do agente, salva logs no PostgreSQL e alimenta Dashboard, Logs e Context Builder.
- **ACP Executor:** permite rodar o workflow por IDE/CLI/agente usando `SKILL.md` como contrato operacional.

## Quick Start

```bash
python -m pip install -r requirements.txt
copy .env.example .env
npm run db
python app.py
```

Abra:

```txt
http://localhost:8080
```

No Linux/macOS:

```bash
cp .env.example .env
```

## Jornada Oficial

Depois de abrir a UI, siga esta ordem:

1. **Abrir Tutorial:** entenda o fluxo do produto em `/tutorial`.
2. **Rodar Algorithm Suite:** execute `lead_score` no Algorithm Test Lab ou rode `npm run algorithm:suite`.
3. **Rodar API Contract Dry-run:** execute `Run Contract Dry-run` no Generic API Lab.
4. **Ver Dashboard:** confira métricas e modos de evidência.
5. **Abrir Logs:** inspecione request, response, erro, latência e `evidence_mode`.
6. **Gerar Context Builder:** selecione o modo de fonte e confira readiness.
7. **Baixar Evidence Pack:** use `Download .md` para contexto rápido ou `Export ZIP`; os caminhos auditáveis ficam em `context_exports`.
8. **Usar contexto com IA:** peça implementação somente com base no contexto validado.

## Comandos Principais

```bash
npm run db              # sobe PostgreSQL
npm run dev             # roda o Studio
npm run test            # roda a suíte de testes
npm run algorithm:suite # valida lead_score e exporta evidência
npm run bot:suite       # valida community_bot_engine e exporta evidência
npm run community:pipeline  # valida member_engagement_score + community_bot_engine
npm run voice:run       # roda xAI Voice Lab real com XAI_API_KEY
npm run ui:smoke        # valida rotas principais com a UI já rodando
npm run ui:smoke:local  # sobe a UI se necessário e valida rotas
npm run acp:workflow    # testa ACP + SKILL.md em 9 prompts; Voice precisa evidência salva
npm run validate:mvp    # valida o MVP inteiro via Docker Python
npm run validate:mvp:provider # valida o MVP e roda xAI real com aprovação/custo
npm run validate:mvp:unix # Linux/macOS: valida o MVP inteiro via Docker Python
npm run validate:mvp:provider:unix # Linux/macOS: valida o MVP e roda xAI real
npm run demo:clean:dry  # resume artefatos de demo que seriam removidos
npm run demo:clean      # remove apenas artefatos gerados, sem tocar código, testes-fonte, .env, .context ou banco
npm run obsidian:sync -- --vault "C:\Users\USER\Documents\Obsidian Vault\ApiContextbuilder"
npm run obsidian:validate -- --vault "C:\Users\USER\Documents\Obsidian Vault\ApiContextbuilder"
```

Atalho por sistema:

```bash
# Windows/PowerShell
npm run validate:mvp
npm run validate:mvp:provider

# Linux/macOS
npm run validate:mvp:unix
npm run validate:mvp:provider:unix
```

No Windows, prefira os comandos PowerShell. Os comandos `:unix` são para Linux/macOS; em Windows eles só fazem sentido se Git Bash estiver antes do launcher WSL no `PATH`.

GitHub Actions fica manual-only (`workflow_dispatch`). A validação oficial do MVP é local, via Docker, com `npm run validate:mvp`; rode CI no GitHub apenas quando quiser testar o workflow em nuvem.

ACP quick prompts:

```bash
python run_acp_prompt.py "/validate-lead-score"
python run_acp_prompt.py "/validate-token-cost provider=xai model=grok-4.3 users=10 requests=20"
python run_acp_prompt.py "/validate-context-readiness"
python run_acp_prompt.py "/validate-voice-roundtrip"
```

`/validate-voice-roundtrip` valida evidência de voz já salva. Para executar xAI Voice real, use `/voice-lab` ou `npm run voice:run`; pelo ACP, `--run-real` pede permissão e não roda automaticamente.

## O Que Está Pronto no MVP

- `lead_score` com 17 casos canônicos e invariantes.
- `member_engagement_score` (12 casos) + `community_bot_engine` (17 casos) na Community Pipeline; UI em `/community-bot-lab` e Context Builder modo **Community Pipeline**.
- API contract pack de WhatsApp em `dry_run_contract`.
- Context Builder com export Markdown, JSON, HTML e ZIP.
- Context Builder com `Generate AI Prompt` para entregar instruções curtas e baseadas em evidência para outra IA.
- Token Calculator com estimativas e trilha de fonte de pricing.
- xAI compact runner com Responses API, Chat legacy, structured outputs, streaming e tools.
- xAI Voice Lab REST com TTS, STT, resposta textual do agente e logs de funil.
- Dashboard, Logs e filtros por evidência.
- ACP workflow com permissão para caminhos pagos ou HTTP real.
- ACP readiness commands para custo, contexto e evidência de voz sem overengineering.

## Importante

- `dry_run_contract` valida contrato local; não é API real.
- `seed_validation` valida suite canônica; não é produção.
- HTTP real exige URL, credenciais e permissão explícita.
- Voice Lab REST é funcional com `XAI_API_KEY`; Voice Agent realtime WebSocket e Agents seguem como V2.
- Sem Context Builder Ready = não implementar; gere contexto/evidence pack validado primeiro.
- Antes de `npm run demo:clean`, preserve exports if Project Health depends on them.
- `npm run demo:clean` remove somente artefatos ignorados: exports gerados, `logs/*.jsonl`, `outputs/*.json` e caches Python. Arquivos em `tests/*.py`, docs, migrations, `.env`, `.context`, banco Docker e `.gitkeep` são preservados.
- Os comandos mostram contagem e tamanho por padrão. Para listar caminhos antes de limpar, use `npm run demo:clean:dry -- --verbose`.
- Next.js/Prisma é destino futuro, não geração automática no MVP.

## Documentação

A raiz fica curta de propósito:

- [SKILL.md](./SKILL.md): contrato operacional para agentes.
- [docs/SUMMARY.md](./docs/SUMMARY.md): índice da documentação completa.
- [docs/USER_GUIDE.md](./docs/USER_GUIDE.md): guia didático para novos usuários.
- [docs/MVP_100_PERCENT_MAP.md](./docs/MVP_100_PERCENT_MAP.md): o que é real, dry-run, seed, legacy e blocked.
- [docs/DEMO_SCRIPT.md](./docs/DEMO_SCRIPT.md): roteiro para demo ou vídeo.
- [docs/ACP_AGENT_ARCHITECTURE.md](./docs/ACP_AGENT_ARCHITECTURE.md): detalhes do executor ACP.
- [docs/OBSIDIAN_CONTEXT_BRAIN.md](./docs/OBSIDIAN_CONTEXT_BRAIN.md): cérebro operacional no Obsidian, sync e retomada de contexto.
- [docs/COMMUNITY_BOT_ENGINE.md](./docs/COMMUNITY_BOT_ENGINE.md): Vice City NPC Engine — lab, suíte, download e handoff para IDE.

## Retomar Com Obsidian

O vault local em `C:\Users\USER\Documents\Obsidian Vault\ApiContextbuilder` guarda o contexto navegável do projeto. Após um commit ou antes de retomar trabalho, sincronize e abra no Obsidian:

```bash
npm run obsidian:sync -- --vault "C:\Users\USER\Documents\Obsidian Vault\ApiContextbuilder"
```

Comece por `00 - Retomar Agora.md`; ele aponta o commit, a documentação ativa, o comando de validação e o próximo passo. Depois abra `00 - Mapa do Projeto.md` para navegar pelo grafo.

## Status

V1 está focada em validação, observabilidade e contexto técnico. A proposta é provar comportamento primeiro e só depois usar IA para implementar com menos retrabalho.
