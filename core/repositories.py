from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime
from typing import Iterable

from sqlalchemy import desc, select
from sqlalchemy.orm import Session, sessionmaker

from core.lead_algorithm import LeadInput, LeadScoreResult
from core.models import LeadTest


class LeadTestRepository:
    def __init__(self, session_factory: sessionmaker[Session]):
        self.session_factory = session_factory

    def create_from_result(
        self,
        lead_input: LeadInput,
        output: LeadScoreResult,
        *,
        status: str = "success",
        error: str | None = None,
    ) -> LeadTest:
        with self.session_factory() as session:
            row = LeadTest(
                id=output.lead_id,
                lead_name=lead_input.lead_name,
                source=lead_input.source,
                message=lead_input.message,
                budget=lead_input.budget,
                urgency=lead_input.urgency,
                interest=lead_input.interest,
                has_phone=lead_input.has_phone,
                has_email=lead_input.has_email,
                previous_customer=lead_input.previous_customer,
                score=output.score,
                classification=output.status,
                confidence=output.confidence,
                reasons=output.reasons,
                recommended_action=output.recommended_action,
                nextjs_impact=output.nextjs_impact,
                raw_input=lead_input.to_dict(),
                raw_output=output.to_dict(),
                status=status,
                error=error,
            )
            session.add(row)
            session.commit()
            session.refresh(row)
            return row

    def list_recent(self, limit: int = 100) -> list[dict[str, object]]:
        with self.session_factory() as session:
            rows = session.scalars(select(LeadTest).order_by(desc(LeadTest.created_at)).limit(limit)).all()
            return [row.to_dict() for row in rows]

    def metrics(self) -> dict[str, object]:
        rows = self.list_recent(limit=5000)
        total = len(rows)
        classifications = Counter(str(row["classification"]) for row in rows)
        sources = Counter(str(row["source"]) for row in rows)
        avg_score = round(sum(int(row["score"]) for row in rows) / total, 2) if total else 0
        latest = rows[0] if rows else None
        channel_scores: dict[str, list[int]] = defaultdict(list)
        daily_counts: dict[str, int] = defaultdict(int)
        daily_avg_scores: dict[str, list[int]] = defaultdict(list)
        for row in rows:
            channel_scores[str(row["source"])].append(int(row["score"]))
            created_at = str(row["created_at"])[:10]
            daily_counts[created_at] += 1
            daily_avg_scores[created_at].append(int(row["score"]))
        return {
            "total": total,
            "classifications": dict(classifications),
            "sources": dict(sources),
            "average_score": avg_score,
            "latest": latest,
            "channel_average_scores": {
                source: round(sum(scores) / len(scores), 2) for source, scores in channel_scores.items()
            },
            "daily_counts": dict(sorted(daily_counts.items())),
            "daily_average_scores": {
                day: round(sum(scores) / len(scores), 2) for day, scores in sorted(daily_avg_scores.items())
            },
        }


def filter_records(
    records: Iterable[dict[str, object]],
    *,
    source: str | None = None,
    classification: str | None = None,
    status: str | None = None,
    min_score: int | None = None,
    max_score: int | None = None,
    query: str | None = None,
) -> list[dict[str, object]]:
    result = []
    normalized_query = (query or "").strip().lower()
    for record in records:
        score = int(record.get("score", 0))
        if source and record.get("source") != source:
            continue
        if classification and record.get("classification") != classification:
            continue
        if status and record.get("status") != status:
            continue
        if min_score is not None and score < min_score:
            continue
        if max_score is not None and score > max_score:
            continue
        if normalized_query and normalized_query not in str(record.get("message", "")).lower():
            continue
        result.append(record)
    return result
