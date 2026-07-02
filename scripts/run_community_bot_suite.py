from __future__ import annotations

import json
import sys

from core.algorithm_test_lab import (
    AlgorithmTestRepository,
    AlgorithmTestRunner,
    build_algorithm_context,
    ensure_default_algorithms,
    export_algorithm_suite,
    summarize_algorithm_invariants,
)
from core.config import get_settings
from core.database import build_engine, build_session_factory, init_db


def main() -> int:
    settings = get_settings()
    engine = build_engine(settings.database_url)
    session_factory = build_session_factory(engine)
    init_db(engine)
    repository = AlgorithmTestRepository(session_factory)
    ensure_default_algorithms(repository)

    definition = repository.get_definition_by_name("community_bot_engine")
    run = AlgorithmTestRunner(repository).run_suite(str(definition["id"]))
    results = repository.list_results(algorithm_id=str(definition["id"]), limit=50)
    invariants = summarize_algorithm_invariants(results)

    settings.reports_dir.mkdir(parents=True, exist_ok=True)
    context_path = settings.reports_dir / "community_bot_engine_context.md"
    context_path.write_text(
        build_algorithm_context(repository, algorithm_name="community_bot_engine"),
        encoding="utf-8",
    )
    suite_path = export_algorithm_suite(repository, str(definition["id"]), settings.reports_dir)

    output = {
        "run": run,
        "invariants": invariants,
        "exports": {"context": str(context_path), "suite": suite_path},
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0 if run["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())