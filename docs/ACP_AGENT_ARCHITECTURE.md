# APIForgeKit ACP Agent Architecture

## Why ACP Fits

Agent Client Protocol is a good V2 direction because APIForgeKit is becoming an evidence-first execution environment, not only a dashboard.

ACP can let an editor or agent client ask APIForgeKit to run validations through a standard protocol while the Studio keeps PostgreSQL, logs, reports and dashboards as the source of truth.

Official docs reviewed:

- https://agentclientprotocol.com/get-started/introduction
- https://agentclientprotocol.com/get-started/architecture
- https://agentclientprotocol.com/protocol/overview
- https://agentclientprotocol.com/protocol/session-setup
- https://agentclientprotocol.com/protocol/prompt-turn
- https://agentclientprotocol.com/protocol/agent-plan
- https://agentclientprotocol.com/protocol/slash-commands
- https://agentclientprotocol.com/protocol/extensibility

Key takeaways:

- ACP standardizes communication between clients/editors and agents.
- Local agents commonly run as subprocesses over stdio.
- Communication uses JSON-RPC requests and notifications.
- Session updates can stream progress to the client UI.
- Clients can request permissions for tool calls.
- ACP reuses MCP-friendly concepts where possible.

## Recommended V2 Shape

```txt
ACP Client / Editor
↓
APIForgeKit ACP Agent
↓
SKILL.md Decision Gates
↓
Generic API Lab / Algorithm Test Lab / Token Calculator
↓
PostgreSQL Evidence Store
↓
Context Builder / Report Bundle
```

## Agent Responsibility

The ACP agent should be an execution bridge. It should not invent API behavior or skip validation.

It should:

- classify the request
- create a validation plan
- request permission for costly or risky actions
- execute the correct lab
- stream progress events
- save structured evidence
- return context/report paths

It should not:

- generate production code directly
- bypass `SKILL.md`
- run paid provider calls without explicit permission
- log secrets
- use seeded pricing as billing truth

## Suggested Capabilities

```txt
validate_api_contract
validate_algorithm_suite
calculate_token_usage
build_technical_context
export_evidence_bundle
explain_next_step
```

## Example Session

```txt
User:
Validate this WhatsApp payload and tell me if it is ready for implementation.

ACP Agent:
1. Classifies request as Generic API Validation.
2. Creates a short validation plan.
3. Runs dry-run suite or asks permission for real API call.
4. Streams events: started, payload checked, response validated, diff generated.
5. Saves result to PostgreSQL.
6. Returns report/context path.
```

## Implementation Order

1. Keep V1 NiceGUI local-first stable.
2. Define an internal command interface around existing core services.
3. Add ACP wrapper that maps protocol sessions to internal commands.
4. Stream `session/update`-style progress from test events.
5. Add permission gates for paid calls, file writes and shell commands.
6. Add tests with fake ACP requests before exposing real provider actions.

## Architecture Opinion

ACP is a strong fit for APIForgeKit, but it should be the protocol layer, not the product core.

The core remains:

```txt
Test
↓
Log
↓
Evidence
↓
Context
↓
Implementation later
```

ACP simply makes that workflow callable from a professional agent client or IDE.

## Implemented V2 Seed

Run the local ACP executor:

```bash
python -m agents.acp_agent
```

or:

```bash
npm run acp
```

For a single local smoke prompt without writing JSON-RPC by hand:

```bash
python run_acp_prompt.py "/validate-lead-score"
python run_acp_prompt.py "/validate-token-cost provider=xai model=grok-4.3 users=10 requests=20"
python run_acp_prompt.py "/validate-context-readiness"
python run_acp_prompt.py "/validate-voice-roundtrip"
python run_acp_prompt.py "/build-context"
```

IDE/client stdio config example:

```json
{
  "command": "npm",
  "args": ["run", "acp"],
  "cwd": "D:\\myworksapce\\Apiforgekit\\APIForgeKit",
  "transport": "stdio"
}
```

Send one JSON-RPC object per line. The required handshake is:

1. `initialize`
2. `session/new` with absolute `cwd`
3. read `available_commands_update`
4. `session/prompt` with text `ContentBlock[]`
5. read `session/update` notifications before the final prompt response

Supported JSON-RPC methods:

- `initialize`
- `session/new`
- `session/prompt`
- `session/cancel`

Protocol behavior implemented in the seed:

- `initialize` returns ACP v1 fields: `protocolVersion`, `agentInfo`, `agentCapabilities`, `authMethods` and APIForgeKit `_meta`.
- MCP stdio support is advertised in `_meta.apiforgekit.supportsMcpStdio`; ACP `mcpCapabilities` keeps `http=false` and `sse=false`.
- `session/new` requires an absolute `cwd`, stores stdio MCP metadata and emits `available_commands_update`.
- `available_commands_update` advertises command names without `/`; prompts may use `/validate-lead-score` or legacy `validate-lead-score`.
- `session/prompt` accepts official ACP `ContentBlock[]` text prompts and legacy string prompts.
- `session/prompt` emits `plan`, `tool_call`, `tool_call_update` and final `agent_message_chunk`.
- Final summaries stream through `agent_message_chunk` using text content blocks; `PromptResponse` keeps only `stopReason` and `_meta`.
- HTTP real/provider-paid paths emit `session/request_permission` before execution and return `PromptResponse.stopReason="refusal"` with `_meta.apiforgekit.permissionRequired=true`.
- `_meta.apiforgekit.sessionId`, command, algorithm, run ID, context path and evidence ZIP are included when available so clients can correlate updates and evidence.
- `run_acp_workflow.py` treats validation prompts as passed only when `stopReason=end_turn` and the latest `tool_call_update.rawOutput.status` is `success`; permission gates must return `stopReason=refusal` and emit `session/request_permission`.

Supported prompt commands:

- announced: `validate-api-suite`, prompt: `/validate-api-suite whatsapp_validation_pack`
- announced: `validate-lead-score`, prompt: `/validate-lead-score`
- announced: `validate-algorithm`, prompt: `/validate-algorithm lead_score`
- announced: `validate-token-cost`, prompt: `/validate-token-cost provider=xai model=grok-4.3 users=10 requests=20 input=1000 output=500 days=30`
- announced: `token-cost`, prompt: `/token-cost provider=xai model=grok-4.3 users=10 requests=20 input=1000 output=500 days=30`
- announced: `validate-context-readiness`, prompt: `/validate-context-readiness` or `/validate-context-readiness mode=algorithm_api`
- announced: `validate-voice-roundtrip`, prompt: `/validate-voice-roundtrip`
- persistence: `/token-cost` only saves to PostgreSQL when `save=true`; default mode is calculation-only to avoid noisy evidence.
- validation alias: `/validate-token-cost` uses the same calculator but reports `token_cost_validation` for ACP clients.
- docs verified pricing: add `pricing_mode=docs_verified pricing_source=<official_url> input_price=<usd> output_price=<usd> cached_price=<usd>` after checking provider docs.
- announced: `build-context`, prompt: `/build-context`
- announced: `export-evidence`, prompt: `/export-evidence`

Voice rules:

- `/validate-voice-roundtrip` reads the latest saved `xai/voice_roundtrip` evidence from PostgreSQL.
- It does not call xAI by itself.
- It requires the core voice events: `lead_received`, `user_message_received`, `tts_audio_received`, `transcript_received`, `agent_response_received` and `voice_call_completed`.
- `/validate-voice-roundtrip --run-real` emits `session/request_permission` and returns `stopReason="refusal"` until a real permission continuation flow exists.

Context readiness:

- `/validate-context-readiness` builds the same guided Context Builder bundle used by the UI.
- Default mode is `algorithm_api`.
- It returns `success` for `Ready`, `not_validated` for `Needs tests` and `failed` for `Has failures`.
- When observability is configured, it records the generated Markdown/JSON/HTML/ZIP paths in `context_exports`.

## Lead Score ACP Best Practice

For score-based lead algorithms, ACP should behave like a validation harness:

```txt
/validate-lead-score
↓
available_commands_update
↓
plan: classify, run suite, verify invariants, compare, export evidence pack
↓
Algorithm Test Lab
↓
PostgreSQL evidence
↓
agent_message_chunk with summary
↓
Context Builder output
```

Required evidence:

- input JSON
- expected output JSON
- actual output JSON
- diff
- invariants: payload validated, deterministic output, clamped score and invalid override
- pass/fail status
- deterministic score and classification
- reasons for every score contribution or penalty
- context path and evidence pack path for future implementation

Permission rules:

- no permission needed for local deterministic suite execution
- permission required for external APIs, provider calls, private PII enrichment or file writes outside `exports/`
- Next.js implementation remains blocked until Context Builder has evidence

Safety defaults:

- HTTP real requires permission.
- MCP HTTP/SSE is rejected.
- MCP stdio definitions are accepted but treated as external capability metadata in this first version.
- Local PostgreSQL remains accessed through APIForgeKit repositories, not through MCP.
- Secrets from env, headers or MCP metadata must be redacted before logs or reports.

The seed is intentionally additive. It does not replace NiceGUI, PostgreSQL, labs or reports; it only makes the same evidence-first workflow callable from ACP clients.

## ACP Audit Persistence

ACP now persists protocol evidence in PostgreSQL:

- `acp_sessions`: session ID, cwd, MCP stdio metadata, status and summary.
- `acp_events`: `session_created`, `session_prompt`, `prompt_response`, `permission_requested` and `session_cancelled`.

Context Builder reads these records as `ACP Evidence`.

Evidence modes:

- `protocol_trace`: normal ACP/CLI/IDE execution trace.
- `blocked`: permission gate or refused risky action.

This lets a user prove not only that a lab produced evidence, but also how an agent client invoked the validation workflow.

## Current Local-Seed Limitations

- ACP protocol version is v1-only and always returns `protocolVersion=1`.
- Text `ContentBlock[]` prompts are supported; legacy string prompts are accepted for scripts.
- Resource, image and audio blocks are refused until APIForgeKit has a specific resource validation path.
- `session/request_permission` currently blocks risky execution and returns `stopReason="refusal"`; there is no continuation flow consuming a permission result yet.
- `/token-cost` uses local seeded pricing by default. `docs_verified` is supported when the user provides an official source URL and manually verified input/output/cached prices.
- `/validate-token-cost` is preferred for ACP validation, while `/token-cost` stays as compatibility syntax.
- `/validate-voice-roundtrip` validates saved evidence only; actual xAI Voice execution remains UI/CLI-driven in this version.
- PostgreSQL should be online for commands that persist evidence.
