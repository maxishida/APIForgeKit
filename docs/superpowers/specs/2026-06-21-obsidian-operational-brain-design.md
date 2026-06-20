# ApiContextbuilder Obsidian Operational Brain Design

## Goal

Create a local Obsidian vault at `C:\Users\USER\Documents\Obsidian Vault\ApiContextbuilder` that acts as a navigable operational memory for APIForgeKit and AI-assisted software work. The vault must expose meaningful relationships in Obsidian Graph view and remain useful to both people and Codex.

## Approved Direction

The vault is the context and decision layer; APIForgeKit remains the source of executable code, tests, database evidence, and generated reports. A local sync command projects selected repository facts into generated vault notes without deleting or overwriting human-authored material.

The design takes the useful, lightweight parts of `obsidian-second-brain`: AI-first frontmatter, a central index, durable wikilinks, generated-content boundaries, and incremental maintenance. It intentionally does not install that project's large command suite, hooks, scheduled agents, or provider integrations.

Reference: https://github.com/eugeniughelbur/obsidian-second-brain

## Information Architecture

The vault starts empty, so the first version creates the following shallow structure:

```text
ApiContextbuilder/
├─ 00 - Mapa do Projeto.md
├─ 00 - Retomar Agora.md
├─ AGENTS.md
├─ 01 - Inbox/
├─ 02 - Projetos/
│  └─ ApiContextbuilder/
├─ 03 - Areas/
├─ 04 - Recursos/
├─ 05 - Arquivo/
├─ 06 - Engenharia/
│  └─ Gerado/
├─ 07 - Prompts/
├─ 08 - Logs/
├─ 09 - Tickets/
├─ 10 - Decisões/
└─ 99 - Templates/
```

`00 - Mapa do Projeto` is the mandatory hub. It links to the project vision, engineering practices, architecture, MVP, workflow, decisions, logs, backlog, prompts, and memory. Every principal note links back to this map and to at least one directly related note.

`00 - Retomar Agora` is the operational entry point for a resumed human or AI session. It is updated during each sync with the current branch, commit, recent commit subject, source-document index, validated commands, and recommended next action. A protected user section records session-specific notes that the sync must preserve.

## Graph Model

The graph is designed as a real working network rather than a decorative starburst:

- **Hub:** `00 - Mapa do Projeto` is the entry point and connects all canonical domains.
- **Operational hubs:** `PREVC`, `ACP - AI Collaboration Protocol`, `SDD - Spec Driven Development`, and `STB - Software Technical Blueprint` connect workflow, requirements, and implementation evidence.
- **Domain hubs:** `Arquitetura do Sistema`, `MVP Inicial`, `Backlog Geral`, `Tickets Ativos`, `Decisões Técnicas`, `Logs de Evolução`, `Prompts Operacionais`, and `Memória Operacional` cross-link only where a real dependency exists.
- **Leaf notes:** individual tickets, decisions, session logs, prompts, and reference notes link to their owning hub plus their affected project area.

This produces a dense, navigable graph over time similar in shape to the supplied examples, without manufacturing meaningless links. Obsidian's local graph reveals focused sub-networks; the global graph reveals the operational system.

## Note Contract

All created notes use concise YAML metadata such as `tipo`, `status`, `area`, `projeto`, `tags`, `source`, and `updated`. Every note has:

1. `## Objetivo`
2. `## Contexto`
3. `## Conteúdo principal`
4. `## Links relacionados`
5. `## Próximas ações`

Agent-facing notes add a short `## Para futuros agentes` section with the minimum operational context. Wikilinks use Obsidian syntax, for example `[[00 - Mapa do Projeto]]`.

## Sync Boundary

A repository command, planned as `python scripts/sync_obsidian_vault.py --vault <path>`, will read selected APIForgeKit sources:

- `README.md`
- `SKILL.md`
- `docs/SUMMARY.md`
- architecture and workflow documents in `docs/`
- the module layout under `agents/`, `core/`, `ui/`, `scripts/`, and `tests/`

It will update only notes in `06 - Engenharia/Gerado/` and generated sections delimited by `<!-- @generated:start -->` and `<!-- @generated:end -->`. It never removes vault files, never moves existing notes, never reads `.env`, and never exports secrets. A stable manifest records source paths, source commit, generated-note paths, and a source fingerprint.

The sync also refreshes the generated block in `00 - Retomar Agora`. It reads Git metadata as the commit anchor and catalogs safe documentation present in the workspace at sync time; it does not inspect or export private environment files, credentials, or raw working-tree diffs.

Human-created notes, decisions, logs, prompts, tickets, and text outside generated blocks remain untouched.

## PREVC Execution Model

1. **Planejamento:** create the note taxonomy, map, templates, agent guidance, and sync boundary.
2. **Revisão:** verify naming, shallow paths, real link relationships, and no conflict with existing vault content.
3. **Execução:** create initial notes, generate repository architecture snapshots, and add the sync command.
4. **Validação:** check required notes, wikilinks, backlinks to the map, generated markers, idempotent sync behavior, and no secret leakage.
5. **Confirmação:** report created and modified files, graph hubs, unresolved links, and the exact sync command.

## Error Handling and Safety

- Missing vault path: the command fails with a clear message and creates nothing.
- Existing note without generated markers: the command leaves it untouched and reports it.
- Unresolved wikilink: validation reports it; the sync does not silently invent a target.
- Existing vault content: no deletes, moves, or renames occur.
- Repository or vault write failure: report the failed path and preserve already-existing content.

## Validation Criteria

- `00 - Mapa do Projeto` exists and links to every canonical hub.
- `00 - Retomar Agora` identifies the current repository commit and links to the map, architecture snapshot, active documentation, and next action.
- Every canonical hub links back to the map.
- Every generated architecture note includes source metadata and generated markers.
- A second sync makes no material change when source files are unchanged.
- Vault validation detects no broken canonical links.
- `AGENTS.md` describes note creation, PREVC, decisions, logs, and safety constraints.

## Scope Exclusions

- No automatic cloud sync, scheduler, or background agent.
- No provider calls, LLM calls, or secret access.
- No destructive vault cleanup or migration.
- No attempt to fabricate a large graph with empty notes.
