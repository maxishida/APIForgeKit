from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from core.lead_algorithm import LeadInput, LeadScoreResult


def append_lead_test_log(
    path: str | Path,
    lead_input: LeadInput,
    output: LeadScoreResult,
    *,
    status: str = "success",
    error: str | None = None,
) -> dict[str, object]:
    log_path = Path(path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "id": output.lead_id,
        "timestamp": datetime.now(UTC).isoformat(),
        "lab": "lead_algorithm_lab",
        "input": lead_input.to_dict(),
        "output": output.to_dict(),
        "status": status,
        "score": output.score,
        "classification": output.status,
        "recommendation": output.recommended_action,
        "nextjs_impact": output.nextjs_impact,
        "error": error,
    }
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
    return payload
