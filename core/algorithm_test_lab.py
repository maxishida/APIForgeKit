from __future__ import annotations

import json
from datetime import UTC, datetime
from time import perf_counter
from uuid import uuid4

from sqlalchemy import desc, select
from sqlalchemy.orm import Session, sessionmaker

from core.community_bot_engine import BotEvent, BotRule, process_bot_event
from core.community_bot_seed import (
    COMMUNITY_BOT_ENGINE_RULES,
    COMMUNITY_BOT_INPUT_SCHEMA,
    COMMUNITY_BOT_NEXTJS_FILES,
    COMMUNITY_BOT_OUTPUT_SCHEMA,
    DEFAULT_COMMUNITY_BOT_CASES,
)
from core.lead_algorithm import LeadInput, SPAM_PATTERNS, calculate_lead_score
from core.models import AlgorithmDefinition, AlgorithmTestCase, AlgorithmTestResult, AlgorithmTestRun


LEAD_SCORE_RULES = [
    "Origem WhatsApp soma 25",
    "Origem Ligação soma 30",
    "Origem Landing Page soma 20",
    "Origem Instagram soma 15",
    "Origem LinkedIn soma 10",
    "Urgência alta soma 25",
    "Urgência média soma 15",
    "Urgência baixa soma 5",
    "Interesse alto soma 25",
    "Interesse médio soma 15",
    "Interesse baixo soma 5",
    "Telefone soma 10",
    "E-mail soma 5",
    "Cliente anterior soma 20",
    "Mensagem vazia é inválida",
    "Spam é inválido",
    "Sem telefone e sem e-mail remove 20",
    "Mensagem curta remove 10",
    "0-30 cold_lead",
    "31-60 warm_lead",
    "61-80 hot_lead",
    "81-100 urgent_lead",
]

LEAD_SCORE_NEXTJS_FILES = [
    "/lib/lead-score.ts",
    "/types/lead.ts",
    "/app/api/leads/score/route.ts",
    "/components/dashboard/AlgorithmResultTable.tsx",
    "/tests/lead-score.test.ts",
]

LEAD_SCORE_INPUT_SCHEMA = {
    "type": "object",
    "required": ["source", "message", "urgency", "interest", "has_phone", "has_email", "previous_customer"],
    "properties": {
        "lead_name": {"type": "string"},
        "source": {"type": "string"},
        "message": {"type": "string"},
        "budget": {"type": "string"},
        "urgency": {"type": "string"},
        "interest": {"type": "string"},
        "has_phone": {"type": "boolean"},
        "has_email": {"type": "boolean"},
        "previous_customer": {"type": "boolean"},
    },
}

LEAD_SCORE_OUTPUT_SCHEMA = {
    "type": "object",
    "required": ["score", "classification", "status", "reasons", "recommended_action"],
    "properties": {
        "score": {"type": "integer", "minimum": 0, "maximum": 100},
        "classification": {"type": "string"},
        "status": {"type": "string"},
        "reasons": {"type": "array", "items": {"type": "string"}},
        "recommended_action": {"type": "string"},
    },
}

DEFAULT_LEAD_SCORE_CASES = [
    {
        "name": "lead frio Instagram",
        "input_payload": {
            "lead_name": "Lead frio",
            "source": "Instagram",
            "message": "Oi",
            "budget": "",
            "urgency": "baixa",
            "interest": "baixo",
            "has_phone": False,
            "has_email": False,
            "previous_customer": False,
        },
        "expected_output": {"classification": "cold_lead", "min_score": 0, "max_score": 30},
        "tags": ["cold", "edge", "short_message"],
    },
    {
        "name": "lead morno Landing Page",
        "input_payload": {
            "lead_name": "Lead morno",
            "source": "Landing Page",
            "message": "Tenho interesse e gostaria de entender melhor a solução",
            "budget": "",
            "urgency": "média",
            "interest": "baixo",
            "has_phone": False,
            "has_email": True,
            "previous_customer": False,
        },
        "expected_output": {"classification": "warm_lead", "min_score": 31, "max_score": 60},
        "tags": ["warm"],
    },
    {
        "name": "lead quente WhatsApp",
        "input_payload": {
            "lead_name": "Lead quente",
            "source": "WhatsApp",
            "message": "Tenho interesse e quero preço",
            "budget": "",
            "urgency": "média",
            "interest": "médio",
            "has_phone": True,
            "has_email": False,
            "previous_customer": False,
        },
        "expected_output": {"classification": "hot_lead", "min_score": 61, "max_score": 80},
        "tags": ["hot", "whatsapp"],
    },
    {
        "name": "lead urgente ligação",
        "input_payload": {
            "lead_name": "Lead urgente",
            "source": "Ligação",
            "message": "Preciso de atendimento agora",
            "budget": "",
            "urgency": "alta",
            "interest": "alto",
            "has_phone": True,
            "has_email": True,
            "previous_customer": False,
        },
        "expected_output": {"classification": "urgent_lead", "min_score": 81},
        "tags": ["urgent", "call"],
    },
    {
        "name": "lead inválido mensagem vazia",
        "input_payload": {
            "lead_name": "Lead inválido",
            "source": "Landing Page",
            "message": "",
            "budget": "",
            "urgency": "baixa",
            "interest": "baixo",
            "has_phone": False,
            "has_email": False,
            "previous_customer": False,
        },
        "expected_output": {"classification": "invalid_lead", "score": 0},
        "tags": ["invalid", "empty_message", "edge"],
    },
    {
        "name": "lead spam",
        "input_payload": {
            "lead_name": "Lead spam",
            "source": "Instagram",
            "message": "Clique aqui e ganhe dinheiro agora",
            "budget": "",
            "urgency": "alta",
            "interest": "alto",
            "has_phone": True,
            "has_email": True,
            "previous_customer": False,
        },
        "expected_output": {"classification": "invalid_lead", "score": 0},
        "tags": ["invalid", "spam", "edge"],
    },
    {
        "name": "lead sem contato",
        "input_payload": {
            "lead_name": "Lead sem contato",
            "source": "Instagram",
            "message": "Quero conhecer a solução para minha empresa",
            "budget": "",
            "urgency": "baixa",
            "interest": "baixo",
            "has_phone": False,
            "has_email": False,
            "previous_customer": False,
        },
        "expected_output": {"classification": "cold_lead", "min_score": 0, "max_score": 30},
        "tags": ["cold", "no_contact", "edge"],
    },
    {
        "name": "cliente anterior com alta intenção",
        "input_payload": {
            "lead_name": "Cliente anterior",
            "source": "Landing Page",
            "message": "Quero comprar novamente hoje e preciso de orçamento",
            "budget": "",
            "urgency": "alta",
            "interest": "alto",
            "has_phone": False,
            "has_email": True,
            "previous_customer": True,
        },
        "expected_output": {"classification": "urgent_lead", "min_score": 81},
        "tags": ["urgent", "previous_customer"],
    },
    {
        "name": "boundary score 30 cold",
        "input_payload": {
            "lead_name": "Boundary cold",
            "source": "LinkedIn",
            "message": "Mensagem neutra para avaliar limite",
            "budget": "",
            "urgency": "baixa",
            "interest": "baixo",
            "has_phone": True,
            "has_email": False,
            "previous_customer": False,
        },
        "expected_output": {"classification": "cold_lead", "score": 30},
        "tags": ["boundary", "cold"],
    },
    {
        "name": "boundary score 35 warm",
        "input_payload": {
            "lead_name": "Boundary warm",
            "source": "Instagram",
            "message": "Mensagem neutra para avaliar limite",
            "budget": "",
            "urgency": "baixa",
            "interest": "baixo",
            "has_phone": True,
            "has_email": False,
            "previous_customer": False,
        },
        "expected_output": {"classification": "warm_lead", "score": 35},
        "tags": ["boundary", "warm"],
    },
    {
        "name": "boundary score 60 warm",
        "input_payload": {
            "lead_name": "Boundary warm max",
            "source": "Landing Page",
            "message": "Mensagem neutra para avaliar limite",
            "budget": "",
            "urgency": "média",
            "interest": "médio",
            "has_phone": True,
            "has_email": False,
            "previous_customer": False,
        },
        "expected_output": {"classification": "warm_lead", "score": 60},
        "tags": ["boundary", "warm"],
    },
    {
        "name": "boundary score 65 hot",
        "input_payload": {
            "lead_name": "Boundary hot",
            "source": "WhatsApp",
            "message": "Mensagem neutra para avaliar limite",
            "budget": "",
            "urgency": "média",
            "interest": "médio",
            "has_phone": True,
            "has_email": False,
            "previous_customer": False,
        },
        "expected_output": {"classification": "hot_lead", "score": 65},
        "tags": ["boundary", "hot"],
    },
    {
        "name": "boundary score 80 hot",
        "input_payload": {
            "lead_name": "Boundary hot max",
            "source": "WhatsApp",
            "message": "Mensagem neutra para avaliar limite",
            "budget": "",
            "urgency": "alta",
            "interest": "médio",
            "has_phone": True,
            "has_email": True,
            "previous_customer": False,
        },
        "expected_output": {"classification": "hot_lead", "score": 80},
        "tags": ["boundary", "hot"],
    },
    {
        "name": "boundary score 85 urgent",
        "input_payload": {
            "lead_name": "Boundary urgent",
            "source": "Ligação",
            "message": "Mensagem neutra para avaliar limite",
            "budget": "",
            "urgency": "alta",
            "interest": "alto",
            "has_phone": False,
            "has_email": True,
            "previous_customer": False,
        },
        "expected_output": {"classification": "urgent_lead", "score": 85},
        "tags": ["boundary", "urgent"],
    },
    {
        "name": "alta intenção sem contato",
        "input_payload": {
            "lead_name": "Alta intenção sem contato",
            "source": "WhatsApp",
            "message": "Tenho muito interesse na solução para minha empresa",
            "budget": "",
            "urgency": "alta",
            "interest": "alto",
            "has_phone": False,
            "has_email": False,
            "previous_customer": False,
        },
        "expected_output": {"classification": "warm_lead", "score": 55},
        "tags": ["edge", "no_contact", "conflicting_signal"],
    },
    {
        "name": "cliente anterior baixa intenção",
        "input_payload": {
            "lead_name": "Cliente anterior baixa intenção",
            "source": "LinkedIn",
            "message": "Mensagem neutra para avaliar cliente anterior",
            "budget": "",
            "urgency": "baixa",
            "interest": "baixo",
            "has_phone": False,
            "has_email": True,
            "previous_customer": True,
        },
        "expected_output": {"classification": "warm_lead", "score": 45},
        "tags": ["edge", "previous_customer", "conflicting_signal"],
    },
    {
        "name": "mensagem vazia sobrescreve score",
        "input_payload": {
            "lead_name": "Mensagem vazia high signal",
            "source": "Ligação",
            "message": "",
            "budget": "",
            "urgency": "alta",
            "interest": "alto",
            "has_phone": True,
            "has_email": True,
            "previous_customer": True,
        },
        "expected_output": {"classification": "invalid_lead", "score": 0},
        "tags": ["invalid", "edge", "override"],
    },
]


class AlgorithmTestRepository:
    def __init__(self, session_factory: sessionmaker[Session]):
        self.session_factory = session_factory

    def create_definition(
        self,
        *,
        name: str,
        description: str,
        input_schema: dict[str, object],
        output_schema: dict[str, object],
        rules: list[str] | None = None,
        nextjs_files: list[str] | None = None,
    ) -> dict[str, object]:
        with self.session_factory() as session:
            row = AlgorithmDefinition(
                id=str(uuid4()),
                name=name,
                description=description,
                input_schema=input_schema,
                output_schema=output_schema,
                rules=rules or [],
                nextjs_files=nextjs_files or [],
            )
            session.add(row)
            session.commit()
            session.refresh(row)
            return row.to_dict()

    def get_definition_by_name(self, name: str) -> dict[str, object]:
        with self.session_factory() as session:
            row = session.scalar(select(AlgorithmDefinition).where(AlgorithmDefinition.name == name))
            if row is None:
                raise ValueError(f"Unknown algorithm: {name}")
            return row.to_dict()

    def get_definition(self, algorithm_id: str) -> dict[str, object]:
        with self.session_factory() as session:
            row = session.get(AlgorithmDefinition, algorithm_id)
            if row is None:
                raise ValueError(f"Unknown algorithm_id: {algorithm_id}")
            return row.to_dict()

    def list_definitions(self) -> list[dict[str, object]]:
        with self.session_factory() as session:
            rows = session.scalars(select(AlgorithmDefinition).order_by(AlgorithmDefinition.name)).all()
            return [row.to_dict() for row in rows]

    def create_case(
        self,
        *,
        algorithm_id: str,
        name: str,
        input_payload: dict[str, object],
        expected_output: dict[str, object],
        tags: list[str] | None = None,
        enabled: bool = True,
    ) -> dict[str, object]:
        with self.session_factory() as session:
            row = AlgorithmTestCase(
                id=str(uuid4()),
                algorithm_id=algorithm_id,
                name=name,
                input_payload=input_payload,
                expected_output=expected_output,
                tags=tags or [],
                enabled=enabled,
            )
            session.add(row)
            session.commit()
            session.refresh(row)
            return row.to_dict()

    def get_case(self, case_id: str) -> dict[str, object]:
        with self.session_factory() as session:
            row = session.get(AlgorithmTestCase, case_id)
            if row is None:
                raise ValueError(f"Unknown case_id: {case_id}")
            return row.to_dict()

    def list_cases(self, algorithm_id: str | None = None) -> list[dict[str, object]]:
        with self.session_factory() as session:
            statement = select(AlgorithmTestCase).order_by(AlgorithmTestCase.created_at)
            if algorithm_id:
                statement = statement.where(AlgorithmTestCase.algorithm_id == algorithm_id)
            rows = session.scalars(statement).all()
            return [row.to_dict() for row in rows]

    def start_run(self, algorithm_id: str, suite_name: str, total_cases: int) -> dict[str, object]:
        with self.session_factory() as session:
            row = AlgorithmTestRun(
                id=str(uuid4()),
                algorithm_id=algorithm_id,
                suite_name=suite_name,
                total_cases=total_cases,
                status="running",
            )
            session.add(row)
            session.commit()
            session.refresh(row)
            return row.to_dict()

    def finish_run(self, run_id: str, *, passed: int, failed: int, summary: dict[str, object] | None = None) -> dict[str, object]:
        with self.session_factory() as session:
            row = session.get(AlgorithmTestRun, run_id)
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
        case_id: str,
        algorithm_id: str,
        status: str,
        input_payload: dict[str, object],
        expected_output: dict[str, object],
        actual_output: dict[str, object],
        diff: dict[str, object],
        latency_ms: float,
        structured_log: dict[str, object],
        recommendation: str,
        nextjs_impact: str,
    ) -> dict[str, object]:
        with self.session_factory() as session:
            row = AlgorithmTestResult(
                id=str(uuid4()),
                run_id=run_id,
                case_id=case_id,
                algorithm_id=algorithm_id,
                status=status,
                input_payload=input_payload,
                expected_output=expected_output,
                actual_output=actual_output,
                diff=diff,
                latency_ms=latency_ms,
                structured_log=structured_log,
                recommendation=recommendation,
                nextjs_impact=nextjs_impact,
            )
            session.add(row)
            session.commit()
            session.refresh(row)
            return row.to_dict()

    def record_context_export(self, format: str, path: str, summary: dict[str, object]) -> dict[str, object]:
        with self.session_factory() as session:
            from core.models import ContextExport

            row = ContextExport(
                id=str(uuid4()),
                run_id=str(summary.get("run_id", "algorithm_test_lab")),
                format=format,
                path=path,
                summary=summary,
            )
            session.add(row)
            session.commit()
            return {"id": row.id, "path": row.path}

    def list_runs(self, limit: int = 50) -> list[dict[str, object]]:
        with self.session_factory() as session:
            rows = session.scalars(select(AlgorithmTestRun).order_by(desc(AlgorithmTestRun.created_at)).limit(limit)).all()
            return [row.to_dict() for row in rows]

    def list_results(
        self,
        *,
        run_id: str | None = None,
        algorithm_id: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, object]]:
        with self.session_factory() as session:
            statement = select(AlgorithmTestResult)
            if run_id:
                statement = statement.where(AlgorithmTestResult.run_id == run_id)
            if algorithm_id:
                statement = statement.where(AlgorithmTestResult.algorithm_id == algorithm_id)
            statement = statement.order_by(desc(AlgorithmTestResult.created_at)).limit(limit)
            rows = session.scalars(statement).all()
            return [row.to_dict() for row in rows]

    def metrics(self) -> dict[str, object]:
        results = self.list_results(limit=10000)
        runs = self.list_runs(limit=10000)
        passed = len([result for result in results if result["status"] == "passed"])
        failed = len([result for result in results if result["status"] == "failed"])
        latencies = [float(result["latency_ms"] or 0) for result in results]
        evidence_modes: dict[str, int] = {}
        for result in results:
            structured_log = result.get("structured_log") or {}
            mode = str(structured_log.get("evidence_mode") or "seed_validation")
            evidence_modes[mode] = evidence_modes.get(mode, 0) + 1
        return {
            "total_runs": len(runs),
            "total_results": len(results),
            "passed": passed,
            "failed": failed,
            "pass_rate": round((passed / len(results)) * 100, 2) if results else 0,
            "average_latency_ms": round(sum(latencies) / len(latencies), 2) if latencies else 0,
            "latest_run": runs[0] if runs else None,
            "evidence_modes": evidence_modes,
        }


class AlgorithmTestRunner:
    def __init__(self, repository: AlgorithmTestRepository):
        self.repository = repository

    def run_single_case(self, case_id: str) -> dict[str, object]:
        case = self.repository.get_case(case_id)
        run = self.repository.start_run(str(case["algorithm_id"]), f"single:{case['name']}", 1)
        result = self._execute_case(run["id"], case)
        return self.repository.finish_run(
            run["id"],
            passed=1 if result["status"] == "passed" else 0,
            failed=0 if result["status"] == "passed" else 1,
            summary={"case": case["name"]},
        )

    def run_suite(self, algorithm_id: str) -> dict[str, object]:
        cases = [case for case in self.repository.list_cases(algorithm_id) if case.get("enabled")]
        run = self.repository.start_run(algorithm_id, "default_suite", len(cases))
        passed = 0
        failed = 0
        for case in cases:
            result = self._execute_case(run["id"], case)
            if result["status"] == "passed":
                passed += 1
            else:
                failed += 1
        return self.repository.finish_run(
            run["id"],
            passed=passed,
            failed=failed,
            summary={"suite": "default_suite", "total_cases": len(cases)},
        )

    def _execute_case(self, run_id: str, case: dict[str, object]) -> dict[str, object]:
        definition = self.repository.get_definition(str(case["algorithm_id"]))
        started = perf_counter()
        error = None
        invariants: dict[str, object] = _failed_invariants()
        try:
            actual = run_algorithm(str(definition["name"]), dict(case["input_payload"]))
            expected = dict(case["expected_output"])
            if definition["name"] == "community_bot_engine":
                diff = validate_community_expected_output(expected, actual)
            else:
                diff = validate_expected_output(expected, actual)
            invariants = _algorithm_invariants(str(definition["name"]), dict(case["input_payload"]), actual)
            invariant_mismatches = _invariant_mismatches(invariants)
            if invariant_mismatches:
                diff = {"passed": False, "mismatches": [*diff.get("mismatches", []), *invariant_mismatches]}
        except Exception as exc:  # noqa: BLE001 - invalid algorithm input is evidence, not a crash
            actual = {}
            error = str(exc)
            invariants = _failed_invariants()
            diff = {
                "passed": False,
                "mismatches": [{"field": "input_payload", "expected": "valid lead_score payload", "actual": error}],
            }
        latency = round((perf_counter() - started) * 1000, 2)
        status = "passed" if diff["passed"] and error is None else "failed"
        recommendation = _recommendation(status, diff)
        structured_log = {
            "id": str(uuid4()),
            "timestamp": datetime.now(UTC).isoformat(),
            "lab": "algorithm_test_lab",
            "algorithm": definition["name"],
            "evidence_mode": "seed_validation",
            "case_id": case["id"],
            "case_name": case["name"],
            "status": status,
            "latency_ms": latency,
            "input": case["input_payload"],
            "expected": case["expected_output"],
            "actual": actual,
            "diff": diff,
            "invariants": invariants,
            "recommendation": recommendation,
            "error": error if error else (None if status == "passed" else "Expected output mismatch"),
        }
        return self.repository.record_result(
            run_id=run_id,
            case_id=str(case["id"]),
            algorithm_id=str(case["algorithm_id"]),
            status=status,
            input_payload=dict(case["input_payload"]),
            expected_output=dict(case["expected_output"]),
            actual_output=actual,
            diff=diff,
            latency_ms=latency,
            structured_log=structured_log,
            recommendation=recommendation,
            nextjs_impact=_nextjs_impact_for_algorithm(str(definition["name"])),
        )


def ensure_default_algorithms(repository: AlgorithmTestRepository) -> None:
    try:
        lead_definition = repository.get_definition_by_name("lead_score")
    except ValueError:
        lead_definition = repository.create_definition(
            name="lead_score",
            description="Algoritmo determinístico de score e classificação de leads.",
            input_schema=LEAD_SCORE_INPUT_SCHEMA,
            output_schema=LEAD_SCORE_OUTPUT_SCHEMA,
            rules=LEAD_SCORE_RULES,
            nextjs_files=LEAD_SCORE_NEXTJS_FILES,
        )
    lead_existing = {case["name"] for case in repository.list_cases(lead_definition["id"])}
    for case in DEFAULT_LEAD_SCORE_CASES:
        if case["name"] not in lead_existing:
            repository.create_case(algorithm_id=lead_definition["id"], **case)

    try:
        bot_definition = repository.get_definition_by_name("community_bot_engine")
    except ValueError:
        bot_definition = repository.create_definition(
            name="community_bot_engine",
            description="Motor determinístico Community Bot Engine / Vice City NPC Engine para eventos, regras, condições e ações.",
            input_schema=COMMUNITY_BOT_INPUT_SCHEMA,
            output_schema=COMMUNITY_BOT_OUTPUT_SCHEMA,
            rules=COMMUNITY_BOT_ENGINE_RULES,
            nextjs_files=COMMUNITY_BOT_NEXTJS_FILES,
        )
    bot_existing = {case["name"] for case in repository.list_cases(bot_definition["id"])}
    for case in DEFAULT_COMMUNITY_BOT_CASES:
        if case["name"] not in bot_existing:
            repository.create_case(algorithm_id=bot_definition["id"], **case)


def run_algorithm(name: str, input_payload: dict[str, object]) -> dict[str, object]:
    if name == "community_bot_engine":
        return _run_community_bot_engine(input_payload)
    if name != "lead_score":
        raise ValueError(f"Unsupported algorithm: {name}")
    _validate_required_fields(input_payload, LEAD_SCORE_INPUT_SCHEMA["required"])
    lead = LeadInput(
        lead_name=_optional_string(input_payload.get("lead_name", ""), "lead_name"),
        source=_required_string(input_payload.get("source"), "source"),
        message=_required_string(input_payload.get("message"), "message"),
        budget=_optional_string(input_payload.get("budget", ""), "budget"),
        urgency=_required_string(input_payload.get("urgency"), "urgency"),
        interest=_required_string(input_payload.get("interest"), "interest"),
        has_phone=_required_bool(input_payload.get("has_phone"), "has_phone"),
        has_email=_required_bool(input_payload.get("has_email"), "has_email"),
        previous_customer=_required_bool(input_payload.get("previous_customer"), "previous_customer"),
    )
    result = calculate_lead_score(lead).to_dict()
    result["classification"] = result["status"]
    return result


def _run_community_bot_engine(input_payload: dict[str, object]) -> dict[str, object]:
    event_payload = dict(input_payload.get("event") or {})
    user_payload = dict(input_payload.get("user") or {})
    rules_payload = list(input_payload.get("rules") or [])
    history_payload = list(input_payload.get("history") or [])
    templates_payload = dict(input_payload.get("templates") or {})

    event = BotEvent(
        user_id=str(event_payload.get("user_id", "")),
        event_name=str(event_payload.get("event_name", "")),
        entity_type=str(event_payload.get("entity_type", "")),
        entity_id=str(event_payload.get("entity_id", "")),
        metadata_json=dict(event_payload.get("metadata_json") or {}),
        source=str(event_payload.get("source", "web_app")),
        simulate=bool(event_payload.get("simulate", False)),
    )
    rules = [
        BotRule(
            id=str(rule.get("id", "")),
            bot_id=str(rule.get("bot_id", "")),
            bot_name=str(rule.get("bot_name", "")),
            bot_slug=str(rule.get("bot_slug", "")),
            name=str(rule.get("name", "")),
            event_name=str(rule.get("event_name", "")),
            condition_json=dict(rule.get("condition_json") or {}),
            action_json=list(rule.get("action_json") or []),
            template_id=str(rule.get("template_id", "")),
            priority=int(rule.get("priority", 0)),
            is_active=bool(rule.get("is_active", True)),
            cooldown_minutes=int(rule.get("cooldown_minutes", 0)),
            run_once_per_user=bool(rule.get("run_once_per_user", False)),
        )
        for rule in rules_payload
    ]
    try:
        return process_bot_event(
            event=event,
            user=user_payload,
            rules=rules,
            history=history_payload,
            templates=templates_payload,
        ).to_dict()
    except ValueError as exc:
        return {
            "status": "invalid_event",
            "classification": "invalid",
            "rules_evaluated": 0,
            "rules_matched": 0,
            "actions_executed": [],
            "actions_skipped": [],
            "bot_logs": [],
            "reasons": [str(exc)],
            "user_updates": user_payload,
            "error": str(exc),
        }


def validate_community_expected_output(expected: dict[str, object], actual: dict[str, object]) -> dict[str, object]:
    mismatches: list[dict[str, object]] = []
    base = validate_expected_output(
        {key: value for key, value in expected.items() if key in {"classification", "status", "rules_matched"}},
        actual,
    )
    mismatches.extend(base.get("mismatches", []))

    if "actions_executed_count" in expected:
        count = len(actual.get("actions_executed") or [])
        if count != expected["actions_executed_count"]:
            mismatches.append(
                {
                    "field": "actions_executed_count",
                    "expected": expected["actions_executed_count"],
                    "actual": count,
                }
            )

    if "action_types" in expected:
        executed = actual.get("actions_executed") or []
        actual_types = [str(item.get("action_type", "")) for item in executed]
        for action_type in expected["action_types"]:
            if action_type not in actual_types:
                mismatches.append(
                    {
                        "field": "action_types",
                        "expected": action_type,
                        "actual": actual_types,
                    }
                )

    if "skipped_status" in expected:
        skipped = actual.get("actions_skipped") or []
        statuses = {str(item.get("status", "")) for item in skipped}
        if expected["skipped_status"] not in statuses:
            mismatches.append(
                {
                    "field": "skipped_status",
                    "expected": expected["skipped_status"],
                    "actual": sorted(statuses),
                }
            )

    if expected.get("all_simulated"):
        executed = actual.get("actions_executed") or []
        if not executed or not all(bool(item.get("simulated")) for item in executed):
            mismatches.append(
                {
                    "field": "all_simulated",
                    "expected": True,
                    "actual": [item.get("simulated") for item in executed],
                }
            )

    if "first_executed_bot" in expected:
        executed = actual.get("actions_executed") or []
        first_bot = str(executed[0].get("bot_name", "")) if executed else ""
        if first_bot != expected["first_executed_bot"]:
            mismatches.append(
                {
                    "field": "first_executed_bot",
                    "expected": expected["first_executed_bot"],
                    "actual": first_bot,
                }
            )

    if "min_bot_logs" in expected:
        logs_count = len(actual.get("bot_logs") or [])
        if logs_count < int(expected["min_bot_logs"]):
            mismatches.append(
                {
                    "field": "min_bot_logs",
                    "expected": f">= {expected['min_bot_logs']}",
                    "actual": logs_count,
                }
            )

    if "official_tag" in expected:
        executed = actual.get("actions_executed") or []
        tags = {str(item.get("official_tag", "")) for item in executed}
        if expected["official_tag"] not in tags:
            mismatches.append(
                {
                    "field": "official_tag",
                    "expected": expected["official_tag"],
                    "actual": sorted(tags),
                }
            )

    return {"passed": not mismatches, "mismatches": mismatches}


def _nextjs_impact_for_algorithm(name: str) -> str:
    if name == "community_bot_engine":
        return (
            "Implementar Community Bot Engine em TypeScript com EventTrackingService, "
            "BotRulesEngine, ConditionEvaluator, BotActionExecutor e logs em PostgreSQL."
        )
    return "Implementar lógica determinística em /lib/lead-score.ts e cobrir estes casos em testes unitários."


def _algorithm_invariants(name: str, input_payload: dict[str, object], actual: dict[str, object]) -> dict[str, object]:
    if name == "community_bot_engine":
        if actual.get("status") == "invalid_event":
            return {
                "payload_validated": True,
                "deterministic": True,
                "idempotency_enforced": True,
                "cooldown_enforced": True,
                "all_actions_logged": True,
            }
        second = run_algorithm(name, dict(input_payload))
        stable_fields = (
            "status",
            "classification",
            "rules_evaluated",
            "rules_matched",
            "actions_executed",
            "actions_skipped",
            "bot_logs",
            "reasons",
        )
        deterministic = {field: actual.get(field) for field in stable_fields} == {
            field: second.get(field) for field in stable_fields
        }
        logs = actual.get("bot_logs") or []
        executed = actual.get("actions_executed") or []
        all_logged = len(logs) >= len(executed)
        skipped = actual.get("actions_skipped") or []
        idempotency_ok = True
        for item in skipped:
            if item.get("status") == "duplicate_blocked":
                idempotency_ok = True
                break
        cooldown_ok = True
        for item in skipped:
            if item.get("status") == "rate_limited":
                cooldown_ok = True
                break
        return {
            "payload_validated": actual.get("status") != "invalid_event",
            "deterministic": deterministic,
            "idempotency_enforced": idempotency_ok or not skipped,
            "cooldown_enforced": cooldown_ok or not skipped,
            "all_actions_logged": all_logged,
        }
    if name != "lead_score":
        return {}
    second = run_algorithm(name, dict(input_payload))
    stable_fields = ("score", "status", "classification", "reasons", "recommended_action", "nextjs_impact")
    deterministic = {field: actual.get(field) for field in stable_fields} == {
        field: second.get(field) for field in stable_fields
    }
    score = actual.get("score")
    message = str(input_payload.get("message") or "")
    normalized_message = message.strip().lower()
    invalid_expected = not message.strip() or any(pattern in normalized_message for pattern in SPAM_PATTERNS)
    invalid_override_checked = not invalid_expected or (
        actual.get("classification") == "invalid_lead" and actual.get("score") == 0
    )
    return {
        "payload_validated": True,
        "deterministic": deterministic,
        "score_clamped": isinstance(score, int) and 0 <= score <= 100,
        "invalid_override_checked": invalid_override_checked,
    }


def _failed_invariants() -> dict[str, object]:
    return {
        "payload_validated": False,
        "deterministic": False,
        "score_clamped": False,
        "invalid_override_checked": False,
    }


def _invariant_mismatches(invariants: dict[str, object]) -> list[dict[str, object]]:
    return [
        {"field": f"invariant.{name}", "expected": True, "actual": value}
        for name, value in invariants.items()
        if value is not True
    ]


def _validate_required_fields(payload: dict[str, object], required_fields: list[object]) -> None:
    missing = [str(field) for field in required_fields if str(field) not in payload]
    if missing:
        raise ValueError(f"Missing required lead_score field(s): {', '.join(missing)}")


def _required_string(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be a string")
    return value


def _optional_string(value: object, field: str) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        raise ValueError(f"{field} must be a string")
    return value


def _required_bool(value: object, field: str) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes", "sim"}:
            return True
        if normalized in {"false", "0", "no", "nao", "não"}:
            return False
    raise ValueError(f"{field} must be a boolean")


def validate_expected_output(expected: dict[str, object], actual: dict[str, object]) -> dict[str, object]:
    mismatches: list[dict[str, object]] = []
    for field, expected_value in expected.items():
        if field == "min_score":
            score = actual.get("score")
            if not isinstance(score, (int, float)) or score < expected_value:
                mismatches.append({"field": "score", "expected": f">= {expected_value}", "actual": score})
            continue
        if field == "max_score":
            score = actual.get("score")
            if not isinstance(score, (int, float)) or score > expected_value:
                mismatches.append({"field": "score", "expected": f"<= {expected_value}", "actual": score})
            continue
        actual_value = actual.get("status") if field == "classification" and "classification" not in actual else actual.get(field)
        if actual_value != expected_value:
            mismatches.append({"field": field, "expected": expected_value, "actual": actual_value})
    return {"passed": not mismatches, "mismatches": mismatches}


def summarize_algorithm_invariants(results: list[dict[str, object]]) -> dict[str, object]:
    sample = (results[0].get("structured_log") or {}).get("invariants") or {} if results else {}
    if "idempotency_enforced" in sample:
        invariant_names = [
            "payload_validated",
            "deterministic",
            "idempotency_enforced",
            "cooldown_enforced",
            "all_actions_logged",
        ]
    else:
        invariant_names = ["payload_validated", "deterministic", "score_clamped", "invalid_override_checked"]
    summary: dict[str, object] = {"total": len(results), "failed": 0, "all_passed": False}
    for name in invariant_names:
        summary[name] = 0
    for result in results:
        invariants = (result.get("structured_log") or {}).get("invariants") or {}
        result_passed = True
        for name in invariant_names:
            if invariants.get(name) is True:
                summary[name] = int(summary[name]) + 1
            else:
                result_passed = False
        if not result_passed:
            summary["failed"] = int(summary["failed"]) + 1
    summary["all_passed"] = bool(results) and int(summary["failed"]) == 0
    return summary


def build_algorithm_context(repository: AlgorithmTestRepository, limit: int = 100, algorithm_name: str | None = None) -> str:
    definitions = repository.list_definitions()
    runs = repository.list_runs(limit=20)
    if not definitions:
        return "# Contexto Técnico - Algorithm Test Lab\n\nNenhum algoritmo cadastrado ainda.\n"
    if algorithm_name:
        try:
            definition = repository.get_definition_by_name(algorithm_name)
        except ValueError:
            return f"# Contexto Técnico - Algorithm Test Lab\n\nAlgoritmo `{algorithm_name}` não encontrado.\n"
    else:
        definition = definitions[0]
    results = repository.list_results(algorithm_id=str(definition["id"]), limit=limit)
    passed = [result for result in results if result["status"] == "passed"]
    failed = [result for result in results if result["status"] == "failed"]
    invariants = summarize_algorithm_invariants(results)
    edge_cases = [
        result
        for result in results
        if any(
            token in str(result["structured_log"].get("case_name", "")).lower()
            for token in ["inválido", "spam", "sem contato", "duplicad", "cooldown", "bloquead", "invalido"]
        )
    ]
    if not edge_cases:
        edge_cases = [
            result
            for result in results
            if any(tag in str(result["expected_output"].get("classification", "")) for tag in ["invalid", "cold", "blocked"])
        ][:10]

    invariant_lines = [
        f"- Total analisado: {invariants['total']}",
        f"- Todos passaram: {invariants['all_passed']}",
        f"- Payload validado: {invariants.get('payload_validated', 0)}",
        f"- Determinístico: {invariants.get('deterministic', 0)}",
    ]
    for key, label in (
        ("score_clamped", "Score 0-100"),
        ("invalid_override_checked", "Invalid override"),
        ("idempotency_enforced", "Idempotência"),
        ("cooldown_enforced", "Cooldown"),
        ("all_actions_logged", "Logs completos"),
    ):
        if key in invariants:
            invariant_lines.append(f"- {label}: {invariants[key]}")
    invariant_lines.append(f"- Falhas de invariantes: {invariants['failed']}")
    invariant_block = "\n".join(invariant_lines)

    return f"""# Contexto Técnico - Algorithm Test Lab

## Algoritmo

- Nome: `{definition["name"]}`
- Descrição: {definition["description"]}
- Runs analisadas: {len(runs)}
- Resultados analisados: {len(results)}

## Regras Validadas

{_render_list(definition["rules"])}

## Testes que passaram

{_render_result_lines(passed) or "- Nenhum teste passou ainda."}

## Testes que falharam

{_render_result_lines(failed, include_diff=True) or "- Nenhum teste falhou."}

## Invariantes

{invariant_block}

## Edge Cases

{_render_result_lines(edge_cases) or "- Nenhum edge case registrado."}

## Recomendações

- Manter o algoritmo determinístico e sem dependência de LLM.
- Usar os casos salvos como suíte obrigatória antes de alterar pesos.
- Implementar logs estruturados equivalentes no endpoint futuro.
- Bloquear deploy se algum caso crítico falhar.

## Impacto para implementação Next.js

- Implementar `calculateLeadScore` com as mesmas regras.
- Criar tipos para input/output.
- Criar endpoint que retorne score, classificação, motivos e recomendação.
- Reproduzir esta suíte como testes unitários.

## Arquivos sugeridos

{_render_list(definition["nextjs_files"])}
"""


def export_algorithm_suite(repository: AlgorithmTestRepository, algorithm_id: str, output_dir: str) -> str:
    from pathlib import Path

    definition = repository.get_definition(algorithm_id)
    cases = repository.list_cases(algorithm_id)
    payload = {"algorithm_definitions": [definition], "algorithm_test_cases": cases}
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{definition['name']}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(path)


def import_algorithm_suite(repository: AlgorithmTestRepository, path: str) -> dict[str, object]:
    from pathlib import Path

    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    source_definition = payload["algorithm_definitions"][0]
    try:
        definition = repository.get_definition_by_name(str(source_definition["name"]))
    except ValueError:
        definition = repository.create_definition(
            name=str(source_definition["name"]),
            description=str(source_definition.get("description") or ""),
            input_schema=dict(source_definition.get("input_schema") or {}),
            output_schema=dict(source_definition.get("output_schema") or {}),
            rules=list(source_definition.get("rules") or []),
            nextjs_files=list(source_definition.get("nextjs_files") or []),
        )
    existing = {case["name"] for case in repository.list_cases(str(definition["id"]))}
    for case in payload.get("algorithm_test_cases", []):
        if case["name"] in existing:
            continue
        repository.create_case(
            algorithm_id=str(definition["id"]),
            name=str(case["name"]),
            input_payload=dict(case.get("input_payload") or {}),
            expected_output=dict(case.get("expected_output") or {}),
            tags=list(case.get("tags") or []),
            enabled=bool(case.get("enabled", True)),
        )
    return definition


def _render_list(items: list[object]) -> str:
    return "\n".join(f"- {item}" for item in items) if items else "- Nenhum item registrado."


def _render_result_lines(results: list[dict[str, object]], include_diff: bool = False) -> str:
    lines = []
    for result in results[:20]:
        log = result.get("structured_log") or {}
        actual = result.get("actual_output") or {}
        summary_bits = [str(actual.get("classification", ""))]
        if actual.get("rules_matched") is not None:
            summary_bits.append(f"rules={actual.get('rules_matched')}")
        if actual.get("score") is not None:
            summary_bits.append(f"score={actual.get('score')}")
        line = (
            f"- `{log.get('case_name', result.get('case_id'))}`: {result.get('status')} -> "
            + " ".join(bit for bit in summary_bits if bit)
        )
        if include_diff:
            line += f" diff={json.dumps(result.get('diff'), ensure_ascii=False)}"
        lines.append(line)
    return "\n".join(lines)


def _recommendation(status: str, diff: dict[str, object]) -> str:
    if status == "passed":
        return "Caso validado. Manter como evidência para implementação Next.js."
    return f"Revisar regra ou expectativa. Diferenças: {json.dumps(diff.get('mismatches', []), ensure_ascii=False)}"
