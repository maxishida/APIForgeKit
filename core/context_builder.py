from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable, Mapping

from core.report_bundle import create_report_bundle


SUGGESTED_FILES = (
    "/lib/lead-score.ts",
    "/types/lead.ts",
    "/app/api/leads/route.ts",
    "/components/dashboard/LeadScoreChart.tsx",
)

SOURCE_MODE_LABELS = {
    "algorithm_api": "Algorithm + API",
    "algorithm": "Algorithm only",
    "api": "API only",
    "acp": "ACP Evidence",
    "community_pipeline": "Community Pipeline",
    "full": "Full evidence",
}

SECTION_LABELS = {
    "algorithm": "Algorithm Test Lab",
    "api": "API Test Lab",
    "live": "Live Observability",
    "token": "Token Calculator",
    "acp": "ACP Skill Executor",
    "community": "Community Pipeline",
}


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


def build_context_readiness(
    *,
    source_mode: str,
    algorithm_metrics: Mapping[str, object],
    api_metrics: Mapping[str, object],
    live_metrics: Mapping[str, object] | None = None,
    token_metrics: Mapping[str, object] | None = None,
    acp_metrics: Mapping[str, object] | None = None,
    community_metrics: Mapping[str, object] | None = None,
) -> dict[str, object]:
    mode = _normalize_source_mode(source_mode)
    sections = {
        "algorithm": _metric_status(
            total=_number(algorithm_metrics, "total_results"),
            passed=_number(algorithm_metrics, "passed"),
            failed=_number(algorithm_metrics, "failed"),
            label="Algorithm Test Lab",
            evidence_modes=_mapping(algorithm_metrics, "evidence_modes"),
        ),
        "api": _metric_status(
            total=_number(api_metrics, "total_results"),
            passed=_number(api_metrics, "passed"),
            failed=_number(api_metrics, "failed"),
            label="API Test Lab",
            evidence_modes=_mapping(api_metrics, "evidence_modes"),
        ),
        "live": _metric_status(
            total=_number(live_metrics or {}, "total_tests"),
            passed=_number(live_metrics or {}, "success"),
            failed=_number(live_metrics or {}, "failures"),
            label="Live Observability",
            evidence_modes=_mapping(live_metrics or {}, "evidence_modes"),
        ),
        "token": _metric_status(
            total=_number(token_metrics or {}, "total_estimates"),
            passed=_number(token_metrics or {}, "total_estimates"),
            failed=0,
            label="Token Calculator",
            evidence_modes=_mapping(token_metrics or {}, "evidence_modes"),
        ),
        "acp": _metric_status(
            total=_number(acp_metrics or {}, "total_events"),
            passed=_number(acp_metrics or {}, "successful_prompts"),
            failed=_number(acp_metrics or {}, "failed_prompts"),
            label="ACP Skill Executor",
            evidence_modes=_mapping(acp_metrics or {}, "evidence_modes"),
        ),
        "community": _community_metric_status(community_metrics or {}),
    }
    required = _required_sections(mode)
    required_statuses = [sections[name]["status"] for name in required]
    if any(status == "Has failures" for status in required_statuses):
        overall = "Has failures"
        message = "Existem falhas nas evidências obrigatórias. Corrija ou documente antes de pedir implementação."
    elif required_statuses and all(status == "Ready" for status in required_statuses):
        overall = "Ready"
        message = "Evidência suficiente para gerar contexto técnico reutilizável."
    else:
        overall = "Needs tests"
        message = "Rode pelo menos uma suite exigida pelo modo selecionado antes de implementar."
    return {
        "source_mode": mode,
        "overall": {"status": overall, "message": message, "required_sections": required},
        **sections,
    }


def build_guided_context_bundle(
    *,
    source_mode: str,
    live_context: str,
    algorithm_context: str,
    api_context: str,
    token_context: str,
    algorithm_metrics: Mapping[str, object],
    api_metrics: Mapping[str, object],
    live_metrics: Mapping[str, object] | None = None,
    token_metrics: Mapping[str, object] | None = None,
    acp_context: str = "",
    acp_metrics: Mapping[str, object] | None = None,
    community_context: str = "",
    community_metrics: Mapping[str, object] | None = None,
) -> dict[str, object]:
    mode = _normalize_source_mode(source_mode)
    readiness = build_context_readiness(
        source_mode=mode,
        algorithm_metrics=algorithm_metrics,
        api_metrics=api_metrics,
        live_metrics=live_metrics or {},
        token_metrics=token_metrics or {},
        acp_metrics=acp_metrics or {},
        community_metrics=community_metrics or {},
    )
    contexts = {
        "live": live_context.strip(),
        "algorithm": algorithm_context.strip(),
        "api": api_context.strip(),
        "token": token_context.strip(),
        "acp": acp_context.strip(),
        "community": community_context.strip(),
    }
    context = _render_guided_context(
        source_mode=mode,
        readiness=readiness,
        contexts=contexts,
        algorithm_metrics=algorithm_metrics,
        api_metrics=api_metrics,
        live_metrics=live_metrics or {},
        token_metrics=token_metrics or {},
        acp_metrics=acp_metrics or {},
    )
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "source_mode": mode,
        "source_label": SOURCE_MODE_LABELS[mode],
        "readiness": readiness,
        "algorithm_metrics": deepcopy(dict(algorithm_metrics)),
        "api_metrics": deepcopy(dict(api_metrics)),
        "live_metrics": deepcopy(dict(live_metrics or {})),
        "token_metrics": deepcopy(dict(token_metrics or {})),
        "acp_metrics": deepcopy(dict(acp_metrics or {})),
        "community_metrics": deepcopy(dict(community_metrics or {})),
        "contexts": contexts,
        "context": context,
    }


def export_guided_context_bundle(output_dir: str | Path, bundle: Mapping[str, object]) -> dict[str, str]:
    mode = _normalize_source_mode(str(bundle.get("source_mode") or "full"))
    markdown = str(bundle.get("context") or "")
    payload = deepcopy(dict(bundle))
    return create_report_bundle(
        output_dir=output_dir,
        name=f"context_builder_{mode}",
        markdown=markdown,
        payload=payload,
    )


def build_final_ai_prompt(bundle: Mapping[str, object]) -> str:
    readiness = bundle.get("readiness") if isinstance(bundle.get("readiness"), Mapping) else {}
    overall = readiness.get("overall", {}) if isinstance(readiness.get("overall"), Mapping) else {}
    contexts = bundle.get("contexts") if isinstance(bundle.get("contexts"), Mapping) else {}
    source_label = str(bundle.get("source_label") or bundle.get("source_mode") or "Full evidence")
    evidence_modes = _bundle_evidence_modes(bundle)
    selected_context = str(bundle.get("context") or "")
    compact_context = selected_context[:6000]
    return "\n".join(
        [
            "Use este contexto técnico validado pelo APIForgeKit.",
            "",
            f"Fonte: {source_label}",
            f"Readiness: {overall.get('status', 'Needs tests')}",
            f"Evidências: {_render_modes(evidence_modes)}",
            "",
            "Regras obrigatórias:",
            "- Implementar somente comportamento validado.",
            "- Nao invente payloads, regras ou endpoints.",
            "- Se faltar evidência, pare e peça novo teste no APIForgeKit.",
            "- Preserve tratamento de erro, telemetria e limites descritos no contexto.",
            "",
            "Resumo das fontes:",
            _render_context_presence(contexts),
            "",
            "Contexto validado:",
            compact_context,
        ]
    )


def _normalize_source_mode(source_mode: str) -> str:
    mode = str(source_mode or "algorithm_api").strip().lower().replace("-", "_")
    aliases = {
        "algorithm + api": "algorithm_api",
        "algorithm_api": "algorithm_api",
        "algorithm only": "algorithm",
        "api only": "api",
        "acp evidence": "acp",
        "full evidence": "full",
        "community pipeline": "community_pipeline",
    }
    normalized = aliases.get(mode, mode)
    return normalized if normalized in SOURCE_MODE_LABELS else "algorithm_api"


def _required_sections(source_mode: str) -> list[str]:
    if source_mode == "algorithm_api":
        return ["algorithm", "api"]
    if source_mode == "algorithm":
        return ["algorithm"]
    if source_mode == "api":
        return ["api"]
    if source_mode == "acp":
        return ["acp"]
    if source_mode == "community_pipeline":
        return ["community"]
    if source_mode == "full":
        return ["algorithm", "api", "live", "token", "acp", "community"]
    return ["algorithm", "api", "live", "token", "acp"]


def _community_metric_status(metrics: Mapping[str, object]) -> dict[str, object]:
    status = str(metrics.get("status") or "Needs tests")
    if status == "Ready":
        normalized = "Ready"
    elif status == "Has failures":
        normalized = "Has failures"
    else:
        normalized = "Needs tests"
    return {
        "status": normalized,
        "label": str(metrics.get("label") or "Community Pipeline"),
        "total": _number(metrics, "total"),
        "passed": _number(metrics, "passed"),
        "failed": _number(metrics, "failed"),
        "evidence_modes": _mapping(metrics, "evidence_modes"),
        "message": str(metrics.get("message") or "Rode member_engagement_score e community_bot_engine."),
    }


def _metric_status(
    *,
    total: int,
    passed: int,
    failed: int,
    label: str,
    evidence_modes: Mapping[str, object] | None = None,
) -> dict[str, object]:
    if failed > 0:
        status = "Has failures"
        message = f"{label} tem {failed} falha(s) que precisam ser revisadas."
    elif total > 0:
        status = "Ready"
        message = f"{label} possui {total} evidência(s) validada(s)."
    else:
        status = "Needs tests"
        message = f"{label} ainda não tem evidência registrada."
    return {
        "status": status,
        "label": label,
        "total": total,
        "passed": passed,
        "failed": failed,
        "evidence_modes": deepcopy(dict(evidence_modes or {})),
        "message": message,
    }


def _number(metrics: Mapping[str, object], key: str) -> int:
    value = metrics.get(key, 0)
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _mapping(metrics: Mapping[str, object], key: str) -> dict[str, object]:
    value = metrics.get(key, {})
    return dict(value) if isinstance(value, Mapping) else {}


def _render_guided_context(
    *,
    source_mode: str,
    readiness: Mapping[str, object],
    contexts: Mapping[str, str],
    algorithm_metrics: Mapping[str, object],
    api_metrics: Mapping[str, object],
    live_metrics: Mapping[str, object],
    token_metrics: Mapping[str, object],
    acp_metrics: Mapping[str, object],
) -> str:
    overall = readiness.get("overall", {})
    missing = [
        section
        for section in _required_sections(source_mode)
        if (readiness.get(section, {}) or {}).get("status") == "Needs tests"
    ]
    failures = [
        section
        for section in _required_sections(source_mode)
        if (readiness.get(section, {}) or {}).get("status") == "Has failures"
    ]
    parts = [
        "# Contexto Técnico - APIForgeKit Studio",
        "",
        f"Gerado em: {datetime.now(UTC).isoformat()}",
        f"Modo de fonte: {SOURCE_MODE_LABELS[source_mode]}",
        f"Readiness: {overall.get('status', 'Needs tests')}",
        "",
        "## Resumo Executivo",
        "",
        str(overall.get("message", "")),
        "",
        "## Evidências Disponíveis",
        "",
        _render_readiness_lines(readiness),
        "",
        "## Métricas",
        "",
        _render_metrics(
            algorithm_metrics,
            api_metrics,
            live_metrics,
            token_metrics,
            acp_metrics,
            readiness.get("community", {}),
        ),
        "",
        "## Bloqueios antes de implementar",
        "",
        _render_blockers(missing, failures),
        "",
        "## O que foi testado",
        "",
        _selected_contexts(source_mode, contexts),
        "",
        "## Payloads corretos",
        "",
        "Os payloads aprovados estão preservados nos logs estruturados, resultados de API e casos de algoritmo incluídos neste pacote.",
        "",
        "## Limitações encontradas",
        "",
        _render_limitations(readiness),
        "",
        "## Recomendações",
        "",
        "- Rode testes antes de pedir implementação para IA.",
        "- Use somente evidências com readiness `Ready` como base de decisão.",
        "- Corrija falhas ou registre exceções antes de abrir tarefa de implementação.",
        "- Mantenha secrets redigidos em logs e relatórios.",
        "",
        "## Impacto para Implementação Futura",
        "",
        "- A IA deve receber este contexto como contrato técnico, não como fonte especulativa.",
        "- Next.js, APIs ou integrações futuras devem reproduzir os casos validados como testes.",
        "- O fluxo aprovado continua: Teste Real -> Logs Estruturados -> Evidências -> Contexto Técnico -> Implementação.",
    ]
    return "\n".join(parts)


def _render_readiness_lines(readiness: Mapping[str, object]) -> str:
    lines = []
    for key in ("algorithm", "api", "live", "token", "acp", "community"):
        item = readiness.get(key, {})
        lines.append(
            f"- {item.get('label', key)}: `{item.get('status', 'Needs tests')}` "
            f"total={item.get('total', 0)} passed={item.get('passed', 0)} failed={item.get('failed', 0)} "
            f"modes={_render_modes(dict(item.get('evidence_modes') or {}))}"
        )
    return "\n".join(lines)


def _render_metrics(
    algorithm_metrics: Mapping[str, object],
    api_metrics: Mapping[str, object],
    live_metrics: Mapping[str, object],
    token_metrics: Mapping[str, object],
    acp_metrics: Mapping[str, object],
    community_readiness: Mapping[str, object] | None = None,
) -> str:
    community = community_readiness or {}
    return "\n".join(
        [
            f"- Algorithm results: {_number(algorithm_metrics, 'total_results')} | passed={_number(algorithm_metrics, 'passed')} | failed={_number(algorithm_metrics, 'failed')}",
            f"- API results: {_number(api_metrics, 'total_results')} | passed={_number(api_metrics, 'passed')} | failed={_number(api_metrics, 'failed')} | modes={_render_modes(_mapping(api_metrics, 'evidence_modes'))}",
            f"- Live tests: {_number(live_metrics, 'total_tests')} | success={_number(live_metrics, 'success')} | failures={_number(live_metrics, 'failures')}",
            f"- Token estimates: {_number(token_metrics, 'total_estimates')}",
            f"- ACP events: {_number(acp_metrics, 'total_events')} | successful_prompts={_number(acp_metrics, 'successful_prompts')} | permission_requests={_number(acp_metrics, 'permission_requests')} | modes={_render_modes(_mapping(acp_metrics, 'evidence_modes'))}",
            f"- Community Pipeline: `{community.get('status', 'Needs tests')}` | total={community.get('total', 0)} | passed={community.get('passed', 0)} | failed={community.get('failed', 0)}",
        ]
    )


def _render_modes(modes: Mapping[str, object]) -> str:
    if not modes:
        return "none"
    return ", ".join(f"{mode}={count}" for mode, count in sorted(modes.items()))


def _bundle_evidence_modes(bundle: Mapping[str, object]) -> dict[str, int]:
    modes: dict[str, int] = {}
    for metrics_key in ("algorithm_metrics", "api_metrics", "live_metrics", "token_metrics", "acp_metrics", "community_metrics"):
        metrics = bundle.get(metrics_key)
        if not isinstance(metrics, Mapping):
            continue
        for mode, count in _mapping(metrics, "evidence_modes").items():
            try:
                modes[str(mode)] = modes.get(str(mode), 0) + int(count or 0)
            except (TypeError, ValueError):
                modes[str(mode)] = modes.get(str(mode), 0)
    return modes


def _render_context_presence(contexts: Mapping[str, object]) -> str:
    if not contexts:
        return "- Nenhuma fonte de contexto anexada."
    lines = []
    for key in ("algorithm", "api", "live", "token", "acp", "community"):
        text = str(contexts.get(key) or "").strip()
        lines.append(f"- {SECTION_LABELS.get(key, key)}: {'incluida' if text else 'ausente'}")
    return "\n".join(lines)


def _render_blockers(missing: list[str], failures: list[str]) -> str:
    lines = []
    if missing:
        labels = ", ".join(SECTION_LABELS.get(section, section) for section in missing)
        lines.append(f"- Rode pelo menos uma suite para: {labels}.")
    if failures:
        labels = ", ".join(SECTION_LABELS.get(section, section) for section in failures)
        lines.append(f"- Corrija falhas registradas em: {labels}.")
    return "\n".join(lines) if lines else "- Nenhum bloqueio crítico encontrado."


def _selected_contexts(source_mode: str, contexts: Mapping[str, str]) -> str:
    selected = _required_sections(source_mode)
    if source_mode == "full":
        selected = ["algorithm", "api", "live", "token", "acp", "community"]
    if source_mode == "community_pipeline":
        selected = ["community"]
    rendered = []
    for key in selected:
        text = contexts.get(key, "").strip()
        label = SECTION_LABELS.get(key, key)
        rendered.append(f"### {label}\n\n{text or '- Nenhum contexto disponível ainda.'}")
    return "\n\n".join(rendered)


def _render_limitations(readiness: Mapping[str, object]) -> str:
    limitations = []
    for key in ("algorithm", "api", "live", "token", "acp", "community"):
        item = readiness.get(key, {})
        if item.get("status") != "Ready":
            limitations.append(f"- {item.get('label', key)}: {item.get('message', 'sem evidência suficiente')}")
    return "\n".join(limitations) if limitations else "- Nenhuma limitação crítica encontrada nas fontes selecionadas."
