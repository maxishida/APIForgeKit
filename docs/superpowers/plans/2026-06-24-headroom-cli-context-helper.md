# Headroom CLI Context Helper Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Document Headroom as an optional, local CLI-only context handoff helper without changing the APIForgeKit runtime, ACP executor, data model, Docker services, or validation labs.

**Architecture:** APIForgeKit continues to create the canonical Context Builder Markdown and Evidence Pack. A human or IDE agent may explicitly invoke a locally installed Headroom CLI only after readiness is established and only for a sanitized copy intended for an implementation AI. The original export, database evidence, and ACP behavior remain unchanged.

**Tech Stack:** Markdown, pytest documentation contracts, existing Context Builder exports, external Headroom CLI installed outside this repository.

---

## File Structure

- `SKILL.md`: operational compression gate and safety boundary for human and IDE agents.
- `README.md`: short optional ninth handoff step and the non-runtime dependency boundary.
- `docs/architecture.md`: explicit branch after Context Builder that preserves raw evidence and keeps Headroom out of provider traffic.
- `docs/SUMMARY.md`: discoverability link for the helper workflow.
- `tests/test_mvp_readiness_docs.py`: documentation contract that protects the optional and evidence-first design.

### Task 1: Define the Headroom documentation contract

**Files:**
- Modify: `tests/test_mvp_readiness_docs.py`
- Test: `tests/test_mvp_readiness_docs.py`

- [ ] **Step 1: Write the failing documentation contract**

Append this test:

```python
def test_headroom_is_documented_as_optional_cli_handoff_helper():
    skill_text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    readme_text = (ROOT / "README.md").read_text(encoding="utf-8")
    architecture_text = (ROOT / "docs" / "architecture.md").read_text(encoding="utf-8")
    summary_text = (ROOT / "docs" / "SUMMARY.md").read_text(encoding="utf-8")
    requirements_text = (ROOT / "requirements.txt").read_text(encoding="utf-8")
    acp_text = (ROOT / "agents" / "acp_agent.py").read_text(encoding="utf-8")

    for text in [skill_text, readme_text, architecture_text, summary_text]:
        assert "Headroom" in text

    assert "8,000" in skill_text
    assert "original evidence" in architecture_text
    assert "optional external CLI" in readme_text
    assert "Headroom" not in requirements_text
    assert "compress-context" not in acp_text
```

- [ ] **Step 2: Run the focused test and verify it fails**

Run:

```powershell
python -m pytest -q tests/test_mvp_readiness_docs.py::test_headroom_is_documented_as_optional_cli_handoff_helper
```

Expected: fail because the production documentation does not yet mention the approved Headroom boundary.

### Task 2: Add the operational gate to the agent contract

**Files:**
- Modify: `SKILL.md` after `## Token Economy Path`
- Test: `tests/test_mvp_readiness_docs.py`

- [ ] **Step 1: Add the Headroom CLI section**

Insert this content before `## Provider Validation`:

```markdown
## Optional Headroom CLI

Headroom is an optional external CLI for shrinking a sanitized Context Builder handoff. It is not an APIForgeKit dependency, ACP command, proxy, database service, or source of evidence.

Use it only after Context Builder is `Ready` (or its explicit limitations are carried forward) and only when the user asks to reduce tokens or the handoff exceeds 8,000 tokens. Invoke the locally installed CLI explicitly and use the syntax reported by that version's `headroom --help`.

Rules:

- preserve original Markdown, JSON, HTML, ZIP, PostgreSQL records and structured logs;
- compress only a sanitized handoff copy for an implementation AI;
- never compress raw logs, raw JSON payloads, diffs, deterministic rules, API keys, authorization headers, audio or PII;
- never place a Headroom proxy in front of provider, voice, streaming, Generic API Lab or ACP traffic;
- keep persistent memory, shared cache, automatic learning and Headroom MCP disabled;
- report that compression was used plus original/optimized paths and before/after tokens when the CLI provides them;
- if the CLI is unavailable or sanitization is uncertain, send the original Context Builder export instead.
```

- [ ] **Step 2: Run the focused test and verify it passes**

Run:

```powershell
python -m pytest -q tests/test_mvp_readiness_docs.py::test_headroom_is_documented_as_optional_cli_handoff_helper
```

Expected: pass after documentation in later tasks supplies every required boundary string.

### Task 3: Document the user workflow and architecture boundary

**Files:**
- Modify: `README.md` after step 8 in `## Jornada Oficial`
- Modify: `docs/architecture.md` after the Context Builder description
- Modify: `docs/SUMMARY.md` after the Context Builder explanation
- Test: `tests/test_mvp_readiness_docs.py`

- [ ] **Step 1: Add the optional handoff note to README**

Add this directly after the official eight-step journey:

```markdown
### Optional: compress an AI handoff

After step 8, an operator may use the **optional external CLI** [Headroom](https://github.com/headroomlabs-ai/headroom) to shrink a sanitized copy of a `Context Builder` Markdown export. It is manual and local to the operator: APIForgeKit does not install, run, proxy or persist Headroom. Keep the original `.md` and Evidence Pack as the audit source, and use `headroom --help` to confirm the installed CLI syntax before running it.
```

- [ ] **Step 2: Add the architecture branch after Context Builder**

Add this section after the existing Context Builder export-path list:

````markdown
## Optional AI Handoff Compression

After Context Builder produces a ready Markdown export, a human or IDE agent may create an optimized copy with the external Headroom CLI. This happens outside the APIForgeKit runtime:

```txt
Context Builder Ready
↓
Original evidence and exports remain canonical
↓
Optional local Headroom CLI on a sanitized Markdown copy
↓
Implementation AI receives the optimized handoff
```

Headroom is never placed in the request path for provider tests, streaming, voice, Generic API Lab or ACP. It does not write to PostgreSQL or replace `context_exports`. Use it only after validation, when a user requests token reduction or the handoff exceeds 8,000 tokens. If compression cannot be safely performed, use the original evidence export.
````

- [ ] **Step 3: Add the discoverability note to the docs summary**

Add this paragraph after the `Generate AI Prompt` paragraph:

```markdown
For large, ready handoffs, Headroom is available only as an optional external CLI helper. It operates on a sanitized Markdown copy after Context Builder; it is not installed by APIForgeKit and never replaces original evidence, PostgreSQL records or the Evidence Pack.
```

- [ ] **Step 4: Run the focused contract test**

Run:

```powershell
python -m pytest -q tests/test_mvp_readiness_docs.py
```

Expected: all tests in the file pass, including the Headroom boundary contract.

### Task 4: Verify non-invasive behavior and publish

**Files:**
- Modify: `SKILL.md`
- Modify: `README.md`
- Modify: `docs/architecture.md`
- Modify: `docs/SUMMARY.md`
- Modify: `tests/test_mvp_readiness_docs.py`

- [ ] **Step 1: Confirm no runtime integration was introduced**

Run:

```powershell
rg -n -i "headroom|compress-context" agents core ui requirements.txt docker-compose.yml package.json
```

Expected: no match. Headroom appears only in documentation and the documentation contract test.

- [ ] **Step 2: Run targeted regression tests**

Run:

```powershell
python -m pytest -q tests/test_mvp_readiness_docs.py tests/test_acp_agent.py tests/test_acp_skill_executor.py tests/test_context_builder.py tests/test_context_builder_ui_contract.py
```

Expected: all selected tests pass.

- [ ] **Step 3: Run full verification**

Run:

```powershell
python -m pytest -q
python -m compileall app.py core ui agents run_algorithm_lab.py run_acp_prompt.py run_acp_workflow.py
git diff --check
git status --short
```

Expected: tests and compilation pass, the diff has no whitespace errors, and only the planned documentation/test files are modified.

- [ ] **Step 4: Commit and push the implementation**

Run:

```powershell
git add SKILL.md README.md docs/architecture.md docs/SUMMARY.md tests/test_mvp_readiness_docs.py docs/superpowers/plans/2026-06-24-headroom-cli-context-helper.md
git diff --cached --check
git commit -m "docs: add optional headroom context workflow"
git push origin main
```

Expected: one focused commit is pushed with no `.env`, local Headroom state or generated Evidence Pack included.

## Plan Self-Review

- **Spec coverage:** Tasks 2 and 3 implement the compression gate, safety boundary, fallback and optional documentation; Task 4 protects the no-runtime-change requirement.
- **Scope:** no database, UI, Docker, provider runner, dependency or ACP changes are planned.
- **Type consistency:** the invariant term is `optional external CLI`; the token threshold is `8,000`; the original evidence remains canonical in every document and test.
- **Placeholder scan:** no implementation task depends on unspecified code or a future Headroom command syntax.
