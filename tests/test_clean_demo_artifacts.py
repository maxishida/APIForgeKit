import json
import subprocess
import sys
from pathlib import Path

from scripts.clean_demo_artifacts import collect_demo_artifacts, clean_demo_artifacts


def test_clean_demo_artifacts_dry_run_does_not_remove_files(tmp_path):
    env_file = tmp_path / ".env"
    report = tmp_path / "exports" / "reports" / "report.md"
    cache_file = tmp_path / "__pycache__" / "module.pyc"
    for path in (env_file, report, cache_file):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("keep", encoding="utf-8")

    result = clean_demo_artifacts(tmp_path, apply=False)

    assert result["mode"] == "dry_run"
    assert env_file.exists()
    assert report.exists()
    assert cache_file.exists()
    assert str(report) in result["files"]
    assert str(cache_file.parent) in result["directories"]
    assert str(env_file) not in result["files"]


def test_clean_demo_artifacts_apply_preserves_env_tests_and_gitkeep(tmp_path):
    env_file = tmp_path / ".env"
    test_file = tmp_path / "tests" / "test_keep.py"
    gitkeep = tmp_path / "exports" / "reports" / ".gitkeep"
    report = tmp_path / "exports" / "reports" / "report.md"
    log_file = tmp_path / "exports" / "logs" / "events.jsonl"
    cache_file = tmp_path / "pkg" / "__pycache__" / "module.pyc"
    for path in (env_file, test_file, gitkeep, report, log_file, cache_file):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("value", encoding="utf-8")

    result = clean_demo_artifacts(tmp_path, apply=True)

    assert result["mode"] == "apply"
    assert env_file.exists()
    assert test_file.exists()
    assert gitkeep.exists()
    assert not report.exists()
    assert not log_file.exists()
    assert not cache_file.parent.exists()


def test_collect_demo_artifacts_only_targets_expected_paths(tmp_path):
    tracked_like = tmp_path / "README.md"
    hidden_env = tmp_path / ".env"
    report = tmp_path / "exports" / "reports" / "report.md"
    pytest_cache = tmp_path / ".pytest_cache"
    for path in (tracked_like, hidden_env, report):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("value", encoding="utf-8")
    pytest_cache.mkdir()

    artifacts = collect_demo_artifacts(tmp_path)

    assert str(report) in artifacts["files"]
    assert str(pytest_cache) in artifacts["directories"]
    assert str(tracked_like) not in artifacts["files"]
    assert str(hidden_env) not in artifacts["files"]


def test_cleanup_collects_all_generated_outputs_and_test_caches(tmp_path):
    report = tmp_path / "exports" / "reports" / "report.md"
    context = tmp_path / "exports" / "contexts" / "context.json"
    blueprint = tmp_path / "exports" / "blueprints" / "blueprint.md"
    jsonl_log = tmp_path / "logs" / "lead_tests.jsonl"
    output = tmp_path / "outputs" / "run.json"
    test_cache = tmp_path / "tests" / "__pycache__" / "test_clean.pyc"
    for path in (report, context, blueprint, jsonl_log, output, test_cache):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("generated", encoding="utf-8")

    artifacts = collect_demo_artifacts(tmp_path)

    for path in (report, context, blueprint, jsonl_log, output):
        assert str(path) in artifacts["files"]
    assert str(test_cache.parent) in artifacts["directories"]
    assert artifacts["file_count"] == 5
    assert artifacts["directory_count"] == 1
    assert artifacts["total_bytes"] == 45


def test_cleanup_apply_removes_generated_test_cache_without_removing_test_source(tmp_path):
    test_source = tmp_path / "tests" / "test_source.py"
    test_cache = tmp_path / "tests" / "__pycache__" / "test_source.pyc"
    env_file = tmp_path / ".env"
    context_state = tmp_path / ".context" / "state.json"
    runtime_log = tmp_path / "logs" / "lead_tests.jsonl"
    output = tmp_path / "outputs" / "run.json"
    for path in (test_source, test_cache, env_file, context_state, runtime_log, output):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("keep" if path in (test_source, env_file, context_state) else "generated", encoding="utf-8")

    result = clean_demo_artifacts(tmp_path, apply=True)

    assert result["mode"] == "apply"
    assert test_source.exists()
    assert env_file.exists()
    assert context_state.exists()
    assert not test_cache.parent.exists()
    assert not runtime_log.exists()
    assert not output.exists()


def test_cleanup_cli_returns_compact_summary_unless_verbose(tmp_path):
    report = tmp_path / "exports" / "reports" / "report.md"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("generated", encoding="utf-8")

    summary = subprocess.run(
        [sys.executable, "scripts/clean_demo_artifacts.py", "--root", str(tmp_path)],
        check=True,
        capture_output=True,
        text=True,
    )
    verbose = subprocess.run(
        [sys.executable, "scripts/clean_demo_artifacts.py", "--root", str(tmp_path), "--verbose"],
        check=True,
        capture_output=True,
        text=True,
    )

    assert json.loads(summary.stdout) == {
        "mode": "dry_run",
        "directory_count": 0,
        "file_count": 1,
        "total_bytes": len("generated"),
    }
    assert str(report) in json.loads(verbose.stdout)["files"]
