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

Supported JSON-RPC methods:

- `initialize`
- `session/new`
- `session/prompt`
- `session/cancel`

Protocol behavior implemented in the seed:

- `initialize` advertises local capabilities and stdio MCP support only.
- `session/new` requires an absolute `cwd`, stores stdio MCP metadata and emits `available_commands_update`.
- `session/prompt` emits a `plan` update before executing a command.
- Final summaries stream through `agent_message_chunk` using text content blocks.
- HTTP real/provider-paid paths emit `session/request_permission` before execution.
- `_meta.apiforgekit.sessionId` is included so clients can correlate updates and evidence.

Supported prompt commands:

- `/validate-api-suite whatsapp_validation_pack`
- `/validate-algorithm lead_score`
- `/token-cost provider=xai model=grok-4.3 users=10 requests=20 input=1000 output=500 days=30`
- `/build-context`
- `/export-evidence`

Safety defaults:

- HTTP real requires permission.
- MCP HTTP/SSE is rejected.
- MCP stdio definitions are accepted but treated as external capability metadata in this first version.
- Local PostgreSQL remains accessed through APIForgeKit repositories, not through MCP.
- Secrets from env, headers or MCP metadata must be redacted before logs or reports.

The seed is intentionally additive. It does not replace NiceGUI, PostgreSQL, labs or reports; it only makes the same evidence-first workflow callable from ACP clients.
