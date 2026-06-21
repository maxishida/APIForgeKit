# Repository Hygiene Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Leave the working tree free of generated validation artifacts while preserving all source code, tests, documentation, migrations, configuration, and operational context.

**Architecture:** `scripts/clean_demo_artifacts.py` remains the single cleanup boundary. `scripts/demo_clean.js` runs it through Docker so the public npm commands work even when Windows lacks a host Python installation. The cleaner discovers only known generated paths, verifies targets stay inside the repository, preserves `.gitkeep`, and returns a compact summary. Documentation explains the retention policy and the Obsidian sync indexes source documentation rather than disposable outputs.

**Tech Stack:** Python standard library, pytest, PowerShell/Bash npm helpers, Markdown, Obsidian sync CLI.

---

### Task 1: Define cleanup contracts

**Files:**
- Modify: `tests/test_clean_demo_artifacts.py`
- Test: `tests/test_clean_demo_artifacts.py`

- [x] **Step 1: Add failing tests for generated paths**

```python
def test_clean_demo_artifacts_includes_logs_outputs_and_test_caches(tmp_path):
    # Create logs/*.jsonl, outputs/*.json and tests/__pycache__/cache.pyc.
    # Assert the dry-run reports every generated artifact.
    ...

def test_clean_demo_artifacts_apply_preserves_source_and_operational_context(tmp_path):
    # Keep tests/test_source.py, docs/README.md, .env and .context/state.json.
    # Assert --apply removes only generated output.
    ...
```

- [x] **Step 2: Run the focused test and verify it fails**

Run: `python -m pytest -q tests/test_clean_demo_artifacts.py`

Expected: failure because logs, outputs and test caches are not all collected today.

### Task 2: Expand the safe cleanup boundary

**Files:**
- Modify: `scripts/clean_demo_artifacts.py`
- Create: `scripts/demo_clean.js`
- Modify: `package.json`
- Test: `tests/test_clean_demo_artifacts.py`

- [x] **Step 1: Add generated file roots**

```python
GENERATED_FILE_GLOBS = ("exports/reports/**/*", "exports/logs/**/*", "exports/contexts/**/*", "exports/blueprints/**/*", "logs/*.jsonl", "outputs/*.json")
```

- [x] **Step 2: Permit cache removal under `tests/` without permitting source removal**

```python
if path.name in ARTIFACT_DIR_NAMES:
    return path.resolve().is_relative_to(root)
```

- [x] **Step 3: Return count and byte totals in the cleanup result**

```python
return {"mode": mode, "directories": directories, "files": files, "file_count": len(files), "directory_count": len(directories), "total_bytes": total_bytes}
```

- [x] **Step 4: Add Docker-backed npm launcher**

```json
"demo:clean:dry": "node scripts/demo_clean.js dry",
"demo:clean": "node scripts/demo_clean.js apply"
```

The launcher checks `docker info`, mounts the repository at `/app`, and invokes `python scripts/clean_demo_artifacts.py` with `--apply` only for the apply mode.

The Python CLI returns counts and bytes by default; `--verbose` preserves the path-level audit view.

- [x] **Step 5: Run the focused test and verify it passes**

Run: `python -m pytest -q tests/test_clean_demo_artifacts.py`

Expected: all cleanup contract tests pass.

### Task 3: Update operational documentation

**Files:**
- Modify: `README.md`
- Modify: `docs/SUMMARY.md`
- Modify: `docs/OBSIDIAN_CONTEXT_BRAIN.md`
- Modify: `docs/MVP_TEST_CHECKLIST.md`

- [x] **Step 1: Document retention policy**

State that `tests/` contains source tests and is preserved; generated exports, JSONL logs, outputs and caches are disposable.

- [x] **Step 2: Document the safe commands**

```bash
npm run demo:clean:dry
npm run demo:clean
```

- [x] **Step 3: Explain the Obsidian boundary**

State that the vault indexes project documentation, source structure and Git metadata. It never ingests disposable exports or secrets.

### Task 4: Run cleanup and refresh the operational brain

**Files:**
- Modify: generated paths only, excluded from Git

- [x] **Step 1: Inspect `npm run demo:clean:dry` output**

Expected: only ignored generated paths are listed.

- [x] **Step 2: Run `npm run demo:clean`**

Expected: generated outputs/caches are removed while `.gitkeep`, tests, docs, `.env` and `.context` remain.

- [x] **Step 3: Synchronize and validate the vault**

```powershell
npm run obsidian:sync -- --vault "C:\Users\USER\Documents\Obsidian Vault\ApiContextbuilder"
npm run obsidian:validate -- --vault "C:\Users\USER\Documents\Obsidian Vault\ApiContextbuilder"
```

Expected: no broken links.

### Task 5: Validate and publish

**Files:**
- Modify: staged source, tests and docs only

- [x] **Step 1: Run full validation**

Run: `npm run validate:mvp`

Expected: test suite, compile, Algorithm Suite, ACP workflow, UI smoke and Docker PostgreSQL pass.

- [x] **Step 2: Remove only caches regenerated by validation**

Expected: no `__pycache__` or `.pytest_cache` remains.

- [ ] **Step 3: Verify staged changes**

Run: `git diff --cached --check` and secret scan.

Expected: clean diff without credentials.

- [ ] **Step 4: Commit and push**

```bash
git commit -m "chore: improve repository hygiene"
git push origin main
```

## Plan Self-Review

- **Spec coverage:** cleanup scope, safety boundaries, documentation, Obsidian refresh and release validation are covered.
- **Scope:** no source test deletion, database reset, `.env` change, migration or provider call.
- **Consistency:** `demo:clean` remains the only artifact deletion command; `.gitkeep` and user context are preserved.
