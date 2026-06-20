# Obsidian Operational Brain Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a safe local Obsidian context brain for APIForgeKit with a navigable graph, automatic resume state, and idempotent repository-to-vault sync.

**Architecture:** `core/obsidian_vault.py` owns canonical note specifications, repository snapshotting, generated-section merging, sync, and wikilink validation. `scripts/sync_obsidian_vault.py` is a thin CLI. The external vault receives Markdown notes and generated snapshots; user content outside generated markers remains untouched.

**Tech Stack:** Python standard library, pytest, Git CLI, Markdown, Obsidian wikilinks, npm scripts.

---

## File Structure

- Create: `core/obsidian_vault.py` — vault domain logic and safe filesystem operations.
- Create: `scripts/sync_obsidian_vault.py` — `sync` and `validate` CLI actions.
- Create: `tests/test_obsidian_vault.py` — temporary-vault behavior tests.
- Create: `docs/OBSIDIAN_CONTEXT_BRAIN.md` — user and agent guide.
- Modify: `package.json`, `README.md`, `docs/SUMMARY.md`, `SKILL.md`.
- Modify: `docs/superpowers/specs/2026-06-21-obsidian-operational-brain-design.md`.
- Create externally: canonical notes under `C:\Users\USER\Documents\Obsidian Vault\ApiContextbuilder`.

### Task 1: Establish the Sync Contract With Tests

**Files:**
- Create: `tests/test_obsidian_vault.py`
- Create later: `core/obsidian_vault.py`

- [ ] **Step 1: Write the failing bootstrap test**

```python
def test_sync_creates_map_resume_note_and_canonical_hubs(tmp_path):
    result = sync_vault(vault_path=tmp_path, repo_root=PROJECT_ROOT)

    assert (tmp_path / "00 - Mapa do Projeto.md").exists()
    assert (tmp_path / "00 - Retomar Agora.md").exists()
    assert "[[Arquitetura do Sistema]]" in (tmp_path / "00 - Mapa do Projeto.md").read_text(encoding="utf-8")
    assert result["created"]
```

- [ ] **Step 2: Run it and confirm the expected red result**

Run: `python -m pytest tests/test_obsidian_vault.py::test_sync_creates_map_resume_note_and_canonical_hubs -q`

Expected: import failure for `core.obsidian_vault`.

- [ ] **Step 3: Write the failing generated-boundary test**

```python
def test_sync_replaces_only_generated_text_and_preserves_user_notes(tmp_path):
    resume = tmp_path / "00 - Retomar Agora.md"
    resume.write_text("<!-- @generated:start -->old<!-- @generated:end -->\n## Notas da sessão\nNão apagar.", encoding="utf-8")

    sync_vault(vault_path=tmp_path, repo_root=PROJECT_ROOT)

    content = resume.read_text(encoding="utf-8")
    assert "Não apagar." in content
    assert "old" not in content
```

- [ ] **Step 4: Run it and confirm the expected red result**

Run: `python -m pytest tests/test_obsidian_vault.py::test_sync_replaces_only_generated_text_and_preserves_user_notes -q`

Expected: failure caused by missing sync behavior.

### Task 2: Implement the Safe Vault Domain Module

**Files:**
- Create: `core/obsidian_vault.py`
- Test: `tests/test_obsidian_vault.py`

- [ ] **Step 1: Add the public API**

```python
def build_repository_snapshot(repo_root: Path) -> dict[str, object]: ...
def sync_vault(*, vault_path: Path, repo_root: Path) -> dict[str, object]: ...
def validate_vault(*, vault_path: Path) -> dict[str, object]: ...
```

- [ ] **Step 2: Define canonical note specifications**

Create specs for `00 - Mapa do Projeto`, `00 - Retomar Agora`, `Visão Geral do Projeto`, `SDD - Spec Driven Development`, `STB - Software Technical Blueprint`, `ACP - AI Collaboration Protocol`, `PREVC`, `Arquitetura do Sistema`, `MVP Inicial`, `Backlog Geral`, `Tickets Ativos`, `Decisões Técnicas`, `Logs de Evolução`, `Prompts Operacionais`, `Memória Operacional`, `Referências Externas`, `Algorithm Test Lab`, `Generic API Lab`, `Context Builder`, and `ACP Skill Executor`.

Each canonical note has YAML metadata plus `Objetivo`, `Contexto`, `Conteúdo principal`, `Links relacionados`, and `Próximas ações`; every hub links to `[[00 - Mapa do Projeto]]`.

- [ ] **Step 3: Implement safe snapshots and generated merging**

Collect branch, HEAD SHA, latest commit subject, selected docs, top-level modules, and `npm run validate:mvp`. Exclude `.env`, `.venv`, `exports/`, `logs/`, and all environment values. Use `<!-- @generated:start -->` / `<!-- @generated:end -->` markers, skip existing notes with no marker, and preserve user content.

- [ ] **Step 4: Generate the resume and engineering snapshots**

Create `06 - Engenharia/Gerado/APIForgeKit - Snapshot de Arquitetura.md` and `06 - Engenharia/Gerado/Documentação Ativa.md`. Update `00 - Retomar Agora.md` with branch, commit, subject, docs, validation command, next action, and links to the map and generated notes.

- [ ] **Step 5: Verify green**

Run: `python -m pytest tests/test_obsidian_vault.py -q`

Expected: bootstrap and preservation tests pass.

### Task 3: Add Graph Validation and Idempotence

**Files:**
- Modify: `tests/test_obsidian_vault.py`
- Modify: `core/obsidian_vault.py`

- [ ] **Step 1: Write the failing broken-link test**

```python
def test_validate_vault_reports_unresolved_wikilinks(tmp_path):
    (tmp_path / "00 - Mapa do Projeto.md").write_text("[[Nota Ausente]]", encoding="utf-8")

    result = validate_vault(vault_path=tmp_path)

    assert result["valid"] is False
    assert "Nota Ausente" in result["broken_links"]
```

- [ ] **Step 2: Run it and confirm red**

Run: `python -m pytest tests/test_obsidian_vault.py::test_validate_vault_reports_unresolved_wikilinks -q`

Expected: failure because wikilink parsing is missing.

- [ ] **Step 3: Implement validator and manifest**

Parse `[[target]]` and `[[target|label]]`, index Markdown stems, and return sorted broken links. Write `.apiforgekit-vault-manifest.json` with source commit, safe source paths, hashes, and generated note paths. A second unchanged sync must not rewrite Markdown.

- [ ] **Step 4: Add idempotence and secret-safety test**

```python
def test_second_sync_is_idempotent_and_does_not_read_environment_values(tmp_path, monkeypatch):
    monkeypatch.setenv("XAI_API_KEY", "must-not-appear")
    sync_vault(vault_path=tmp_path, repo_root=PROJECT_ROOT)
    second = sync_vault(vault_path=tmp_path, repo_root=PROJECT_ROOT)

    assert second["updated"] == []
    assert "must-not-appear" not in "\n".join(path.read_text(encoding="utf-8") for path in tmp_path.rglob("*.md"))
```

Run: `python -m pytest tests/test_obsidian_vault.py -q`

Expected: graph, idempotence, and secret-safety tests pass.

### Task 4: Add CLI and Documentation

**Files:**
- Create: `scripts/sync_obsidian_vault.py`
- Create: `docs/OBSIDIAN_CONTEXT_BRAIN.md`
- Modify: `package.json`, `README.md`, `docs/SUMMARY.md`, `SKILL.md`
- Test: `tests/test_obsidian_vault.py`

- [ ] **Step 1: Write the failing CLI test**

```python
def test_sync_cli_creates_and_validates_vault(tmp_path):
    completed = subprocess.run(
        [sys.executable, "scripts/sync_obsidian_vault.py", "sync", "--vault", str(tmp_path)],
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert '"status": "ok"' in completed.stdout
```

- [ ] **Step 2: Run it and confirm red**

Run: `python -m pytest tests/test_obsidian_vault.py::test_sync_cli_creates_and_validates_vault -q`

Expected: failure because CLI is absent.

- [ ] **Step 3: Implement CLI and npm scripts**

Support `sync` and `validate` with a required existing `--vault` directory. Add:

```text
npm run obsidian:sync -- --vault "C:\Users\USER\Documents\Obsidian Vault\ApiContextbuilder"
npm run obsidian:validate -- --vault "C:\Users\USER\Documents\Obsidian Vault\ApiContextbuilder"
```

The CLI prints JSON, returns nonzero for missing vault or invalid graph, and never creates a missing vault directory.

- [ ] **Step 4: Write user and agent guidance**

Vault `AGENTS.md` tells agents to read `00 - Retomar Agora` then `00 - Mapa do Projeto`, follow PREVC, preserve user text, update decisions/logs/tickets, and never delete or move notes without a plan. The repository guide documents graph navigation, generated markers, manual session notes, and the sync commands.

- [ ] **Step 5: Verify green**

Run: `python -m pytest tests/test_obsidian_vault.py -q`

Expected: vault and CLI tests pass.

### Task 5: Bootstrap and Validate the Real Vault

**Files:**
- Create externally: `C:\Users\USER\Documents\Obsidian Vault\ApiContextbuilder\**`

- [ ] **Step 1: Run the initial sync**

Run: `python scripts/sync_obsidian_vault.py sync --vault "C:\Users\USER\Documents\Obsidian Vault\ApiContextbuilder"`

Expected: only planned folders, notes, templates, generated snapshots, and manifest are created.

- [ ] **Step 2: Validate all canonical links**

Run: `python scripts/sync_obsidian_vault.py validate --vault "C:\Users\USER\Documents\Obsidian Vault\ApiContextbuilder"`

Expected: JSON has `"valid": true` and no broken canonical links.

- [ ] **Step 3: Add the initial evolution log**

Record bootstrap date, source commit, graph purpose, and the next action to open `00 - Retomar Agora` in Obsidian.

### Task 6: Audit, Clean Safely, Verify, Commit, and Push

**Files:**
- Modify only if needed: `.gitignore`

- [ ] **Step 1: Audit test collection**

Run: `python -m pytest --collect-only -q`

Keep every collected `tests/test_*.py` file. Remove only ignored caches and generated artifacts with `npm run demo:clean`; do not delete active test source.

- [ ] **Step 2: Run final verification**

Run: `python -m pytest tests/test_obsidian_vault.py -q`, `npm test`, and `git diff --check`.

Expected: vault tests and MVP validation pass with no diff errors.

- [ ] **Step 3: Commit and push**

```text
git add core/obsidian_vault.py scripts/sync_obsidian_vault.py tests/test_obsidian_vault.py docs README.md SKILL.md package.json
git commit -m "feat: add obsidian operational context brain"
git push origin main
```

## Plan Self-Review

- **Spec coverage:** graph, complete project context, resume state, protected user notes, sync, validation, safety, and release checks are covered by Tasks 1 through 6.
- **Scope:** local-first vault and bounded sync only; no cloud automation, provider calls, or destructive migration.
- **Consistency:** `sync_vault`, `validate_vault`, generated markers, manifest, CLI actions, and `00 - Retomar Agora` use the same names throughout.
- **Placeholder scan:** every task includes exact paths, behavior, test command, and expected result.
