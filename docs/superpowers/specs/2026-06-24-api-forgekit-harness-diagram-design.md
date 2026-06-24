# APIForgeKit Harness Diagram Design

**Status:** Approved visual direction; awaiting written-spec review

## Goal

Add a GitHub-rendered Mermaid overview that explains the APIForgeKit evidence harness in one visual: operator and IDE entry points, optional Dotcontext workflow support, ACP/SKILL orchestration, validation labs, PostgreSQL evidence, observability, Context Builder and the optional Headroom handoff step.

## Placement

The diagram will be the first overview in `docs/SYSTEM_DIAGRAM.md`, before the existing focused diagrams for Algorithm Test Lab, Generic API Lab, Token Calculator, provider validation and ACP audit. The existing diagrams stay in place because they explain individual paths in more detail.

## Diagram Type

Use a GitHub-compatible Mermaid `flowchart LR` with six visible boundaries:

1. **Entry points:** Human/Operator, NiceGUI Studio, IDE/AI Client, optional Dotcontext MCP, ACP/CLI Client.
2. **Operational control:** `SKILL.md` decision gates, ACP Executor and Core Services.
3. **Validation:** Algorithm Test Lab, Generic API Lab, xAI/Voice Validation and Token Calculator.
4. **Evidence:** PostgreSQL Evidence Store with structured logs and metrics.
5. **Review and context:** Dashboard/Logs and Context Builder/Evidence Pack.
6. **AI handoff:** direct original evidence handoff or optional local Headroom CLI operating only on a sanitized copy.

## Real Paths

- NiceGUI Studio sends users directly to the validation labs.
- ACP/CLI sends requests through ACP Executor, then `SKILL.md` gates and Core Services.
- Dotcontext MCP is an optional IDE workflow companion. It may guide an AI client, but it does not replace the ACP executor, become a source of evidence, or write application data to PostgreSQL.
- Every validation path persists structured evidence to PostgreSQL.
- Dashboard/Logs and Context Builder read the evidence store.
- Context Builder creates the original Evidence Pack. Headroom never runs before or inside validation; it only creates an optional sanitized handoff copy after readiness.

## Visual Rules

- Use short labels and left-to-right progression similar to the approved preview.
- Use Mermaid subgraphs for boundaries, but do not depend on colors or interaction for comprehension.
- Label Dotcontext and Headroom as `optional` in the node labels.
- Do not show an edge from Headroom to labs, API providers, PostgreSQL, logs, or ACP.
- Preserve the operating rule below the diagram: evidence must exist before implementation work starts.

## Verification

- Extend `tests/test_system_diagram_docs.py` to check the overview contains the entry, control, validation, evidence, review and handoff node labels.
- Confirm Mermaid fences remain balanced and `git diff --check` reports no error.
- Confirm no runtime, dependency, Docker, ACP executor or database file is changed.
