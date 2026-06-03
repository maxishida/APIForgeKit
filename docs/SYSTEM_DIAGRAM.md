# APIForgeKit System Diagram

Este diagrama mostra o fluxo completo do MVP evidence-first, começando no ACP e no `SKILL.md`.

```mermaid
flowchart LR
    A[ACP Client / CLI / IDE] --> B[agents/acp_agent.py]
    B --> C[SKILL.md Decision Gates]
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

## Operating Rule

Implementation starts only after evidence exists and Context Builder can explain what was validated, what failed, what payloads worked and where the evidence pack lives.
