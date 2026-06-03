from __future__ import annotations

import re
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import desc, select
from sqlalchemy.orm import Session, sessionmaker

from core.models import AcpEventRecord, AcpSessionRecord


SECRET_KEY_PATTERN = re.compile(r"(?i)\b(api[_-]?key|token|authorization|password|secret)=([^\s]+)")
SECRET_FIELD_NAMES = {"authorization", "x-api-key", "api-key", "token", "password", "secret"}


class AcpAuditRepository:
    def __init__(self, session_factory: sessionmaker[Session]):
        self.session_factory = session_factory

    def create_session(self, *, session_id: str, cwd: str, mcp_servers: list[dict[str, object]]) -> dict[str, object]:
        with self.session_factory() as session:
            existing = session.get(AcpSessionRecord, session_id)
            if existing:
                return existing.to_dict()
            row = AcpSessionRecord(
                id=session_id,
                cwd=cwd,
                status="active",
                mcp_servers=_redact(mcp_servers),
                summary={"evidence_mode": "protocol_trace"},
            )
            session.add(row)
            session.commit()
            session.refresh(row)
            return row.to_dict()

    def complete_session(self, session_id: str, *, status: str, summary: dict[str, object] | None = None) -> dict[str, object] | None:
        with self.session_factory() as session:
            row = session.get(AcpSessionRecord, session_id)
            if row is None:
                return None
            row.completed_at = datetime.now(UTC)
            row.status = status
            row.summary = _redact(summary or {})
            session.commit()
            session.refresh(row)
            return row.to_dict()

    def record_event(
        self,
        *,
        session_id: str,
        event_type: str,
        status: str,
        command: str = "",
        message: str = "",
        request: dict[str, object] | None = None,
        response: dict[str, object] | None = None,
        metadata: dict[str, object] | None = None,
        evidence_mode: str = "protocol_trace",
    ) -> dict[str, object]:
        with self.session_factory() as session:
            row = AcpEventRecord(
                id=str(uuid4()),
                session_id=session_id,
                event_type=event_type,
                command=_redact_text(command),
                status=status,
                evidence_mode=evidence_mode,
                message=_redact_text(message),
                request=_redact(request or {}),
                response=_redact(response or {}),
                event_metadata=_redact(metadata or {}),
            )
            session.add(row)
            session.commit()
            session.refresh(row)
            return row.to_dict()

    def list_sessions(self, limit: int = 50) -> list[dict[str, object]]:
        with self.session_factory() as session:
            rows = session.scalars(select(AcpSessionRecord).order_by(desc(AcpSessionRecord.created_at)).limit(limit)).all()
            return [row.to_dict() for row in rows]

    def list_events(self, *, session_id: str | None = None, limit: int = 200) -> list[dict[str, object]]:
        with self.session_factory() as session:
            statement = select(AcpEventRecord).order_by(desc(AcpEventRecord.created_at)).limit(limit)
            if session_id:
                statement = (
                    select(AcpEventRecord)
                    .where(AcpEventRecord.session_id == session_id)
                    .order_by(desc(AcpEventRecord.created_at))
                    .limit(limit)
                )
            rows = session.scalars(statement).all()
            return [row.to_dict() for row in rows]

    def metrics(self) -> dict[str, object]:
        sessions = self.list_sessions(limit=10000)
        events = self.list_events(limit=10000)
        evidence_modes: dict[str, int] = {}
        for event in events:
            mode = str(event.get("evidence_mode") or "protocol_trace")
            evidence_modes[mode] = evidence_modes.get(mode, 0) + 1
        return {
            "total_sessions": len(sessions),
            "total_events": len(events),
            "prompt_events": len([event for event in events if event["event_type"] == "session_prompt"]),
            "successful_prompts": len([event for event in events if event["event_type"] == "prompt_response" and event["status"] == "success"]),
            "failed_prompts": len([event for event in events if event["event_type"] == "prompt_response" and event["status"] == "failed"]),
            "refused_prompts": len([event for event in events if event["event_type"] == "prompt_response" and event["status"] == "refused"]),
            "permission_requests": len([event for event in events if event["event_type"] == "permission_requested"]),
            "evidence_modes": evidence_modes,
        }


def build_acp_context(repository: AcpAuditRepository, limit: int = 100) -> str:
    sessions = repository.list_sessions(limit=20)
    events = repository.list_events(limit=limit)
    metrics = repository.metrics()
    event_lines = []
    for event in events[:30]:
        event_lines.append(
            f"- `{event['event_type']}` session={event['session_id']} command=`{event.get('command') or 'n/a'}` "
            f"status={event['status']} mode={event['evidence_mode']} message={event.get('message') or 'n/a'}"
        )
    session_lines = [
        f"- `{session['id']}` status={session['status']} cwd={session['cwd']} mcp_servers={len(session.get('mcp_servers') or [])}"
        for session in sessions[:20]
    ]
    return f"""# Contexto Técnico - ACP Skill Executor

Gerado em: {datetime.now(UTC).isoformat()}

## Objetivo

Registrar como clientes ACP/CLI/IDE executaram o contrato operacional do `SKILL.md`.

## Métricas

- Sessões: {metrics['total_sessions']}
- Eventos: {metrics['total_events']}
- Prompts: {metrics['prompt_events']}
- Prompts com sucesso: {metrics['successful_prompts']}
- Prompts recusados: {metrics['refused_prompts']}
- Pedidos de permissão: {metrics['permission_requests']}
- Modos de evidência: {_render_modes(metrics['evidence_modes'])}

## Sessões

{chr(10).join(session_lines) if session_lines else "- Nenhuma sessão ACP registrada ainda."}

## Eventos Relevantes

{chr(10).join(event_lines) if event_lines else "- Nenhum evento ACP registrado ainda."}

## Recomendações

- Use ACP como executor de validação, não como gerador direto de código.
- Trate `protocol_trace` como evidência do fluxo de agente e `blocked` como gate de permissão preservado.
- Combine este contexto com Algorithm Test Lab, Generic API Lab e Token Calculator antes de pedir implementação.
"""


def _render_modes(modes: dict[str, object]) -> str:
    if not modes:
        return "none"
    return ", ".join(f"{mode}={count}" for mode, count in sorted(modes.items()))


def _redact(value):
    if isinstance(value, dict):
        redacted = {}
        for key, item in value.items():
            if str(key).lower() in SECRET_FIELD_NAMES:
                redacted[key] = "***REDACTED***"
            else:
                redacted[key] = _redact(item)
        return redacted
    if isinstance(value, list):
        return [_redact(item) for item in value]
    if isinstance(value, str):
        return _redact_text(value)
    return value


def _redact_text(value: str) -> str:
    return SECRET_KEY_PATTERN.sub(lambda match: f"{match.group(1)}=***REDACTED***", str(value))
