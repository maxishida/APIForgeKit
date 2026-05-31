from __future__ import annotations

import json
from datetime import UTC, datetime
from time import perf_counter
from uuid import uuid4

from sqlalchemy import desc, select
from sqlalchemy.orm import Session, sessionmaker

from core.lead_algorithm import LeadInput, calculate_lead_score
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

    def list_results(self, *, run_id: str | None = None, limit: int = 100) -> list[dict[str, object]]:
        with self.session_factory() as session:
            statement = select(AlgorithmTestResult).order_by(desc(AlgorithmTestResult.created_at)).limit(limit)
            if run_id:
                statement = (
                    select(AlgorithmTestResult)
                    .where(AlgorithmTestResult.run_id == run_id)
                    .order_by(desc(AlgorithmTestResult.created_at))
                    .limit(limit)
                )
            rows = session.scalars(statement).all()
            return [row.to_dict() for row in rows]

    def metrics(self) -> dict[str, object]:
        results = self.list_results(limit=10000)
        runs = self.list_runs(limit=10000)
        passed = len([result for result in results if result["status"] == "passed"])
        failed = len([result for result in results if result["status"] == "failed"])
        latencies = [float(result["latency_ms"] or 0) for result in results]
        return {
            "total_runs": len(runs),
            "total_results": len(results),
            "passed": passed,
            "failed": failed,
            "pass_rate": round((passed / len(results)) * 100, 2) if results else 0,
            "average_latency_ms": round(sum(latencies) / len(latencies), 2) if latencies else 0,
            "latest_run": runs[0] if runs else None,
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
        actual = run_algorithm(str(definition["name"]), dict(case["input_payload"]))
        latency = round((perf_counter() - started) * 1000, 2)
        diff = validate_expected_output(dict(case["expected_output"]), actual)
        status = "passed" if diff["passed"] else "failed"
        recommendation = _recommendation(status, diff)
        structured_log = {
            "id": str(uuid4()),
            "timestamp": datetime.now(UTC).isoformat(),
            "lab": "algorithm_test_lab",
            "algorithm": definition["name"],
            "case_id": case["id"],
            "case_name": case["name"],
            "status": status,
            "latency_ms": latency,
            "input": case["input_payload"],
            "expected": case["expected_output"],
            "actual": actual,
            "diff": diff,
            "recommendation": recommendation,
            "error": None if status == "passed" else "Expected output mismatch",
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
            nextjs_impact="Implementar lógica determinística em /lib/lead-score.ts e cobrir estes casos em testes unitários.",
        )


def ensure_default_algorithms(repository: AlgorithmTestRepository) -> None:
    try:
        definition = repository.get_definition_by_name("lead_score")
    except ValueError:
        definition = repository.create_definition(
            name="lead_score",
            description="Algoritmo determinístico de score e classificação de leads.",
            input_schema=LEAD_SCORE_INPUT_SCHEMA,
            output_schema=LEAD_SCORE_OUTPUT_SCHEMA,
            rules=LEAD_SCORE_RULES,
            nextjs_files=LEAD_SCORE_NEXTJS_FILES,
        )
    existing_names = {case["name"] for case in repository.list_cases(definition["id"])}
    for case in DEFAULT_LEAD_SCORE_CASES:
        if case["name"] not in existing_names:
            repository.create_case(algorithm_id=definition["id"], **case)


def run_algorithm(name: str, input_payload: dict[str, object]) -> dict[str, object]:
    if name != "lead_score":
        raise ValueError(f"Unsupported algorithm: {name}")
    lead = LeadInput(
        lead_name=str(input_payload.get("lead_name", "")),
        source=str(input_payload.get("source", "")),
        message=str(input_payload.get("message", "")),
        budget=str(input_payload.get("budget", "")),
        urgency=str(input_payload.get("urgency", "")),
        interest=str(input_payload.get("interest", "")),
        has_phone=bool(input_payload.get("has_phone", False)),
        has_email=bool(input_payload.get("has_email", False)),
        previous_customer=bool(input_payload.get("previous_customer", False)),
    )
    result = calculate_lead_score(lead).to_dict()
    result["classification"] = result["status"]
    return result


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


def build_algorithm_context(repository: AlgorithmTestRepository, limit: int = 100) -> str:
    definitions = repository.list_definitions()
    results = repository.list_results(limit=limit)
    runs = repository.list_runs(limit=20)
    if not definitions:
        return "# Contexto Técnico - Algorithm Test Lab\n\nNenhum algoritmo cadastrado ainda.\n"
    definition = definitions[0]
    passed = [result for result in results if result["status"] == "passed"]
    failed = [result for result in results if result["status"] == "failed"]
    edge_cases = [result for result in results if any(tag in result["structured_log"].get("case_name", "").lower() for tag in ["inválido", "spam", "sem contato"])]
    if not edge_cases:
        edge_cases = [
            result
            for result in results
            if any(tag in result["expected_output"].get("classification", "") for tag in ["invalid", "cold"])
        ][:10]

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


def _render_list(items: list[object]) -> str:
    return "\n".join(f"- {item}" for item in items) if items else "- Nenhum item registrado."


def _render_result_lines(results: list[dict[str, object]], include_diff: bool = False) -> str:
    lines = []
    for result in results[:20]:
        log = result.get("structured_log") or {}
        actual = result.get("actual_output") or {}
        line = f"- `{log.get('case_name', result.get('case_id'))}`: {result.get('status')} -> {actual.get('classification')} score={actual.get('score')}"
        if include_diff:
            line += f" diff={json.dumps(result.get('diff'), ensure_ascii=False)}"
        lines.append(line)
    return "\n".join(lines)


def _recommendation(status: str, diff: dict[str, object]) -> str:
    if status == "passed":
        return "Caso validado. Manter como evidência para implementação Next.js."
    return f"Revisar regra ou expectativa. Diferenças: {json.dumps(diff.get('mismatches', []), ensure_ascii=False)}"
