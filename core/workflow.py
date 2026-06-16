from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy


OFFICIAL_VALIDATION_JOURNEY = (
    {
        "number": 1,
        "title": "Abrir Tutorial",
        "route": "/tutorial",
        "cta_label": "Open Tutorial",
        "command": "python app.py",
        "evidence": "Entender a jornada oficial antes de rodar validações.",
        "evidence_mode": "guide",
        "help": "Comece pelo mapa visual para saber o que é seed, dry-run, log, contexto e evidence pack.",
    },
    {
        "number": 2,
        "title": "Rodar Algorithm Suite",
        "route": "/algorithm-test-lab",
        "cta_label": "Run Algorithm Suite",
        "command": "npm run algorithm:suite",
        "evidence": "Suite lead_score com expected vs actual, diff e invariantes.",
        "evidence_mode": "seed_validation",
        "help": "Valida lógica determinística sem LLM. O alvo atual é lead_score 17/17.",
    },
    {
        "number": 3,
        "title": "Rodar API Contract Dry-run",
        "route": "/api-test-lab",
        "cta_label": "Run API Dry-run",
        "command": "",
        "evidence": "WhatsApp validation pack salvo como contrato local.",
        "evidence_mode": "dry_run_contract",
        "help": "Use Run Contract Dry-run para provar payload, expected response e diff sem chamar API real.",
    },
    {
        "number": 4,
        "title": "Ver Dashboard",
        "route": "/live-dashboard",
        "cta_label": "Open Dashboard",
        "command": "",
        "evidence": "Métricas, latência, modos de evidência e falhas recentes visíveis.",
        "evidence_mode": "dashboard_metrics",
        "help": "Confira se a telemetria confirma o que foi executado antes de gerar contexto.",
    },
    {
        "number": 5,
        "title": "Abrir Logs",
        "route": "/logs",
        "cta_label": "Open Logs",
        "command": "",
        "evidence": "JSON estruturado filtrável por status, módulo e evidence_mode.",
        "evidence_mode": "structured_logs",
        "help": "Use logs para inspecionar request, response, erro, recomendação e payload sanitizado.",
    },
    {
        "number": 6,
        "title": "Gerar Context Builder",
        "route": "/context-builder",
        "cta_label": "Open Context Builder",
        "command": 'python run_acp_prompt.py "/build-context"',
        "evidence": "Contexto técnico com readiness, métricas, bloqueios e fontes.",
        "evidence_mode": "technical_context",
        "help": "O Context Builder é o gate antes de pedir qualquer implementação para IA.",
    },
    {
        "number": 7,
        "title": "Baixar Evidence Pack",
        "route": "/context-builder",
        "cta_label": "Download Evidence Pack",
        "command": "Export ZIP no Context Builder",
        "evidence": "Markdown, JSON, HTML e ZIP exportados e registrados em context_exports.",
        "evidence_mode": "evidence_pack",
        "help": "Use Download .md para IA rápida; use Export ZIP/JSON/HTML para revisão e auditoria pelo registro context_exports.",
    },
    {
        "number": 8,
        "title": "Usar contexto com IA",
        "route": "/context-builder",
        "cta_label": "Use Context With AI",
        "command": "",
        "evidence": "Prompt curto baseado em evidência, sem comportamento inventado.",
        "evidence_mode": "llm_context",
        "help": "A IA deve implementar somente o que foi validado e documentado no contexto.",
    },
)


def official_journey_titles() -> list[str]:
    return [str(step["title"]) for step in OFFICIAL_VALIDATION_JOURNEY]


def official_journey_steps() -> list[dict[str, object]]:
    return [deepcopy(dict(step)) for step in OFFICIAL_VALIDATION_JOURNEY]


def build_official_journey_progress(
    *,
    db_online: bool,
    algorithm_metrics: Mapping[str, object],
    api_metrics: Mapping[str, object],
    provider_metrics: Mapping[str, object],
) -> list[dict[str, object]]:
    algorithm_ready = _number(algorithm_metrics, "passed") > 0 and _number(algorithm_metrics, "failed") == 0
    api_modes = _mapping(api_metrics, "evidence_modes")
    api_ready = _number(api_metrics, "passed") > 0 and int(api_modes.get("dry_run_contract") or 0) > 0
    dashboard_ready = db_online
    logs_ready = (
        _number(algorithm_metrics, "total_results") > 0
        or _number(api_metrics, "total_results") > 0
        or _number(provider_metrics, "total_tests") > 0
    )
    context_ready = algorithm_ready or api_ready
    evidence_pack_ready = context_ready
    llm_ready = context_ready
    completed = {
        1: True,
        2: algorithm_ready,
        3: api_ready,
        4: dashboard_ready,
        5: logs_ready,
        6: context_ready,
        7: evidence_pack_ready,
        8: llm_ready,
    }
    steps = official_journey_steps()
    for step in steps:
        number = int(step["number"])
        step["status"] = "Ready" if completed[number] else "Pending"
    return steps


def _number(metrics: Mapping[str, object], key: str) -> int:
    try:
        return int(metrics.get(key) or 0)
    except (TypeError, ValueError):
        return 0


def _mapping(metrics: Mapping[str, object], key: str) -> dict[str, object]:
    value = metrics.get(key, {})
    return dict(value) if isinstance(value, Mapping) else {}
