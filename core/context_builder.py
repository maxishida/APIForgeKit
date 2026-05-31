from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable, Mapping


SUGGESTED_FILES = (
    "/lib/lead-score.ts",
    "/types/lead.ts",
    "/app/api/leads/route.ts",
    "/components/dashboard/LeadScoreChart.tsx",
)


def _value(record: Mapping[str, object], key: str, default: object = "") -> object:
    return record.get(key, default)


def build_technical_context(records: Iterable[Mapping[str, object]]) -> str:
    rows = list(records)
    success_rows = [row for row in rows if _value(row, "status") == "success"]
    error_rows = [row for row in rows if _value(row, "error")]
    cases = "\n".join(
        (
            f"- `{_value(row, 'id')}` | {_value(row, 'source')} | "
            f"score `{_value(row, 'score')}` | `{_value(row, 'classification')}` | "
            f"{_value(row, 'recommended_action')}"
        )
        for row in rows
    ) or "- Nenhum teste persistido ainda."
    errors = "\n".join(f"- `{_value(row, 'id')}`: {_value(row, 'error')}" for row in error_rows)
    if not errors:
        errors = "- Nenhum erro registrado nos testes selecionados."
    suggested = "\n".join(f"- `{path}`" for path in SUGGESTED_FILES)

    return f"""# Contexto Técnico — Lead Algorithm Lab

Gerado em: {datetime.now(UTC).isoformat()}

## Objetivo

Implementar algoritmo determinístico de lead score em Next.js/TypeScript.

## Regras Validadas

- Palavras fortes: comprar, preço, orçamento, urgente, hoje, agora, WhatsApp, ligação.
- Cada palavra forte adiciona 10 pontos.
- WhatsApp: +25
- Ligação: +30
- Landing Page: +20
- Instagram: +15
- LinkedIn: +10
- Urgência alta: +25; média: +15; baixa: +5.
- Interesse alto: +25; médio: +15; baixo: +5.
- Telefone: +10; e-mail: +5; cliente anterior: +20.
- Mensagem vazia ou spam classifica como `invalid_lead`.
- Sem telefone e sem e-mail remove 20 pontos.
- Mensagem muito curta remove 10 pontos.

## Fórmula de Score

`score = clamp(palavras + origem + urgência + interesse + contato + histórico - penalidades, 0, 100)`

## Entradas

`lead_name`, `source`, `message`, `budget`, `urgency`, `interest`, `has_phone`, `has_email`, `previous_customer`.

## Saídas

`lead_id`, `score`, `status`, `confidence`, `reasons`, `recommended_action`, `nextjs_impact`.

## Casos de Teste

{cases}

## Resultados

- Total de testes analisados: {len(rows)}
- Testes com sucesso: {len(success_rows)}
- Erros encontrados: {len(error_rows)}

## Erros Encontrados

{errors}

## Logs Relevantes

Os registros persistidos em PostgreSQL e JSONL são a fonte de evidência para a implementação.

## Comportamentos Esperados

- O algoritmo não chama IA nem APIs externas.
- A IA deve apenas implementar a lógica validada.
- O status `urgent_lead` deve acionar atendimento humano imediato.
- O status `invalid_lead` deve bloquear qualificação automática.

## Arquivos sugeridos

{suggested}

## Observações

Este algoritmo não depende de IA para decidir.
A IA deve apenas implementar a lógica validada.
"""


def export_technical_context(path: str | Path, records: Iterable[Mapping[str, object]]) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_technical_context(records), encoding="utf-8")
    return output_path
