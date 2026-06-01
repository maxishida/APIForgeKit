from __future__ import annotations

import argparse
import json

from core.algorithm_test_lab import (
    AlgorithmTestRepository,
    AlgorithmTestRunner,
    build_algorithm_context,
    ensure_default_algorithms,
    export_algorithm_suite,
)
from core.config import get_settings
from core.database import build_engine, build_session_factory, init_db


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run APIForgeKit algorithm suites from the CLI.")
    parser.add_argument("--suite", default="lead_score", help="Algorithm suite name to run.")
    parser.add_argument("--export", action="store_true", help="Export context markdown and suite JSON after running.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    settings = get_settings()
    engine = build_engine(settings.database_url)
    session_factory = build_session_factory(engine)
    init_db(engine)
    repository = AlgorithmTestRepository(session_factory)
    ensure_default_algorithms(repository)

    definition = repository.get_definition_by_name(args.suite)
    run = AlgorithmTestRunner(repository).run_suite(str(definition["id"]))
    output: dict[str, object] = {"run": run}

    if args.export:
        settings.reports_dir.mkdir(parents=True, exist_ok=True)
        context_path = settings.reports_dir / f"{args.suite}_context.md"
        context_path.write_text(build_algorithm_context(repository), encoding="utf-8")
        suite_path = export_algorithm_suite(repository, str(definition["id"]), settings.reports_dir)
        output["exports"] = {"context": str(context_path), "suite": suite_path}

    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0 if run["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
