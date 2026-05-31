from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, JSON, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class LeadTest(Base):
    __tablename__ = "lead_tests"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), index=True)
    lead_name: Mapped[str] = mapped_column(String(255), default="")
    source: Mapped[str] = mapped_column(String(80), index=True)
    message: Mapped[str] = mapped_column(Text)
    budget: Mapped[str] = mapped_column(String(120), default="")
    urgency: Mapped[str] = mapped_column(String(40))
    interest: Mapped[str] = mapped_column(String(40))
    has_phone: Mapped[bool] = mapped_column(Boolean, default=False)
    has_email: Mapped[bool] = mapped_column(Boolean, default=False)
    previous_customer: Mapped[bool] = mapped_column(Boolean, default=False)
    score: Mapped[int] = mapped_column(Integer, index=True)
    classification: Mapped[str] = mapped_column(String(40), index=True)
    confidence: Mapped[float] = mapped_column(Float)
    reasons: Mapped[list[str]] = mapped_column(JSON)
    recommended_action: Mapped[str] = mapped_column(Text)
    nextjs_impact: Mapped[str] = mapped_column(Text)
    raw_input: Mapped[dict[str, object]] = mapped_column(JSON)
    raw_output: Mapped[dict[str, object]] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(40), default="success", index=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat() if self.created_at else "",
            "lead_name": self.lead_name,
            "source": self.source,
            "message": self.message,
            "budget": self.budget,
            "urgency": self.urgency,
            "interest": self.interest,
            "has_phone": self.has_phone,
            "has_email": self.has_email,
            "previous_customer": self.previous_customer,
            "score": self.score,
            "classification": self.classification,
            "confidence": self.confidence,
            "reasons": self.reasons,
            "recommended_action": self.recommended_action,
            "nextjs_impact": self.nextjs_impact,
            "raw_input": self.raw_input,
            "raw_output": self.raw_output,
            "status": self.status,
            "error": self.error,
        }


class TestRun(Base):
    __tablename__ = "test_runs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), index=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    provider: Mapped[str] = mapped_column(String(80), index=True)
    suite_name: Mapped[str] = mapped_column(String(120), index=True)
    status: Mapped[str] = mapped_column(String(40), default="running", index=True)
    phases: Mapped[list[str]] = mapped_column(JSON, default=list)
    summary: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat() if self.created_at else "",
            "completed_at": self.completed_at.isoformat() if self.completed_at else "",
            "provider": self.provider,
            "suite_name": self.suite_name,
            "status": self.status,
            "phases": self.phases,
            "summary": self.summary,
        }


class TestEvent(Base):
    __tablename__ = "test_events"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), index=True)
    run_id: Mapped[str] = mapped_column(String(64), index=True)
    provider: Mapped[str] = mapped_column(String(80), index=True)
    module: Mapped[str] = mapped_column(String(120), index=True)
    test_name: Mapped[str] = mapped_column(String(120), index=True)
    event_type: Mapped[str] = mapped_column(String(120), index=True)
    status: Mapped[str] = mapped_column(String(40), index=True)
    message: Mapped[str] = mapped_column(Text, default="")
    latency_ms: Mapped[float] = mapped_column(Float, default=0)
    tokens: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    cost: Mapped[float] = mapped_column(Float, default=0)
    request: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    response: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommendation: Mapped[str] = mapped_column(Text, default="")

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "event_id": self.id,
            "timestamp": self.created_at.isoformat() if self.created_at else "",
            "created_at": self.created_at.isoformat() if self.created_at else "",
            "run_id": self.run_id,
            "provider": self.provider,
            "module": self.module,
            "test_name": self.test_name,
            "event_type": self.event_type,
            "status": self.status,
            "message": self.message,
            "latency_ms": self.latency_ms,
            "tokens": self.tokens,
            "cost": self.cost,
            "request": self.request,
            "response": self.response,
            "error": self.error,
            "recommendation": self.recommendation,
        }


class ApiRequest(Base):
    __tablename__ = "api_requests"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), index=True)
    run_id: Mapped[str] = mapped_column(String(64), index=True)
    event_id: Mapped[str] = mapped_column(String(64), index=True)
    provider: Mapped[str] = mapped_column(String(80), index=True)
    test_name: Mapped[str] = mapped_column(String(120), index=True)
    endpoint: Mapped[str] = mapped_column(String(255))
    payload: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)


class ApiResponse(Base):
    __tablename__ = "api_responses"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), index=True)
    run_id: Mapped[str] = mapped_column(String(64), index=True)
    event_id: Mapped[str] = mapped_column(String(64), index=True)
    status_code: Mapped[int] = mapped_column(Integer, default=0)
    payload: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    tokens: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    cost: Mapped[float] = mapped_column(Float, default=0)


class VoiceTest(Base):
    __tablename__ = "voice_tests"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), index=True)
    run_id: Mapped[str] = mapped_column(String(64), index=True)
    audio_artifact: Mapped[str] = mapped_column(String(500), default="")
    transcript: Mapped[str] = mapped_column(Text, default="")
    classification: Mapped[str] = mapped_column(String(120), default="")
    metrics: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(40), default="pending", index=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)


class AgentTest(Base):
    __tablename__ = "agent_tests"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), index=True)
    run_id: Mapped[str] = mapped_column(String(64), index=True)
    agent_name: Mapped[str] = mapped_column(String(120), default="")
    task: Mapped[str] = mapped_column(Text, default="")
    events: Mapped[list[dict[str, object]]] = mapped_column(JSON, default=list)
    metrics: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(40), default="pending", index=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)


class ContextExport(Base):
    __tablename__ = "context_exports"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), index=True)
    run_id: Mapped[str] = mapped_column(String(64), index=True)
    format: Mapped[str] = mapped_column(String(20))
    path: Mapped[str] = mapped_column(String(500))
    summary: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)


class AlgorithmDefinition(Base):
    __tablename__ = "algorithm_definitions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), index=True)
    name: Mapped[str] = mapped_column(String(120), index=True, unique=True)
    description: Mapped[str] = mapped_column(Text, default="")
    input_schema: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    output_schema: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    rules: Mapped[list[str]] = mapped_column(JSON, default=list)
    nextjs_files: Mapped[list[str]] = mapped_column(JSON, default=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat() if self.created_at else "",
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
            "output_schema": self.output_schema,
            "rules": self.rules,
            "nextjs_files": self.nextjs_files,
        }


class AlgorithmTestCase(Base):
    __tablename__ = "algorithm_test_cases"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), index=True)
    algorithm_id: Mapped[str] = mapped_column(String(64), index=True)
    name: Mapped[str] = mapped_column(String(180), index=True)
    input_payload: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    expected_output: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, index=True)

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat() if self.created_at else "",
            "algorithm_id": self.algorithm_id,
            "name": self.name,
            "input_payload": self.input_payload,
            "expected_output": self.expected_output,
            "tags": self.tags,
            "enabled": self.enabled,
        }


class AlgorithmTestRun(Base):
    __tablename__ = "algorithm_test_runs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), index=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    algorithm_id: Mapped[str] = mapped_column(String(64), index=True)
    suite_name: Mapped[str] = mapped_column(String(160), default="manual", index=True)
    status: Mapped[str] = mapped_column(String(40), default="running", index=True)
    total_cases: Mapped[int] = mapped_column(Integer, default=0)
    passed: Mapped[int] = mapped_column(Integer, default=0)
    failed: Mapped[int] = mapped_column(Integer, default=0)
    summary: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat() if self.created_at else "",
            "completed_at": self.completed_at.isoformat() if self.completed_at else "",
            "algorithm_id": self.algorithm_id,
            "suite_name": self.suite_name,
            "status": self.status,
            "total_cases": self.total_cases,
            "passed": self.passed,
            "failed": self.failed,
            "summary": self.summary,
        }


class AlgorithmTestResult(Base):
    __tablename__ = "algorithm_test_results"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), index=True)
    run_id: Mapped[str] = mapped_column(String(64), index=True)
    case_id: Mapped[str] = mapped_column(String(64), index=True)
    algorithm_id: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(40), index=True)
    input_payload: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    expected_output: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    actual_output: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    diff: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    latency_ms: Mapped[float] = mapped_column(Float, default=0)
    structured_log: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    recommendation: Mapped[str] = mapped_column(Text, default="")
    nextjs_impact: Mapped[str] = mapped_column(Text, default="")

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat() if self.created_at else "",
            "run_id": self.run_id,
            "case_id": self.case_id,
            "algorithm_id": self.algorithm_id,
            "status": self.status,
            "input_payload": self.input_payload,
            "expected_output": self.expected_output,
            "actual_output": self.actual_output,
            "diff": self.diff,
            "latency_ms": self.latency_ms,
            "structured_log": self.structured_log,
            "recommendation": self.recommendation,
            "nextjs_impact": self.nextjs_impact,
        }
