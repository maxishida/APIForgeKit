from __future__ import annotations

import json
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from uuid import uuid4

from sqlalchemy import desc, select
from sqlalchemy.orm import Session, sessionmaker

from core.models import ApiTestCase, ApiTestResult, ApiTestRun, ApiTestSuite


SECRET_HEADER_NAMES = {"authorization", "x-api-key", "api-key", "cookie", "set-cookie"}


DEFAULT_WHATSAPP_CASES = [
    {
        "name": "valid outbound text payload",
        "method": "POST",
        "url": "dry-run://whatsapp/messages",
        "headers": {"Authorization": "Bearer {{WHATSAPP_TOKEN}}", "Content-Type": "application/json"},
        "body": {
            "messaging_product": "whatsapp",
            "to": "5511999999999",
            "type": "text",
            "text": {"body": "Olá, podemos falar agora?"},
        },
        "expected": {"status_code": 200, "json_contains": {"ok": True, "channel": "whatsapp", "contract": "outbound_message"}},
        "dry_run": True,
        "mock_response": {
            "status_code": 200,
            "json": {"ok": True, "channel": "whatsapp", "contract": "outbound_message"},
            "text": '{"ok": true, "channel": "whatsapp", "contract": "outbound_message"}',
        },
        "tags": ["whatsapp", "outbound", "contract"],
    },
    {
        "name": "lead intent webhook payload",
        "method": "POST",
        "url": "dry-run://whatsapp/webhook",
        "headers": {"Content-Type": "application/json"},
        "body": {
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "messages": [
                                    {
                                        "from": "5511888888888",
                                        "text": {"body": "Quero preço e orçamento hoje"},
                                        "type": "text",
                                    }
                                ]
                            }
                        }
                    ]
                }
            ]
        },
        "expected": {"status_code": 200, "json_contains": {"ok": True, "lead_intent": "high"}},
        "dry_run": True,
        "mock_response": {"status_code": 200, "json": {"ok": True, "lead_intent": "high"}, "text": '{"ok": true, "lead_intent": "high"}'},
        "tags": ["whatsapp", "webhook", "lead"],
    },
    {
        "name": "missing phone should fail contract",
        "method": "POST",
        "url": "dry-run://whatsapp/messages",
        "headers": {"Content-Type": "application/json"},
        "body": {"messaging_product": "whatsapp", "type": "text", "text": {"body": "Oi"}},
        "expected": {"status_code": 400, "json_contains": {"ok": False, "error_code": "missing_phone"}},
        "dry_run": True,
        "mock_response": {
            "status_code": 400,
            "json": {"ok": False, "error_code": "missing_phone"},
            "text": '{"ok": false, "error_code": "missing_phone"}',
        },
        "tags": ["whatsapp", "negative", "contract"],
    },
    {
        "name": "spam-like payload should be classified",
        "method": "POST",
        "url": "dry-run://whatsapp/webhook",
        "headers": {"Content-Type": "application/json"},
        "body": {"from": "5511777777777", "message": "clique aqui e ganhe dinheiro agora"},
        "expected": {"status_code": 200, "json_contains": {"ok": True, "classification": "spam_risk"}},
        "dry_run": True,
        "mock_response": {
            "status_code": 200,
            "json": {"ok": True, "classification": "spam_risk"},
            "text": '{"ok": true, "classification": "spam_risk"}',
        },
        "tags": ["whatsapp", "spam", "edge"],
    },
]


class ApiTestRepository:
    def __init__(self, session_factory: sessionmaker[Session]):
        self.session_factory = session_factory

    def create_suite(
        self,
        *,
        name: str,
        provider: str,
        description: str,
        docs_url: str = "",
        tags: list[str] | None = None,
    ) -> dict[str, object]:
        with self.session_factory() as session:
            row = ApiTestSuite(
                id=str(uuid4()),
                name=name,
                provider=provider,
                description=description,
                docs_url=docs_url,
                tags=tags or [],
            )
            session.add(row)
            session.commit()
            session.refresh(row)
            return row.to_dict()

    def get_suite(self, suite_id: str) -> dict[str, object]:
        with self.session_factory() as session:
            row = session.get(ApiTestSuite, suite_id)
            if row is None:
                raise ValueError(f"Unknown suite_id: {suite_id}")
            return row.to_dict()

    def get_suite_by_name(self, name: str) -> dict[str, object]:
        with self.session_factory() as session:
            row = session.scalar(select(ApiTestSuite).where(ApiTestSuite.name == name))
            if row is None:
                raise ValueError(f"Unknown suite: {name}")
            return row.to_dict()

    def list_suites(self) -> list[dict[str, object]]:
        with self.session_factory() as session:
            rows = session.scalars(select(ApiTestSuite).order_by(ApiTestSuite.name)).all()
            return [row.to_dict() for row in rows]

    def create_case(
        self,
        *,
        suite_id: str,
        name: str,
        method: str,
        url: str,
        headers: dict[str, object],
        body: dict[str, object],
        expected: dict[str, object],
        dry_run: bool = True,
        mock_response: dict[str, object] | None = None,
        timeout_seconds: int = 20,
        tags: list[str] | None = None,
        enabled: bool = True,
    ) -> dict[str, object]:
        with self.session_factory() as session:
            row = ApiTestCase(
                id=str(uuid4()),
                suite_id=suite_id,
                name=name,
                method=method.upper(),
                url=url,
                headers=headers,
                body=body,
                expected=expected,
                dry_run=dry_run,
                mock_response=mock_response or {},
                timeout_seconds=timeout_seconds,
                tags=tags or [],
                enabled=enabled,
            )
            session.add(row)
            session.commit()
            session.refresh(row)
            return row.to_dict()

    def get_case(self, case_id: str) -> dict[str, object]:
        with self.session_factory() as session:
            row = session.get(ApiTestCase, case_id)
            if row is None:
                raise ValueError(f"Unknown case_id: {case_id}")
            return row.to_dict()

    def list_cases(self, suite_id: str | None = None) -> list[dict[str, object]]:
        with self.session_factory() as session:
            statement = select(ApiTestCase).order_by(ApiTestCase.created_at)
            if suite_id:
                statement = statement.where(ApiTestCase.suite_id == suite_id)
            rows = session.scalars(statement).all()
            return [row.to_dict() for row in rows]

    def start_run(self, suite_id: str, total_cases: int) -> dict[str, object]:
        with self.session_factory() as session:
            row = ApiTestRun(id=str(uuid4()), suite_id=suite_id, total_cases=total_cases, status="running")
            session.add(row)
            session.commit()
            session.refresh(row)
            return row.to_dict()

    def finish_run(self, run_id: str, *, passed: int, failed: int, summary: dict[str, object] | None = None) -> dict[str, object]:
        with self.session_factory() as session:
            row = session.get(ApiTestRun, run_id)
            if row is None:
                raise ValueError(f"Unknown run_id: {run_id}")
            row.completed_at = datetime.now(UTC)
            row.passed = passed
            row.failed = failed
            row.status = "passed" if failed == 0 else "failed"
            row.summary = summary or {}
            session.commit()
            session.refresh(row)
            return row.to_dict()

    def record_result(
        self,
        *,
        run_id: str,
        suite_id: str,
        case_id: str,
        status: str,
        request: dict[str, object],
        response: dict[str, object],
        diff: dict[str, object],
        latency_ms: float,
        structured_log: dict[str, object],
        error: str | None,
        recommendation: str,
    ) -> dict[str, object]:
        with self.session_factory() as session:
            row = ApiTestResult(
                id=str(uuid4()),
                run_id=run_id,
                suite_id=suite_id,
                case_id=case_id,
                status=status,
                request=request,
                response=response,
                diff=diff,
                latency_ms=latency_ms,
                structured_log=structured_log,
                error=error,
                recommendation=recommendation,
            )
            session.add(row)
            session.commit()
            session.refresh(row)
            return row.to_dict()

    def list_runs(self, limit: int = 50) -> list[dict[str, object]]:
        with self.session_factory() as session:
            rows = session.scalars(select(ApiTestRun).order_by(desc(ApiTestRun.created_at)).limit(limit)).all()
            return [row.to_dict() for row in rows]

    def list_results(self, *, run_id: str | None = None, limit: int = 100) -> list[dict[str, object]]:
        with self.session_factory() as session:
            statement = select(ApiTestResult).order_by(desc(ApiTestResult.created_at)).limit(limit)
            if run_id:
                statement = (
                    select(ApiTestResult)
                    .where(ApiTestResult.run_id == run_id)
                    .order_by(desc(ApiTestResult.created_at))
                    .limit(limit)
                )
            rows = session.scalars(statement).all()
            return [row.to_dict() for row in rows]

    def metrics(self) -> dict[str, object]:
        runs = self.list_runs(limit=10000)
        results = self.list_results(limit=10000)
        passed = len([result for result in results if result["status"] == "passed"])
        failed = len([result for result in results if result["status"] == "failed"])
        latencies = [float(result["latency_ms"] or 0) for result in results]
        evidence_modes: dict[str, int] = {}
        for result in results:
            mode = _result_evidence_mode(result)
            evidence_modes[mode] = evidence_modes.get(mode, 0) + 1
        return {
            "total_runs": len(runs),
            "total_results": len(results),
            "passed": passed,
            "failed": failed,
            "pass_rate": round((passed / len(results)) * 100, 2) if results else 0,
            "average_latency_ms": round(sum(latencies) / len(latencies), 2) if latencies else 0,
            "evidence_modes": evidence_modes,
        }


class ApiTestRunner:
    def __init__(self, repository: ApiTestRepository):
        self.repository = repository

    def run_single_case(self, case_id: str) -> dict[str, object]:
        case = self.repository.get_case(case_id)
        run = self.repository.start_run(str(case["suite_id"]), 1)
        result = self._execute_case(run["id"], case)
        return self.repository.finish_run(
            run["id"],
            passed=1 if result["status"] == "passed" else 0,
            failed=0 if result["status"] == "passed" else 1,
            summary={"case": case["name"]},
        )

    def run_suite(self, suite_id: str) -> dict[str, object]:
        cases = [case for case in self.repository.list_cases(suite_id) if case.get("enabled")]
        run = self.repository.start_run(suite_id, len(cases))
        passed = 0
        failed = 0
        for case in cases:
            result = self._execute_case(run["id"], case)
            if result["status"] == "passed":
                passed += 1
            else:
                failed += 1
        return self.repository.finish_run(run["id"], passed=passed, failed=failed, summary={"total_cases": len(cases)})

    def _execute_case(self, run_id: str, case: dict[str, object]) -> dict[str, object]:
        suite = self.repository.get_suite(str(case["suite_id"]))
        evidence_mode = _evidence_mode_for_case(case)
        request_payload = {
            "method": case["method"],
            "url": case["url"],
            "headers": redact_headers(dict(case["headers"])),
            "body": case["body"],
            "dry_run": case["dry_run"],
            "evidence_mode": evidence_mode,
        }
        started = perf_counter()
        error = None
        try:
            response_payload = execute_api_case(case)
        except Exception as exc:  # noqa: BLE001 - captured as structured evidence
            response_payload = {"status_code": 0, "json": {}, "text": ""}
            error = str(exc)
        response_payload["evidence_mode"] = evidence_mode
        latency = round((perf_counter() - started) * 1000, 2)
        diff = validate_api_response(dict(case["expected"]), response_payload)
        status = "passed" if diff["passed"] and error is None else "failed"
        recommendation = _api_recommendation(status, diff, error)
        structured_log = {
            "event_id": str(uuid4()),
            "timestamp": datetime.now(UTC).isoformat(),
            "provider": suite["provider"],
            "module": "generic_api_test_lab",
            "test_name": case["name"],
            "status": status,
            "evidence_mode": evidence_mode,
            "latency_ms": latency,
            "tokens": {},
            "cost": 0,
            "request": request_payload,
            "response": response_payload,
            "error": error,
            "recommendation": recommendation,
        }
        return self.repository.record_result(
            run_id=run_id,
            suite_id=str(case["suite_id"]),
            case_id=str(case["id"]),
            status=status,
            request=request_payload,
            response=response_payload,
            diff=diff,
            latency_ms=latency,
            structured_log=structured_log,
            error=error if status == "failed" else None,
            recommendation=recommendation,
        )


def ensure_default_api_suites(repository: ApiTestRepository) -> None:
    try:
        suite = repository.get_suite_by_name("whatsapp_validation_pack")
    except ValueError:
        suite = repository.create_suite(
            name="whatsapp_validation_pack",
            provider="whatsapp",
            description="Dry-run contract pack for WhatsApp payloads, webhook events and lead intent validation.",
            docs_url="https://developers.facebook.com/docs/whatsapp",
            tags=["whatsapp", "contract", "seed"],
        )
    existing = {case["name"] for case in repository.list_cases(str(suite["id"]))}
    for case in DEFAULT_WHATSAPP_CASES:
        if case["name"] not in existing:
            repository.create_case(suite_id=str(suite["id"]), **case)


def execute_api_case(case: dict[str, object]) -> dict[str, object]:
    if bool(case.get("dry_run", True)):
        return normalize_response(dict(case.get("mock_response") or {}))

    data = json.dumps(case.get("body") or {}).encode("utf-8")
    headers = {str(key): str(value) for key, value in dict(case.get("headers") or {}).items()}
    request = urllib.request.Request(
        str(case["url"]),
        data=data if str(case.get("method", "GET")).upper() != "GET" else None,
        headers=headers,
        method=str(case.get("method", "GET")).upper(),
    )
    try:
        with urllib.request.urlopen(request, timeout=int(case.get("timeout_seconds") or 20)) as response:  # noqa: S310 - user-provided local harness
            text = response.read().decode("utf-8", errors="replace")
            return normalize_response({"status_code": response.status, "text": text})
    except urllib.error.HTTPError as exc:
        text = exc.read().decode("utf-8", errors="replace")
        return normalize_response({"status_code": exc.code, "text": text})


def normalize_response(response: dict[str, object]) -> dict[str, object]:
    text = str(response.get("text") or "")
    json_payload = response.get("json")
    if json_payload is None and text:
        try:
            json_payload = json.loads(text)
        except json.JSONDecodeError:
            json_payload = {}
    if not text and json_payload is not None:
        text = json.dumps(json_payload, ensure_ascii=False)
    return {
        "status_code": int(response.get("status_code") or 0),
        "json": json_payload or {},
        "text": text,
        "headers": response.get("headers") or {},
    }


def validate_api_response(expected: dict[str, object], actual: dict[str, object]) -> dict[str, object]:
    mismatches: list[dict[str, object]] = []
    expected_status = expected.get("status_code")
    if expected_status is not None and int(actual.get("status_code") or 0) != int(expected_status):
        mismatches.append({"field": "status_code", "expected": expected_status, "actual": actual.get("status_code")})

    contains = expected.get("json_contains")
    if isinstance(contains, dict):
        mismatches.extend(_json_contains_mismatches(contains, dict(actual.get("json") or {})))

    body_contains = expected.get("body_contains")
    if body_contains and str(body_contains) not in str(actual.get("text") or ""):
        mismatches.append({"field": "body", "expected": f"contains {body_contains}", "actual": actual.get("text")})

    return {"passed": not mismatches, "mismatches": mismatches}


def export_api_suite(repository: ApiTestRepository, suite_id: str, output_dir: str | Path) -> str:
    suite = repository.get_suite(suite_id)
    cases = repository.list_cases(suite_id)
    payload = {"api_test_suites": [suite], "api_test_cases": cases}
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{suite['name']}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(path)


def import_api_suite(repository: ApiTestRepository, path: str | Path) -> dict[str, object]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return import_api_suite_payload(repository, payload)


def import_api_suite_payload(repository: ApiTestRepository, payload: dict[str, object]) -> dict[str, object]:
    source_suite = payload["api_test_suites"][0]
    try:
        suite = repository.get_suite_by_name(str(source_suite["name"]))
    except ValueError:
        suite = repository.create_suite(
            name=str(source_suite["name"]),
            provider=str(source_suite["provider"]),
            description=str(source_suite.get("description") or ""),
            docs_url=str(source_suite.get("docs_url") or ""),
            tags=list(source_suite.get("tags") or []),
        )
    existing = {case["name"] for case in repository.list_cases(str(suite["id"]))}
    for case in payload.get("api_test_cases", []):
        if case["name"] in existing:
            continue
        repository.create_case(
            suite_id=str(suite["id"]),
            name=str(case["name"]),
            method=str(case["method"]),
            url=str(case["url"]),
            headers=dict(case.get("headers") or {}),
            body=dict(case.get("body") or {}),
            expected=dict(case.get("expected") or {}),
            dry_run=bool(case.get("dry_run", True)),
            mock_response=dict(case.get("mock_response") or {}),
            timeout_seconds=int(case.get("timeout_seconds") or 20),
            tags=list(case.get("tags") or []),
            enabled=bool(case.get("enabled", True)),
        )
    return suite


def build_api_context(repository: ApiTestRepository, limit: int = 100) -> str:
    suites = repository.list_suites()
    results = repository.list_results(limit=limit)
    runs = repository.list_runs(limit=20)
    passed = [result for result in results if result["status"] == "passed"]
    failed = [result for result in results if result["status"] == "failed"]
    evidence_modes: dict[str, int] = {}
    for result in results:
        mode = _result_evidence_mode(result)
        evidence_modes[mode] = evidence_modes.get(mode, 0) + 1
    payload_lines = []
    for result in results[:20]:
        log = result.get("structured_log") or {}
        payload_lines.append(
            f"- `{log.get('test_name', result.get('case_id'))}` status={result.get('status')} "
            f"mode={_result_evidence_mode(result)} http={result.get('response', {}).get('status_code')} "
            f"request={json.dumps(result.get('request', {}).get('body', {}), ensure_ascii=False)}"
        )

    return f"""# Contexto Técnico - Generic API Test Lab

## Suites

{_render_suite_lines(suites)}

## O que foi validado

- Runs analisadas: {len(runs)}
- Resultados analisados: {len(results)}
- Passaram: {len(passed)}
- Falharam: {len(failed)}
- Modos de evidência: {_render_evidence_modes(evidence_modes)}

## Payloads validados

{chr(10).join(payload_lines) if payload_lines else "- Nenhum payload validado ainda."}

## Falhas e diffs

{_render_failed_api_lines(failed)}

## Recomendações

- Use dry-run para validar contrato antes de gastar requests reais.
- Use HTTP real apenas quando autenticação, limites e payload estiverem claros.
- Transforme payloads aprovados em contexto técnico compacto para IA.
- Para WhatsApp, valide shape do webhook, telefone, tipo de mensagem e classificação de intenção antes da implementação.
"""


def redact_headers(headers: dict[str, object]) -> dict[str, object]:
    redacted = {}
    for key, value in headers.items():
        redacted[key] = "***REDACTED***" if str(key).lower() in SECRET_HEADER_NAMES else value
    return redacted


def _evidence_mode_for_case(case: dict[str, object]) -> str:
    return "dry_run_contract" if bool(case.get("dry_run", True)) else "real_http"


def _result_evidence_mode(result: dict[str, object]) -> str:
    structured_log = result.get("structured_log") or {}
    request = result.get("request") or {}
    return str(structured_log.get("evidence_mode") or request.get("evidence_mode") or "dry_run_contract")


def _render_evidence_modes(evidence_modes: dict[str, int]) -> str:
    if not evidence_modes:
        return "nenhum"
    return ", ".join(f"{mode}={count}" for mode, count in sorted(evidence_modes.items()))


def _json_contains_mismatches(expected: dict[str, object], actual: dict[str, object], prefix: str = "") -> list[dict[str, object]]:
    mismatches: list[dict[str, object]] = []
    for key, expected_value in expected.items():
        field = f"{prefix}.{key}" if prefix else str(key)
        if key not in actual:
            mismatches.append({"field": field, "expected": expected_value, "actual": None})
            continue
        actual_value = actual[key]
        if isinstance(expected_value, dict) and isinstance(actual_value, dict):
            mismatches.extend(_json_contains_mismatches(expected_value, actual_value, field))
        elif actual_value != expected_value:
            mismatches.append({"field": field, "expected": expected_value, "actual": actual_value})
    return mismatches


def _api_recommendation(status: str, diff: dict[str, object], error: str | None) -> str:
    if error:
        return f"Corrigir conectividade, autenticação ou payload antes de implementar. Erro: {error}"
    if status == "passed":
        return "Contrato validado. Pode virar contexto técnico para implementação futura."
    return f"Revisar expected output ou payload. Diferenças: {json.dumps(diff.get('mismatches', []), ensure_ascii=False)}"


def _render_suite_lines(suites: list[dict[str, object]]) -> str:
    if not suites:
        return "- Nenhuma suite cadastrada."
    return "\n".join(f"- `{suite['name']}` provider={suite['provider']} docs={suite.get('docs_url') or 'n/a'}" for suite in suites)


def _render_failed_api_lines(results: list[dict[str, object]]) -> str:
    if not results:
        return "- Nenhuma falha registrada."
    lines = []
    for result in results[:20]:
        log = result.get("structured_log") or {}
        lines.append(f"- `{log.get('test_name', result.get('case_id'))}` diff={json.dumps(result.get('diff'), ensure_ascii=False)}")
    return "\n".join(lines)
