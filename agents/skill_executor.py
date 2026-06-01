from __future__ import annotations

import shlex
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from core.algorithm_test_lab import AlgorithmTestRunner, build_algorithm_context, ensure_default_algorithms
from core.api_test_lab import ApiTestRunner, build_api_context, ensure_default_api_suites
from core.report_bundle import create_report_bundle
from core.token_usage import TokenUsageRepository, build_token_usage_context, calculate_token_cost


@dataclass(frozen=True)
class SkillExecutorServices:
    algorithm_repository: object
    api_repository: object
    token_repository: TokenUsageRepository
    reports_dir: str | Path
    skill_path: str | Path = "SKILL.md"


class SkillExecutor:
    def __init__(self, services: SkillExecutorServices):
        self.services = services
        self.reports_dir = Path(services.reports_dir)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.skill_text = Path(services.skill_path).read_text(encoding="utf-8") if Path(services.skill_path).exists() else ""
        self.last_context = ""

    def execute(self, prompt: str) -> dict[str, object]:
        tokens = shlex.split(prompt.strip())
        if not tokens:
            return self._not_validated()
        command = tokens[0]
        args = tokens[1:]
        if command == "/validate-algorithm":
            return self._validate_algorithm(args)
        if command == "/validate-api-suite":
            return self._validate_api_suite(args)
        if command == "/token-cost":
            return self._token_cost(args)
        if command == "/build-context":
            return self._build_context()
        if command == "/export-evidence":
            return self._export_evidence()
        return self._not_validated()

    def _validate_algorithm(self, args: list[str]) -> dict[str, object]:
        algorithm_name = args[0] if args else "lead_score"
        ensure_default_algorithms(self.services.algorithm_repository)
        try:
            definition = self.services.algorithm_repository.get_definition_by_name(algorithm_name)
        except ValueError as exc:
            return self._not_validated(str(exc))
        run = AlgorithmTestRunner(self.services.algorithm_repository).run_suite(str(definition["id"]))
        context = build_algorithm_context(self.services.algorithm_repository)
        context_path = self.reports_dir / f"{algorithm_name}_context.md"
        context_path.write_text(context, encoding="utf-8")
        self.last_context = context
        return {
            "status": "success" if run["status"] == "passed" else "failed",
            "mode": "algorithm_validation",
            "permission_required": False,
            "run": run,
            "evidence": {
                "algorithm": algorithm_name,
                "passed": run["passed"],
                "failed": run["failed"],
                "total_cases": run["total_cases"],
            },
            "exports": {"context": str(context_path)},
            "message": "Algorithm suite validated through SKILL.md gates.",
        }

    def _validate_api_suite(self, args: list[str]) -> dict[str, object]:
        suite_name = args[0] if args else "whatsapp_validation_pack"
        options = set(args[1:])
        if "--http-real" in options:
            return self._permission_required(
                kind="network",
                reason="HTTP real ou provider pago exige permissão antes de executar.",
                command=f"/validate-api-suite {suite_name}",
            )
        ensure_default_api_suites(self.services.api_repository)
        try:
            suite = self.services.api_repository.get_suite_by_name(suite_name)
        except ValueError as exc:
            return self._not_validated(str(exc))
        cases = self.services.api_repository.list_cases(str(suite["id"]))
        if any(not case.get("dry_run", True) for case in cases):
            return self._permission_required(
                kind="network",
                reason="HTTP real ou provider pago exige permissão antes de executar.",
                command=f"/validate-api-suite {suite_name}",
            )
        run = ApiTestRunner(self.services.api_repository).run_suite(str(suite["id"]))
        context = build_api_context(self.services.api_repository)
        context_path = self.reports_dir / f"{suite_name}_context.md"
        context_path.write_text(context, encoding="utf-8")
        self.last_context = context
        return {
            "status": "success" if run["status"] == "passed" else "failed",
            "mode": "generic_api_validation",
            "permission_required": False,
            "run": run,
            "evidence": {
                "suite": suite_name,
                "provider": suite["provider"],
                "passed": run["passed"],
                "failed": run["failed"],
                "total_cases": run["total_cases"],
            },
            "exports": {"context": str(context_path)},
            "message": "API suite validated in dry-run contract mode.",
        }

    def _token_cost(self, args: list[str]) -> dict[str, object]:
        values = _parse_key_values(args)
        estimate = calculate_token_cost(
            provider=str(values.get("provider", "xai")),
            model=str(values.get("model", "grok-4.3")),
            users=int(values.get("users", 1)),
            requests_per_user_per_day=int(values.get("requests", values.get("requests_per_user_per_day", 1))),
            days=int(values.get("days", 30)),
            input_tokens_per_request=int(values.get("input", values.get("input_tokens", 1000))),
            output_tokens_per_request=int(values.get("output", values.get("output_tokens", 500))),
            cached_input_tokens_per_request=int(values.get("cached", values.get("cached_input", 0))),
        )
        saved = self.services.token_repository.save_estimate(estimate)
        context = build_token_usage_context(self.services.token_repository)
        self.last_context = context
        return {
            "status": "success",
            "mode": "token_economy",
            "permission_required": False,
            "estimate": estimate,
            "record": saved,
            "message": "Token estimate created. Verify official pricing docs before financial decisions.",
        }

    def _build_context(self) -> dict[str, object]:
        parts = [
            build_algorithm_context(self.services.algorithm_repository),
            build_api_context(self.services.api_repository),
            build_token_usage_context(self.services.token_repository),
        ]
        context = "\n\n---\n\n".join(part for part in parts if part)
        self.last_context = context
        path = self.reports_dir / f"acp_context_{_stamp()}.md"
        path.write_text(context, encoding="utf-8")
        return {
            "status": "success",
            "mode": "context_builder",
            "permission_required": False,
            "exports": {"context": str(path)},
            "message": "Technical context generated from current evidence.",
        }

    def _export_evidence(self) -> dict[str, object]:
        context = self.last_context or str(self._build_context().get("message", ""))
        if not self.last_context:
            context = build_algorithm_context(self.services.algorithm_repository)
            self.last_context = context
        bundle = create_report_bundle(
            output_dir=self.reports_dir,
            name="acp_evidence_bundle",
            markdown=self.last_context,
            payload={"generated_at": datetime.now(UTC).isoformat(), "source": "acp_skill_executor"},
        )
        return {
            "status": "success",
            "mode": "evidence_export",
            "permission_required": False,
            "exports": bundle,
            "message": "Evidence bundle exported.",
        }

    def _not_validated(self, reason: str | None = None) -> dict[str, object]:
        message = "Ainda não validado pelo APIForgeKit. Próximo passo: executar teste/log/contexto antes de implementar."
        if reason:
            message = f"{reason}. {message}"
        return {
            "status": "not_validated",
            "mode": "unknown",
            "permission_required": False,
            "message": message,
            "suggested_commands": [
                "/validate-algorithm lead_score",
                "/validate-api-suite whatsapp_validation_pack",
                "/token-cost provider=xai model=grok-4.3 users=10 requests=20",
                "/build-context",
                "/export-evidence",
            ],
        }

    def _permission_required(self, *, kind: str, reason: str, command: str) -> dict[str, object]:
        return {
            "status": "permission_required",
            "mode": "permission_gate",
            "permission_required": True,
            "permission": {"kind": kind, "reason": reason, "command": command},
            "message": reason,
        }


def _parse_key_values(args: list[str]) -> dict[str, str]:
    values: dict[str, str] = {}
    for item in args:
        if "=" not in item:
            continue
        key, value = item.split("=", 1)
        values[key.strip().replace("-", "_")] = value.strip()
    return values


def _stamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
