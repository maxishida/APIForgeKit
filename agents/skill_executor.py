from __future__ import annotations

import hashlib
import json
import re
import shlex
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from core.acp_audit import build_acp_context
from core.algorithm_test_lab import AlgorithmTestRunner, build_algorithm_context, ensure_default_algorithms, summarize_algorithm_invariants
from core.api_test_lab import ApiTestRunner, build_api_context, ensure_default_api_suites
from core.context_builder import build_guided_context_bundle, export_guided_context_bundle
from core.observability import build_live_context
from core.report_bundle import create_report_bundle
from core.token_usage import TokenUsageRepository, build_token_usage_context, calculate_token_cost


VOICE_REQUIRED_EVENT_TYPES = (
    "lead_received",
    "user_message_received",
    "tts_audio_received",
    "transcript_received",
    "agent_response_received",
    "voice_call_completed",
)


@dataclass(frozen=True)
class SkillExecutorServices:
    algorithm_repository: object
    api_repository: object
    token_repository: TokenUsageRepository
    reports_dir: str | Path
    skill_path: str | Path = "SKILL.md"
    acp_repository: object | None = None
    observability_repository: object | None = None


class SkillExecutor:
    def __init__(self, services: SkillExecutorServices):
        self.services = services
        self.reports_dir = Path(services.reports_dir)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.skill_text = Path(services.skill_path).read_text(encoding="utf-8") if Path(services.skill_path).exists() else ""
        self.skill_contract = skill_contract_from_text(self.skill_text)
        self.last_context = ""
        self.last_evidence: dict[str, object] = {}

    def execute(self, prompt: str) -> dict[str, object]:
        tokens = shlex.split(prompt.strip())
        if not tokens:
            return self._not_validated()
        raw_command = tokens[0]
        command = _normalize_command(raw_command)
        args = tokens[1:]
        if command == "/validate-lead-score":
            return self._validate_lead_score()
        if command == "/validate-algorithm":
            return self._validate_algorithm(args)
        if command == "/validate-api-suite":
            return self._validate_api_suite(args)
        if command == "/validate-token-cost":
            return self._validate_token_cost(args)
        if command == "/token-cost":
            return self._token_cost(args)
        if command == "/validate-context-readiness":
            return self._validate_context_readiness(args)
        if command == "/validate-voice-roundtrip":
            return self._validate_voice_roundtrip(args)
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
        results = self.services.algorithm_repository.list_results(run_id=str(run["id"]), limit=int(run["total_cases"] or 100))
        invariants = summarize_algorithm_invariants(results)
        context = build_algorithm_context(self.services.algorithm_repository, algorithm_name=algorithm_name)
        context_path = self.reports_dir / f"{algorithm_name}_context.md"
        context_path.write_text(context, encoding="utf-8")
        self.last_context = context
        evidence = {
            "command": f"/validate-algorithm {algorithm_name}",
            "algorithm": algorithm_name,
            "run_id": run["id"],
            "passed": run["passed"],
            "failed": run["failed"],
            "total_cases": run["total_cases"],
            "invariants": invariants,
        }
        self.last_evidence = evidence
        return {
            "status": "success" if run["status"] == "passed" else "failed",
            "mode": "algorithm_validation",
            "permission_required": False,
            "run": run,
            "evidence": evidence,
            "exports": {"context": str(context_path)},
            "errors": [],
            "message": "Algorithm suite validated through SKILL.md gates.",
        }

    def _validate_lead_score(self) -> dict[str, object]:
        result = self._validate_algorithm(["lead_score"])
        if result.get("status") not in {"success", "failed"}:
            return result
        bundle = create_report_bundle(
            output_dir=self.reports_dir,
            name="lead_score_evidence_pack",
            markdown=self.last_context,
            payload={
                "generated_at": datetime.now(UTC).isoformat(),
                "source": "validate_lead_score",
                "evidence": result.get("evidence", {}),
                "run": result.get("run", {}),
            },
        )
        exports = dict(result.get("exports") or {})
        exports.update(bundle)
        evidence = dict(result.get("evidence") or {})
        evidence["command"] = "/validate-lead-score"
        self.last_evidence = evidence
        result["mode"] = "lead_score_validation"
        result["evidence"] = evidence
        result["exports"] = exports
        result["errors"] = []
        result["message"] = "Lead score suite validated and evidence pack exported."
        return result

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
        results = self.services.api_repository.list_results(run_id=str(run["id"]), limit=int(run["total_cases"] or 100))
        evidence_modes: dict[str, int] = {}
        for result in results:
            log = result.get("structured_log") or {}
            request = result.get("request") or {}
            mode = str(log.get("evidence_mode") or request.get("evidence_mode") or "dry_run_contract")
            evidence_modes[mode] = evidence_modes.get(mode, 0) + 1
        context = build_api_context(self.services.api_repository)
        context_path = self.reports_dir / f"{suite_name}_context.md"
        context_path.write_text(context, encoding="utf-8")
        self.last_context = context
        evidence = {
            "command": f"/validate-api-suite {suite_name}",
            "suite": suite_name,
            "provider": suite["provider"],
            "run_id": run["id"],
            "passed": run["passed"],
            "failed": run["failed"],
            "total_cases": run["total_cases"],
            "evidence_modes": evidence_modes,
        }
        self.last_evidence = evidence
        return {
            "status": "success" if run["status"] == "passed" else "failed",
            "mode": "generic_api_validation",
            "permission_required": False,
            "run": run,
            "evidence": evidence,
            "exports": {"context": str(context_path)},
            "errors": [],
            "message": "API suite validated in dry-run contract mode.",
        }

    def _token_cost(self, args: list[str]) -> dict[str, object]:
        values = _parse_key_values(args)
        should_save = _parse_bool(values.get("save") or values.get("persist"), default=False)
        try:
            estimate = calculate_token_cost(
                provider=str(values.get("provider", "xai")),
                model=str(values.get("model", "grok-4.3")),
                users=_int_arg(values, "users", default=1),
                requests_per_user_per_day=_int_arg(values, "requests", "requests_per_user_per_day", default=1),
                days=_int_arg(values, "days", default=30),
                input_tokens_per_request=_int_arg(values, "input", "input_tokens", default=1000),
                output_tokens_per_request=_int_arg(values, "output", "output_tokens", default=500),
                cached_input_tokens_per_request=_int_arg(values, "cached", "cached_input", default=0),
                pricing_mode=str(values.get("pricing_mode", "seeded_estimate")),
                pricing_verified_source_url=str(values.get("pricing_source", values.get("pricing_verified_source_url", ""))),
                pricing_input_per_million=_optional_float(values.get("input_price", values.get("pricing_input_per_million"))),
                pricing_output_per_million=_optional_float(values.get("output_price", values.get("pricing_output_per_million"))),
                pricing_cached_input_per_million=_optional_float(
                    values.get("cached_price", values.get("pricing_cached_input_per_million"))
                ),
            )
        except ValueError as exc:
            return self._invalid_token_cost_args(str(exc))
        saved = self.services.token_repository.save_estimate(estimate) if should_save else None
        context = build_token_usage_context(self.services.token_repository)
        self.last_context = context
        self.last_evidence = {
            "command": "/token-cost",
            "record_id": saved["id"] if saved else None,
            "provider": estimate["provider"],
            "model": estimate["model"],
            "pricing_mode": estimate["pricing_mode"],
            "saved": should_save,
        }
        return {
            "status": "success",
            "mode": "token_economy",
            "permission_required": False,
            "estimate": estimate,
            "record": saved,
            "evidence": self.last_evidence,
            "exports": {},
            "errors": [],
            "message": (
                "Token estimate saved. Verify official pricing docs before financial decisions."
                if should_save
                else "Token estimate calculated. Add save=true to persist it in PostgreSQL."
            ),
        }

    def _validate_token_cost(self, args: list[str]) -> dict[str, object]:
        result = self._token_cost(args)
        evidence = dict(result.get("evidence") or {})
        evidence["command"] = "/validate-token-cost"
        result["mode"] = "token_cost_validation"
        result["evidence"] = evidence
        self.last_evidence = evidence
        if result.get("status") == "success":
            result["message"] = "Token cost validation calculated through SKILL.md pricing gates."
        return result

    def _invalid_token_cost_args(self, reason: str) -> dict[str, object]:
        message = f"Invalid /token-cost arguments: {reason}. Ajuste provider/modelo/números e execute novamente."
        return {
            "status": "not_validated",
            "mode": "token_economy",
            "permission_required": False,
            "message": message,
            "evidence": {"command": "/token-cost"},
            "exports": {},
            "errors": [{"type": "invalid_token_cost_args", "message": reason}],
            "suggested_commands": [
                "/token-cost provider=xai model=grok-4.3 users=10 requests=20 input=1000 output=500 days=30",
                "/token-cost provider=xai model=grok-4.3 users=10 requests=20 save=true",
            ],
        }

    def _build_context(self) -> dict[str, object]:
        parts = [
            build_algorithm_context(self.services.algorithm_repository),
            build_api_context(self.services.api_repository),
            build_token_usage_context(self.services.token_repository),
        ]
        if self.services.acp_repository is not None:
            parts.append(build_acp_context(self.services.acp_repository))
        context = "\n\n---\n\n".join(part for part in parts if part)
        self.last_context = context
        path = self.reports_dir / f"acp_context_{_stamp()}.md"
        path.write_text(context, encoding="utf-8")
        self.last_evidence = {"command": "/build-context", "context_path": str(path)}
        return {
            "status": "success",
            "mode": "context_builder",
            "permission_required": False,
            "evidence": self.last_evidence,
            "exports": {"context": str(path)},
            "errors": [],
            "message": "Technical context generated from current evidence.",
        }

    def _validate_context_readiness(self, args: list[str]) -> dict[str, object]:
        values = _parse_key_values(args)
        source_mode = str(values.get("mode") or values.get("source_mode") or (args[0] if args and "=" not in args[0] else "algorithm_api"))
        live_runs = []
        live_events = []
        live_metrics: dict[str, object] = {}
        if self.services.observability_repository is not None:
            live_runs = self.services.observability_repository.list_runs(limit=50)
            live_events = self.services.observability_repository.list_events(limit=200)
            live_metrics = self.services.observability_repository.metrics()
        token_metrics = _token_metrics(self.services.token_repository)
        acp_context = ""
        acp_metrics: dict[str, object] = {}
        if self.services.acp_repository is not None:
            acp_context = build_acp_context(self.services.acp_repository)
            acp_metrics = self.services.acp_repository.metrics()
        bundle = build_guided_context_bundle(
            source_mode=source_mode,
            live_context=build_live_context(live_runs, live_events) if self.services.observability_repository is not None else "",
            algorithm_context=build_algorithm_context(self.services.algorithm_repository),
            api_context=build_api_context(self.services.api_repository),
            token_context=build_token_usage_context(self.services.token_repository),
            acp_context=acp_context,
            algorithm_metrics=self.services.algorithm_repository.metrics(),
            api_metrics=self.services.api_repository.metrics(),
            live_metrics=live_metrics,
            token_metrics=token_metrics,
            acp_metrics=acp_metrics,
        )
        exports = export_guided_context_bundle(self.reports_dir, bundle)
        self._record_observability_context_export(
            paths=exports,
            summary={
                "source": "acp_context_readiness",
                "source_mode": bundle["source_mode"],
                "readiness": bundle["readiness"]["overall"]["status"],
                "evidence_mode": "mixed",
                "generated_at": bundle["generated_at"],
                "paths": exports,
            },
        )
        readiness = dict(bundle["readiness"])
        overall = dict(readiness.get("overall") or {})
        readiness_status = str(overall.get("status") or "Needs tests")
        status = "success" if readiness_status == "Ready" else ("failed" if readiness_status == "Has failures" else "not_validated")
        evidence = {
            "command": "/validate-context-readiness",
            "source_mode": bundle["source_mode"],
            "readiness": readiness_status,
            "required_sections": overall.get("required_sections", []),
        }
        self.last_context = str(bundle.get("context") or "")
        self.last_evidence = evidence
        return {
            "status": status,
            "mode": "context_readiness",
            "permission_required": False,
            "readiness": readiness,
            "evidence": evidence,
            "exports": exports,
            "errors": [] if status != "failed" else [{"type": "context_readiness_failure", "message": str(overall.get("message") or "")}],
            "message": str(overall.get("message") or "Context readiness calculated."),
        }

    def _record_observability_context_export(self, *, paths: dict[str, str], summary: dict[str, object]) -> None:
        if self.services.observability_repository is None:
            return
        runs = self.services.observability_repository.list_runs(limit=1)
        if not runs:
            return
        self.services.observability_repository.record_context_export(
            str(runs[0]["id"]),
            "multi",
            json.dumps(paths, ensure_ascii=False),
            summary,
        )

    def _validate_voice_roundtrip(self, args: list[str]) -> dict[str, object]:
        options = set(args)
        if "--run-real" in options or "--http-real" in options:
            return self._permission_required(
                kind="network",
                reason="xAI Voice real usa API paga/externa e exige permissão antes de executar.",
                command="/validate-voice-roundtrip --run-real",
            )
        if self.services.observability_repository is None:
            return self._voice_not_validated("Observability repository is not configured for this ACP executor.")
        runs = self.services.observability_repository.list_runs(limit=1, provider="xai", suite_name="voice_roundtrip")
        if not runs:
            return self._voice_not_validated("Nenhum roundtrip de voz foi encontrado no PostgreSQL.")
        latest_run = runs[0]
        events = self.services.observability_repository.list_events(run_id=str(latest_run["id"]), limit=100)
        success_events = [event for event in events if event.get("status") == "success"]
        failed_events = [event for event in events if event.get("status") in {"failed", "blocked"}]
        event_types = {str(event.get("event_type") or "") for event in events}
        missing_event_types = [event_type for event_type in VOICE_REQUIRED_EVENT_TYPES if event_type not in event_types]
        status = "success" if latest_run.get("status") == "success" and not failed_events and not missing_event_types else "failed"
        evidence = {
            "command": "/validate-voice-roundtrip",
            "latest_run": latest_run,
            "event_count": len(events),
            "success_events": len(success_events),
            "failed_events": len(failed_events),
            "missing_event_types": missing_event_types,
            "voice_status": latest_run.get("status"),
            "evidence_modes": _event_evidence_modes(events),
        }
        context = build_live_context([latest_run], events)
        context_path = self.reports_dir / f"voice_roundtrip_context_{_stamp()}.md"
        context_path.write_text(context, encoding="utf-8")
        self.last_context = context
        self.last_evidence = evidence
        return {
            "status": status,
            "mode": "voice_roundtrip_validation",
            "permission_required": False,
            "run": latest_run,
            "evidence": evidence,
            "exports": {"context": str(context_path)},
            "errors": [
                *[
                    {"type": "voice_roundtrip_failure", "message": str(event.get("error") or event.get("message") or "")}
                    for event in failed_events
                ],
                *[
                    {"type": "voice_roundtrip_missing_events", "message": f"Missing required event type: {event_type}"}
                    for event_type in missing_event_types
                ],
            ],
            "message": "Voice roundtrip evidence validated from PostgreSQL.",
        }

    def _voice_not_validated(self, reason: str) -> dict[str, object]:
        return {
            "status": "not_validated",
            "mode": "voice_roundtrip_validation",
            "permission_required": False,
            "message": f"{reason} Rode `npm run voice:run` ou use `/voice-lab` com XAI_API_KEY antes de validar via ACP.",
            "evidence": {"command": "/validate-voice-roundtrip", "latest_run": None},
            "exports": {},
            "errors": [{"type": "voice_roundtrip_missing", "message": reason}],
            "suggested_commands": ["npm run voice:run", "/validate-voice-roundtrip"],
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
            payload={
                "generated_at": datetime.now(UTC).isoformat(),
                "source": "acp_skill_executor",
                "evidence": self.last_evidence,
                "summary": {"context_chars": len(self.last_context)},
            },
        )
        evidence = {
            "command": str(self.last_evidence.get("command") or "/export-evidence"),
            "algorithm": self.last_evidence.get("algorithm"),
            "run_id": self.last_evidence.get("run_id"),
            "summary": {"context_chars": len(self.last_context)},
        }
        return {
            "status": "success",
            "mode": "evidence_export",
            "permission_required": False,
            "evidence": evidence,
            "exports": bundle,
            "errors": [],
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
            "evidence": {},
            "exports": {},
            "errors": [{"type": "not_validated", "message": reason}] if reason else [],
            "suggested_commands": [
                "/validate-lead-score",
                "/validate-algorithm lead_score",
                "/validate-api-suite whatsapp_validation_pack",
                "/validate-token-cost provider=xai model=grok-4.3 users=10 requests=20",
                "/token-cost provider=xai model=grok-4.3 users=10 requests=20",
                "/validate-context-readiness",
                "/validate-voice-roundtrip",
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
            "evidence": {},
            "exports": {},
            "errors": [{"type": "permission_required", "message": reason}],
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


def _normalize_command(command: str) -> str:
    command = command.strip()
    return command if command.startswith("/") else f"/{command}"


def _stamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


def _optional_float(value: str | None) -> float | None:
    if value in {None, ""}:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _parse_bool(value: str | None, *, default: bool = False) -> bool:
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def _int_arg(values: dict[str, str], *names: str, default: int) -> int:
    for name in names:
        if name in values:
            raw = values[name]
            try:
                return int(raw)
            except (TypeError, ValueError) as exc:
                raise ValueError(f"{name} must be an integer, got {raw!r}") from exc
    return default


def _token_metrics(repository: TokenUsageRepository) -> dict[str, object]:
    estimates = repository.list_estimates(limit=10000)
    evidence_modes: dict[str, int] = {}
    for estimate in estimates:
        summary = estimate.get("summary") or {}
        mode = str(summary.get("pricing_mode") or "seeded_estimate")
        evidence_modes[mode] = evidence_modes.get(mode, 0) + 1
    return {"total_estimates": len(estimates), "evidence_modes": evidence_modes}


def _event_evidence_modes(events: list[dict[str, object]]) -> dict[str, int]:
    evidence_modes: dict[str, int] = {}
    for event in events:
        mode = str(event.get("evidence_mode") or "real_http")
        evidence_modes[mode] = evidence_modes.get(mode, 0) + 1
    return evidence_modes


def load_skill_contract(skill_path: str | Path) -> dict[str, str]:
    path = Path(skill_path)
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    return skill_contract_from_text(text)


def skill_contract_from_text(skill_text: str) -> dict[str, str]:
    match = re.search(r"^version:\s*([^\r\n]+)$", skill_text, flags=re.MULTILINE)
    return {
        "version": match.group(1).strip() if match else "unknown",
        "sha256": hashlib.sha256(skill_text.encode("utf-8")).hexdigest(),
    }
