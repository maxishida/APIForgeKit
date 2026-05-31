from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path


def generate_nextjs_blueprint() -> str:
    return f"""# Next.js Blueprint — Lead Score Implementation

Gerado em: {datetime.now(UTC).isoformat()}

## Diretriz

Não gerar código completo nesta etapa. Este blueprint descreve estrutura, contratos e responsabilidades.

## Estrutura de Pastas

```txt
app/
  api/
    leads/
      route.ts
actions/
  createLead.ts
components/
  dashboard/
    LeadScoreChart.tsx
    LeadStatusDonut.tsx
    LeadOriginBar.tsx
lib/
  lead-score.ts
  prisma.ts
types/
  lead.ts
prisma/
  schema.prisma
tests/
  lead-score.test.ts
```

## Tipos TypeScript

- `LeadInput`: dados recebidos pelo formulário ou API.
- `LeadScoreResult`: `leadId`, `score`, `status`, `confidence`, `reasons`, `recommendedAction`, `nextjsImpact`.
- `LeadStatus`: `cold_lead | warm_lead | hot_lead | urgent_lead | invalid_lead`.

## Prisma Local

- `prisma/schema.prisma` deve modelar a tabela `LeadTest`.
- `/lib/prisma.ts` deve expor um PrismaClient singleton para Next.js local.
- A implementação final deve persistir entrada bruta, saída bruta, score, status, motivos e recomendação.

## Função Principal

- `/lib/lead-score.ts` deve exportar `calculateLeadScore(input: LeadInput): LeadScoreResult`.
- A função deve ser determinística e não deve chamar LLM, API externa ou provider.
- A fórmula deve espelhar as regras validadas pelo APIForgeKit Studio.

## API Route

- `/app/api/leads/route.ts` deve aceitar `POST`.
- Validar payload.
- Calcular score.
- Persistir no Prisma.
- Retornar JSON estruturado.

## Actions

- `/actions/createLead.ts` deve encapsular chamada de criação quando usada por Server Actions.

## Componentes de Dashboard

- `/components/dashboard/LeadScoreChart.tsx`: distribuição de score.
- `/components/dashboard/LeadStatusDonut.tsx`: classificação dos leads.
- `/components/dashboard/LeadOriginBar.tsx`: origem dos leads.

## Testes Unitários Sugeridos

- Mensagem vazia retorna `invalid_lead`.
- Spam retorna `invalid_lead`.
- WhatsApp + urgência alta + interesse alto gera lead quente ou urgente.
- Sem telefone e sem e-mail aplica penalidade.
- Mensagem curta aplica penalidade.
- Score máximo é 100.
- Boundaries: 0-30, 31-60, 61-80, 81-100.
"""


def export_nextjs_blueprint(path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(generate_nextjs_blueprint(), encoding="utf-8")
    return output_path
