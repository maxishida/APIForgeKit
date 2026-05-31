from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session, sessionmaker

from core.models import AgentTest, ApiRequest, ApiResponse, ContextExport, TestEvent, TestRun, VoiceTest


@dataclass(frozen=True)
class ObservabilityEventInput:
    run_id: str
    provider: str
    module: str
    test_name: str
    event_type: str
    status: str
    message: str
    latency_ms: float = 0
    tokens: dict[str, object] = field(default_factory=dict)
    cost: float = 0
    request: dict[str, object] = field(default_factory=dict)
    response: dict[str, object] = field(default_factory=dict)
    error: str | None = None
    recommendation: str = ""


class ObservabilityRepository:
    def __init__(self, session_factory: sessionmaker[Session]):
        self.session_factory = session_factory

    def start_run(self, provider: str, suite_name: str, phases: list[str]) -> dict[str, object]:
        with self.session_factory() as session:
            row = TestRun(
                id=str(uuid4()),
                provider=provider,
                suite_name=suite_name,
                phases=phases,
                status="running",
                summary={},
            )
            session.add(row)
            session.commit()
            session.refresh(row)
            return row.to_dict()

    def finish_run(self, run_id: str, status: str, summary: dict[str, object] | None = None) -> dict[str, object]:
        with self.session_factory() as session:
            row = session.get(TestRun, run_id)
            if row is None:
                raise ValueError(f"Unknown run_id: {run_id}")
            row.status = status
            row.completed_at = datetime.now(UTC)
            row.summary = summary or {}
            session.commit()
            session.refresh(row)
            return row.to_dict()

    def record_event(self, event: ObservabilityEventInput) -> dict[str, object]:
        with self.session_factory() as session:
            row = TestEvent(id=str(uuid4()), **asdict(event))
            session.add(row)
            session.commit()
            session.refresh(row)
            return row.to_dict()

    def record_api_request(
        self,
        run_id: str,
        event_id: str,
        provider: str,
        test_name: str,
        endpoint: str,
        payload: dict[str, object],
    ) -> dict[str, object]:
        with self.session_factory() as session:
            row = ApiRequest(
                id=str(uuid4()),
                run_id=run_id,
                event_id=event_id,
                provider=provider,
                test_name=test_name,
                endpoint=endpoint,
                payload=payload,
            )
            session.add(row)
            session.commit()
            return {"id": row.id, "endpoint": endpoint}

    def record_api_response(
        self,
        run_id: str,
        event_id: str,
        status_code: int,
        payload: dict[str, object],
        tokens: dict[str, object] | None = None,
        cost: float = 0,
    ) -> dict[str, object]:
        with self.session_factory() as session:
            row = ApiResponse(
                id=str(uuid4()),
                run_id=run_id,
                event_id=event_id,
                status_code=status_code,
                payload=payload,
                tokens=tokens or {},
                cost=cost,
            )
            session.add(row)
            session.commit()
            return {"id": row.id, "status_code": status_code}

    def record_voice_test(
        self,
        run_id: str,
        *,
        audio_artifact: str = "",
        transcript: str = "",
        classification: str = "",
        metrics: dict[str, object] | None = None,
        status: str = "pending",
        error: str | None = None,
    ) -> dict[str, object]:
        with self.session_factory() as session:
            row = VoiceTest(
                id=str(uuid4()),
                run_id=run_id,
                audio_artifact=audio_artifact,
                transcript=transcript,
                classification=classification,
                metrics=metrics or {},
                status=status,
                error=error,
            )
            session.add(row)
            session.commit()
            return {"id": row.id, "status": status}

    def record_agent_test(
        self,
        run_id: str,
        *,
        agent_name: str,
        task: str,
        events: list[dict[str, object]] | None = None,
        metrics: dict[str, object] | None = None,
        status: str = "pending",
        error: str | None = None,
    ) -> dict[str, object]:
        with self.session_factory() as session:
            row = AgentTest(
                id=str(uuid4()),
                run_id=run_id,
                agent_name=agent_name,
                task=task,
                events=events or [],
                metrics=metrics or {},
                status=status,
                error=error,
            )
            session.add(row)
            session.commit()
            return {"id": row.id, "status": status}

    def record_context_export(self, run_id: str, format: str, path: str, summary: dict[str, object]) -> dict[str, object]:
        with self.session_factory() as session:
            row = ContextExport(id=str(uuid4()), run_id=run_id, format=format, path=path, summary=summary)
            session.add(row)
            session.commit()
            return {"id": row.id, "path": path}

    def list_runs(self, limit: int = 50) -> list[dict[str, object]]:
        with self.session_factory() as session:
            rows = session.scalars(select(TestRun).order_by(desc(TestRun.created_at)).limit(limit)).all()
            return [row.to_dict() for row in rows]

    def list_events(self, limit: int = 200, run_id: str | None = None) -> list[dict[str, object]]:
        with self.session_factory() as session:
            statement = select(TestEvent).order_by(desc(TestEvent.created_at)).limit(limit)
            if run_id:
                statement = select(TestEvent).where(TestEvent.run_id == run_id).order_by(desc(TestEvent.created_at)).limit(limit)
            rows = session.scalars(statement).all()
            return [row.to_dict() for row in rows]

    def metrics(self) -> dict[str, object]:
        with self.session_factory() as session:
            total_runs = session.scalar(select(func.count()).select_from(TestRun)) or 0
            active = session.scalar(select(func.count()).select_from(TestRun).where(TestRun.status == "running")) or 0
            success = session.scalar(select(func.count()).select_from(TestRun).where(TestRun.status == "success")) or 0
            failures = session.scalar(select(func.count()).select_from(TestRun).where(TestRun.status == "failed")) or 0
            requests = session.scalar(select(func.count()).select_from(ApiRequest)) or 0
            avg_latency = session.scalar(select(func.avg(TestEvent.latency_ms))) or 0
            total_cost = session.scalar(select(func.sum(ApiResponse.cost))) or 0
            completed_runs = session.scalars(
                select(TestRun).where(TestRun.completed_at.is_not(None)).order_by(desc(TestRun.created_at)).limit(200)
            ).all()
            response_rows = session.scalars(select(ApiResponse)).all()
            tokens = 0
            for row in response_rows:
                usage = row.tokens or {}
                for key in ("total_tokens", "total", "input_tokens", "output_tokens"):
                    value = usage.get(key)
                    if isinstance(value, (int, float)):
                        tokens += int(value)
            durations = [
                (row.completed_at - row.created_at).total_seconds() * 1000
                for row in completed_runs
                if row.completed_at and row.created_at
            ]
            average_time = sum(durations) / len(durations) if durations else 0
        return {
            "total_tests": int(total_runs),
            "active_tests": int(active),
            "success": int(success),
            "failures": int(failures),
            "requests": int(requests),
            "average_latency_ms": round(float(avg_latency), 2),
            "average_time_ms": round(float(average_time), 2),
            "tokens": tokens,
            "estimated_cost": round(float(total_cost), 6),
        }


def build_live_context(runs: list[dict[str, object]], events: list[dict[str, object]]) -> str:
    successes = [event for event in events if event.get("status") == "success"]
    failures = [event for event in events if event.get("status") == "failed"]
    payloads = "\n".join(
        f"- `{event.get('test_name')}` request={json.dumps(event.get('request', {}), ensure_ascii=False)}"
        for event in events[:12]
        if event.get("request")
    ) or "- Nenhum payload registrado ainda."
    limitations = "\n".join(
        f"- `{event.get('test_name')}`: {event.get('error')}" for event in failures if event.get("error")
    ) or "- Nenhuma limitação bloqueante registrada."
    recommendations = "\n".join(
        f"- {event.get('recommendation')}" for event in events if event.get("recommendation")
    ) or "- Continuar validando endpoints com logs estruturados antes de implementar."
    return f"""# Contexto Técnico — API Observability Lab

## O que foi testado

- Runs analisadas: {len(runs)}
- Eventos analisados: {len(events)}
- Módulos: {", ".join(sorted({str(event.get("module")) for event in events if event.get("module")})) or "nenhum"}

## O que funcionou

{chr(10).join(f"- `{event.get('module')}/{event.get('test_name')}`: {event.get('message')}" for event in successes[:20]) or "- Nenhum sucesso registrado."}

## O que falhou

{chr(10).join(f"- `{event.get('module')}/{event.get('test_name')}`: {event.get('error') or event.get('message')}" for event in failures[:20]) or "- Nenhuma falha registrada."}

## Payloads corretos

{payloads}

## Latências

- Latência média observada: {round(sum(float(event.get("latency_ms") or 0) for event in events) / len(events), 2) if events else 0} ms

## Limitações encontradas

{limitations}

## Recomendações

{recommendations}

## Impacto para implementação futura

Não iniciar implementação de negócio ainda. Usar estes logs para definir contratos, retries, timeout, telemetria, custo e tratamento de erros.
"""


def build_report_payload(runs: list[dict[str, object]], events: list[dict[str, object]]) -> dict[str, object]:
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "summary": {
            "total_runs": len(runs),
            "total_events": len(events),
            "success_events": len([event for event in events if event.get("status") == "success"]),
            "failed_events": len([event for event in events if event.get("status") == "failed"]),
        },
        "runs": runs,
        "events": events,
        "context": build_live_context(runs, events),
    }


def export_observability_report(
    output_dir: str | Path,
    runs: list[dict[str, object]],
    events: list[dict[str, object]],
) -> dict[str, str]:
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    payload = build_report_payload(runs, events)
    json_path = directory / f"observability_report_{stamp}.json"
    md_path = directory / f"observability_report_{stamp}.md"
    html_path = directory / f"observability_report_{stamp}.html"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(payload["context"], encoding="utf-8")
    html_path.write_text(
        "<!doctype html><html><head><meta charset='utf-8'><title>APIForgeKit Observability Report</title>"
        "<style>body{background:#0A0F1C;color:#F9FAFB;font-family:Inter,Arial;padding:32px}code{color:#00D4FF}</style>"
        f"</head><body><pre>{payload['context']}</pre></body></html>",
        encoding="utf-8",
    )
    return {"json": str(json_path), "markdown": str(md_path), "html": str(html_path)}
