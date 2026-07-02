from __future__ import annotations

from core.algorithm_test_lab import AlgorithmTestRepository, build_algorithm_context

COMMUNITY_ALGORITHMS = ("community_bot_engine", "member_engagement_score")


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

    results = repository.list_results(algorithm_id=str(definition["id"]), limit=200)
    passed = sum(1 for item in results if item["status"] == "passed")
    failed = sum(1 for item in results if item["status"] == "failed")
    runs = [run for run in repository.list_runs(limit=30) if run.get("algorithm_id") == definition["id"]]
    latest_run = runs[0] if runs else None
    latest_run_status = str((latest_run or {}).get("status") or "never_run")
    cases = repository.list_cases(str(definition["id"]))
    enabled_cases = [case for case in cases if case.get("enabled", True)]
    ready = bool(enabled_cases) and failed == 0 and passed >= len(enabled_cases) and latest_run_status == "passed"

    return {
        "name": algorithm_name,
        "status": "ready" if ready else "needs_tests" if failed == 0 else "has_failures",
        "total_cases": len(enabled_cases),
        "passed": passed,
        "failed": failed,
        "latest_run_status": latest_run_status,
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
        f"- Casos passed: {metrics['passed']} | failed: {metrics['failed']}",
        "",
        "## Suítes",
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


def _pipeline_message(status: str, suites: list[dict[str, object]]) -> str:
    if status == "Ready":
        return "Community Pipeline validada: member_engagement_score + community_bot_engine prontos para handoff."
    if status == "Has failures":
        failed_names = [str(suite["name"]) for suite in suites if int(suite.get("failed") or 0) > 0]
        return f"Falhas na pipeline: {', '.join(failed_names)}. Corrija antes de implementar na comunidade."
    missing = [str(suite["name"]) for suite in suites if not suite.get("ready")]
    return f"Rode as suítes faltantes: {', '.join(missing)}."