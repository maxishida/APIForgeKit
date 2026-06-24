# APIForgeKit System Diagram

Este diagrama mostra o fluxo completo do MVP evidence-first, começando no ACP e no `SKILL.md`.

## APIForgeKit Evidence Harness

```mermaid
flowchart LR
    subgraph entryPoints[Entry Points]
        direction TB
        operator[Human / Operator] --> studio[NiceGUI Studio]
        ide[IDE / AI Client] --> dotcontext[Dotcontext MCP optional]
        acpClient[ACP / CLI Client] --> acpExecutor[ACP Executor]
    end

    subgraph control[Operational Control]
        direction TB
        dotcontext -.-> skillGates[SKILL.md Gates]
        acpExecutor --> skillGates
        skillGates --> coreServices[Core Services]
    end

    subgraph validation[Validation Labs]
        direction TB
        algorithmLab[Algorithm Test Lab]
        apiLab[Generic API Lab]
        providerLab[xAI / Voice Validation]
        tokenCalculator[Token Calculator]
    end

    subgraph evidence[Evidence and Review]
        direction TB
        evidenceStore[PostgreSQL Evidence Store]
        dashboardLogs[Dashboard / Logs]
        contextBuilder[Context Builder / Evidence Pack]
    end

    subgraph handoff[AI Handoff]
        direction TB
        originalHandoff[Original Evidence Handoff]
        headroomOpt[Optional Headroom CLI]
        implementationAi[Implementation AI]
    end

    studio --> algorithmLab
    studio --> apiLab
    studio --> providerLab
    studio --> tokenCalculator
    coreServices --> algorithmLab
    coreServices --> apiLab
    coreServices --> providerLab
    coreServices --> tokenCalculator
    algorithmLab --> evidenceStore
    apiLab --> evidenceStore
    providerLab --> evidenceStore
    tokenCalculator --> evidenceStore
    evidenceStore --> dashboardLogs
    evidenceStore --> contextBuilder
    contextBuilder --> originalHandoff
    originalHandoff --> implementationAi
    contextBuilder -. sanitized copy only .-> headroomOpt
    headroomOpt --> implementationAi
```

`Dotcontext MCP optional` guides an IDE workflow but does not replace the ACP executor or become a source of evidence. PostgreSQL, structured logs, raw exports and the original Evidence Pack remain canonical. `Optional Headroom CLI` runs only after Context Builder readiness and only on a sanitized handoff copy; it never sits in front of provider tests, labs, PostgreSQL, logs or ACP.

```mermaid
flowchart LR
    A[ACP Client / CLI / IDE] --> B[agents/acp_agent.py]
    B --> C[SKILL.md Decision Gates]
    B --> N[ACP protocol_trace audit]
    C --> D[SkillExecutor]
    D --> E{Validation Path}
    E --> F[Algorithm Test Lab]
    E --> G[Generic API Lab]
    E --> H[Token Calculator]
    E --> I[Provider/xAI Validation]
    F --> J[PostgreSQL Evidence Store]
    G --> J
    H --> J
    I --> J
    N --> J
    J --> K[Dashboard / Logs / Context Builder]
    K --> L[Evidence Pack]
    L --> M[Implementation later]
```

## Algorithm Test Lab

```mermaid
flowchart LR
    A[Test Case] --> B[Algorithm Runner]
    B --> C[Expected Output Validator]
    C --> D[Structured Log]
    D --> E[PostgreSQL Evidence Store]
    E --> F[Context Builder]
    F --> G[Evidence Pack]
```

## Generic API Lab

```mermaid
flowchart LR
    A[API/Webhook Contract] --> B{Mode}
    B --> C[dry_run_contract]
    B --> D[real_http with permission]
    C --> E[Expected vs Actual]
    D --> E
    E --> F[PostgreSQL Evidence Store]
    F --> G[Dashboard / Logs / Context Builder]
```

## Token Calculator

```mermaid
flowchart LR
    A[Provider + Model] --> B[Usage Volume]
    B --> C[Token Shape]
    C --> D[pricing_mode]
    D --> E[Cost Estimate]
    E --> F[Token Usage History]
    F --> G[Context Builder]
```

## Provider/xAI Validation

```mermaid
flowchart LR
    A[Official Docs] --> B[Smallest Safe Test]
    B --> C[Request/Response Telemetry]
    C --> D[Structured Event]
    D --> E[PostgreSQL Evidence Store]
    E --> F[Live Dashboard]
    F --> G[Context Builder]
```

## ACP Audit

```mermaid
flowchart LR
    A[ACP initialize/session/new/session/prompt] --> B[Protocol gates]
    B --> C[session_prompt]
    B --> D[prompt_response]
    B --> E[permission_requested]
    C --> F[acp_events]
    D --> F
    E --> F
    F --> G[Context Builder: ACP Evidence]
```

## Operating Rule

Implementation starts only after evidence exists and Context Builder can explain what was validated, what failed, what payloads worked and where the evidence pack lives.
