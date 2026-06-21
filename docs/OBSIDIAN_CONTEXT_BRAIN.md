# Obsidian Context Brain

O vault do Obsidian transforma a documentação do APIForgeKit em memória navegável para pessoas e agentes. Ele não substitui o repositório: o Git continua sendo a fonte de código, testes, banco e evidência executável.

## Caminho Aprovado

```txt
C:\Users\USER\Documents\Obsidian Vault\ApiContextbuilder
```

## Começar ou Retomar

Sincronize o vault após um commit ou antes de iniciar uma sessão:

```powershell
npm run obsidian:sync -- --vault "C:\Users\USER\Documents\Obsidian Vault\ApiContextbuilder"
npm run obsidian:validate -- --vault "C:\Users\USER\Documents\Obsidian Vault\ApiContextbuilder"
```

Abra nesta ordem:

1. `00 - Retomar Agora.md`: branch, commit, último assunto, documentação ativa e validação recomendada.
2. `00 - Mapa do Projeto.md`: hubs e navegação global.
3. Nota do módulo, ticket ou decisão ligada ao trabalho atual.

## Grafo

O grafo é formado por links reais. Os hubs principais são:

- `00 - Mapa do Projeto`
- `00 - Retomar Agora`
- `Arquitetura do Sistema`
- `PREVC`
- `Decisões Técnicas`
- `Logs de Evolução`
- `Tickets Ativos`
- `Context Builder`

No Obsidian, abra Graph View e selecione `00 - Mapa do Projeto` para ver os clusters. Use Local Graph ao revisar um ticket, uma decisão ou um módulo.

## O Que o Sync Cria

- notas canônicas para visão, MVP, SDD, STB, ACP, PREVC, arquitetura, labs, contexto, prompts, backlog, tickets, decisões, logs e referências;
- snapshots gerados em `06 - Engenharia/Gerado/`;
- `AGENTS.md` para orientar Codex e outros agentes;
- `.apiforgekit-vault-manifest.json` com fontes seguras e fingerprint do snapshot;
- templates de nota e decisão.

## Segurança e Preservação

O sync cria arquivos ausentes e atualiza somente conteúdo entre:

```html
<!-- @generated:start -->
<!-- @generated:end -->
```

Texto fora desses marcadores, especialmente a seção `Notas da sessão`, é preservado. O processo não apaga, move ou renomeia notas existentes; não lê `.env` nem exporta segredos. No modo Docker, ele recebe somente branch, commit e assunto do último commit como metadados públicos para atualizar a nota de retomada.

O vault indexa código e documentação do projeto, não Evidence Packs descartáveis. Antes de uma demo limpa, execute `npm run demo:clean:dry`; depois de `npm run demo:clean`, execute o sync novamente para registrar o commit e a documentação atual, sem depender de exports antigos.

## Para Agentes

Antes de sugerir trabalho, o agente deve ler `00 - Retomar Agora`, `00 - Mapa do Projeto`, o ticket relacionado e o `SKILL.md` do repositório. Aplique PREVC, registre decisões e logs, e mantenha toda nova nota conectada a um hub existente.
