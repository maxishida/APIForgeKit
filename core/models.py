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
