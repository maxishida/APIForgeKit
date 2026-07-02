from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.algorithm_test_lab import (
    AlgorithmTestRepository,
    AlgorithmTestRunner,
    ensure_default_algorithms,
    export_algorithm_suite,
    summarize_algorithm_invariants,
)
from core.community_pipeline import COMMUNITY_ALGORITHMS, build_community_pipeline_context, community_pipeline_metrics
from core.config import get_settings
from core.database import build_engine, build_session_factory, init_db


def _run_suite(repository: AlgorithmTestRepository, algorithm_name: str) -> dict[str, object]:
    definition = repository.get_definition_by_name(algorithm_name)
    run = AlgorithmTestRunner(repository).run_suite(str(definition["id"]))
    results = repository.list_results(algorithm_id=str(definition["id"]), limit=200)
    invariants = summarize_algorithm_invariants(results)
    return {
        "algorithm": algorithm_name,
        "run": run,
        "invariants": invariants,
        "cases": len(repository.list_cases(str(definition["id"]))),
    }


def main() -> int:
    settings = get_settings()
    engine = build_engine(settings.database_url)
    session_factory = build_session_factory(engine)
    init_db(engine)
    repository = AlgorithmTestRepository(session_factory)
    ensure_default_algorithms(repository)

    suites = [_run_suite(repository, name) for name in COMMUNITY_ALGORITHMS]
    metrics = community_pipeline_metrics(repository)

    settings.reports_dir.mkdir(parents=True, exist_ok=True)
    context_path = settings.reports_dir / "community_pipeline_context.md"
    context_path.write_text(build_community_pipeline_context(repository), encoding="utf-8")

    exports: dict[str, str] = {"context": str(context_path)}
    for suite in suites:
        algorithm_name = str(suite["algorithm"])
        definition = repository.get_definition_by_name(algorithm_name)
        exports[algorithm_name] = export_algorithm_suite(repository, str(definition["id"]), settings.reports_dir)

    all_passed = all(str(suite["run"]["status"]) == "passed" for suite in suites)
    output = {
        "status": "passed" if all_passed and metrics["status"] == "Ready" else "failed",
        "metrics": metrics,
        "suites": suites,
        "exports": exports,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0 if output["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())