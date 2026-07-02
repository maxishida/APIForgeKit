from __future__ import annotations

from pathlib import Path

from core.algorithm_test_lab import AlgorithmTestRepository, build_algorithm_context

COMMUNITY_ALGORITHMS = ("community_bot_engine", "member_engagement_score")
PIPELINE_HANDOFF_FILENAME = "CODE_GTA6_COMMUNITY_PIPELINE_IMPLEMENTATION_CONTEXT.md"
BOT_HANDOFF_FILENAME = "CODE_GTA6_COMMUNITY_BOT_ENGINE_IMPLEMENTATION_CONTEXT.md"


def algorithm_suite_status(repository: AlgorithmTestRepository, algorithm_name: str) -> dict[str, object]:
    try:
        definition = repository.get_definition_by_name(algorithm_name)
    except ValueError:
        return {
            "name": algorithm_name,
            "status": "missing",
            "total_cases": 0,
            "passed": 0,
            "failed": 0,
            "latest_run_status": "missing",
            "ready": False,
        }

    cases = repository.list_cases(str(definition["id"]))
    enabled_cases = [case for case in cases if case.get("enabled", True)]
    total_cases = len(enabled_cases)

    runs = [run for run in repository.list_runs(limit=30) if run.get("algorithm_id") == definition["id"]]
    latest_run = runs[0] if runs else None
    latest_run_status = str((latest_run or {}).get("status") or "never_run")
    passed = int((latest_run or {}).get("passed") or 0)
    failed = int((latest_run or {}).get("failed") or 0)

    ready = (
        bool(enabled_cases)
        and latest_run_status == "passed"
        and failed == 0
        and passed >= total_cases
    )

    if failed > 0:
        status = "has_failures"
    elif ready:
        status = "ready"
    else:
        status = "needs_tests"

    return {
        "name": algorithm_name,
        "status": status,
        "total_cases": total_cases,
        "passed": passed,
        "failed": failed,
        "latest_run_status": latest_run_status,
        "latest_run_id": str((latest_run or {}).get("id") or ""),
        "ready": ready,
    }


def community_pipeline_metrics(repository: AlgorithmTestRepository) -> dict[str, object]:
    suites = [algorithm_suite_status(repository, name) for name in COMMUNITY_ALGORITHMS]
    ready_count = sum(1 for suite in suites if suite["ready"])
    failed = sum(int(suite["failed"]) for suite in suites)
    passed = sum(int(suite["passed"]) for suite in suites)
    total = sum(int(suite["total_cases"]) for suite in suites)
    if failed > 0:
        status = "Has failures"
    elif ready_count == len(COMMUNITY_ALGORITHMS):
        status = "Ready"
    else:
        status = "Needs tests"
    return {
        "label": "Community Pipeline",
        "status": status,
        "total": total,
        "passed": passed,
        "failed": failed,
        "ready_count": ready_count,
        "required_algorithms": len(COMMUNITY_ALGORITHMS),
        "evidence_modes": {"seed_validation": passed},
        "suites": suites,
        "message": _pipeline_message(status, suites),
    }


def build_community_pipeline_context(repository: AlgorithmTestRepository) -> str:
    metrics = community_pipeline_metrics(repository)
    sections = [
        "# Contexto Técnico — Community Pipeline",
        "",
        "Pipeline: **Score de membro → Bot Engine → mini conteúdo → logs**",
        "",
        "## Readiness da pipeline",
        "",
        f"- Status geral: `{metrics['status']}`",
        f"- Algoritmos prontos: {metrics['ready_count']}/{metrics['required_algorithms']}",
        f"- Casos no último run: {metrics['passed']}/{metrics['total']} passed | failed: {metrics['failed']}",
        "",
        "## Suítes (último run)",
        "",
    ]
    for suite in metrics["suites"]:
        sections.append(
            f"- `{suite['name']}`: {suite['status']} | casos={suite['total_cases']} | "
            f"passed={suite['passed']} | failed={suite['failed']} | último run={suite['latest_run_status']}"
        )
    sections.extend(["", "## Algoritmo — member_engagement_score", ""])
    sections.append(build_algorithm_context(repository, algorithm_name="member_engagement_score"))
    sections.extend(["", "## Algoritmo — community_bot_engine", ""])
    sections.append(build_algorithm_context(repository, algorithm_name="community_bot_engine"))
    sections.extend(
        [
            "",
            "## Organização na comunidade",
            "",
            "- `member_engagement_score` define tier e elegibilidade (`bot_eligible`).",
            "- `community_bot_engine` consome `user.engagementScore` / `user.engagementTier` nas condições.",
            "- Eventos → score → regras → notificações/badges/créditos, sem IA no MVP.",
        ]
    )
    return "\n".join(sections)


def export_community_pipeline_handoff(repository: AlgorithmTestRepository, output_dir: str | Path) -> dict[str, str]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    metrics = community_pipeline_metrics(repository)
    context = build_community_pipeline_context(repository)
    bot_context = build_algorithm_context(repository, algorithm_name="community_bot_engine")

    pipeline_doc = "\n".join(
        [
            "# Code GTA6 Community — Community Pipeline Implementation Context",
            "",
            f"**Readiness:** `{metrics['status']}`",
            f"**Suítes validadas:** {metrics['ready_count']}/{metrics['required_algorithms']}",
            f"**Último run:** {metrics['passed']}/{metrics['total']} casos passed",
            "",
            "## Fluxo obrigatório",
            "",
            "```txt",
            "User Action → Event → member_engagement_score → community_bot_engine → mini conteúdo → logs",
            "```",
            "",
            "## Regras de implementação",
            "",
            "- Implementar somente comportamento validado neste pacote.",
            "- Reproduzir casos seed como testes unitários no projeto destino.",
            "- Não inventar payloads, regras ou endpoints fora da evidência.",
            "- `user.engagementScore` e `user.engagementTier` vêm do score antes do Bot Engine.",
            "",
            context,
        ]
    )
    bot_doc = "\n".join(
        [
            "# Code GTA6 Community — Community Bot Engine Implementation Context",
            "",
            "**Algoritmo:** `community_bot_engine`",
            "",
            bot_context,
        ]
    )

    pipeline_path = output_path / PIPELINE_HANDOFF_FILENAME
    bot_path = output_path / BOT_HANDOFF_FILENAME
    pipeline_path.write_text(pipeline_doc, encoding="utf-8")
    bot_path.write_text(bot_doc, encoding="utf-8")
    return {
        "pipeline": str(pipeline_path),
        "bot_engine": str(bot_path),
    }


def _pipeline_message(status: str, suites: list[dict[str, object]]) -> str:
    if status == "Ready":
        return "Community Pipeline validada: member_engagement_score + community_bot_engine prontos para handoff."
    if status == "Has failures":
        failed_names = [str(suite["name"]) for suite in suites if int(suite.get("failed") or 0) > 0]
        return f"Falhas na pipeline: {', '.join(failed_names)}. Corrija antes de implementar na comunidade."
    missing = [str(suite["name"]) for suite in suites if not suite.get("ready")]
    return f"Rode as suítes faltantes: {', '.join(missing)}."