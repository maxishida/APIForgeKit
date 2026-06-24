# Headroom CLI Context Helper Design

**Status:** Proposed and approved for implementation planning

## Goal

Use Headroom only as an optional local CLI helper that compresses a validated Context Builder export before an operator sends it to an implementation AI. It must not become part of the APIForgeKit runtime, provider test path, database, or ACP executor.

## Problem

Evidence Packs can become large when they contain validated API behavior, logs, payload summaries, failures, and recommendations. Sending their full text to an implementation AI can increase token cost and distract the model. Compression may help, but it must never replace the original evidence or alter deterministic validation.

## Decision

The first integration is documentation-driven and manual:

1. APIForgeKit validates behavior and exports the original Context Builder Markdown and Evidence Pack.
2. An operator or IDE agent checks Context Builder readiness and token size.
3. Only when the compression gate passes, it invokes the locally installed Headroom CLI using the command syntax reported by that installed version's `headroom --help`.
4. Headroom writes or returns an optimized copy for a target implementation AI.
5. The original export remains the canonical, auditable source of truth.

The ACP executor does not receive a new command in this phase. The `SKILL.md` explains the gate and tells agents to use the local CLI explicitly when appropriate.

## Data Flow

```txt
Labs -> Structured Logs -> PostgreSQL -> Context Builder (Ready)
                                            |
                                            +-> Original Markdown + Evidence Pack
                                            |
                                            +-> Optional Headroom CLI -> Optimized handoff copy -> Implementation AI
```

## Compression Gate

Headroom is permitted only when all of the following are true:

- Context Builder reports `Ready` or its explicit limitations are included in the handoff.
- The user asks for token reduction, or the handoff is estimated at more than 8,000 tokens.
- The action happens after validation and export, never while a lab, suite, API request, or diff is running.
- The command is available locally and is invoked explicitly by the operator or IDE agent.

## Safety Rules

- Preserve the original Markdown, JSON, HTML, ZIP, database records, structured logs, and algorithm diffs.
- Never send raw API keys, authorization headers, audio, PII, full raw logs, raw JSON payloads, or deterministic rule definitions to the compressor.
- Do not configure a Headroom proxy in front of xAI, generic API, voice, streaming, or ACP traffic.
- Do not enable persistent memory, shared cache, automatic learning, MCP wiring, or background processes for this phase.
- Report the original path, optimized path, token count before and after when the CLI exposes those values, and the fact that compression was used.
- If Headroom is unavailable or a safe sanitized copy cannot be produced, use the original Context Builder export and state that compression was skipped.

## Scope

### Included

- Operational instructions in `SKILL.md`.
- A concise user-facing workflow note in the README and architecture documentation.
- A small verification checklist for a manually installed Headroom CLI.

### Excluded

- Changes to `agents/acp_agent.py`, `agents/skill_executor.py`, database models, migrations, Docker Compose, provider runners, or NiceGUI pages.
- Adding Headroom to `requirements.txt` or runtime containers.
- Adding an ACP `/compress-context` command.
- Automatic compression or cost optimization.

## Acceptance Criteria

- A contributor can identify when Headroom is allowed and when it is forbidden.
- A contributor can complete the standard APIForgeKit workflow without Headroom installed.
- The documentation preserves the evidence-first rule: original evidence is canonical and compression is only a handoff optimization.
- ACP behavior and existing commands remain unchanged.
- No project dependency, service, database table, or API test behavior changes.

## Verification

1. Confirm `SKILL.md` names the compression gate, safety rules, and fallback.
2. Confirm README and architecture documentation label Headroom as optional external CLI tooling.
3. Run documentation contract tests and the existing ACP/context tests.
4. Confirm `git diff --check` is clean and no secret or local Headroom state is staged.

## Future Option

Only after a manual pilot shows measurable token reduction without loss of implementation fidelity may APIForgeKit add an explicit `/compress-context` ACP command. That future command would still preserve raw evidence and record before/after metrics.
