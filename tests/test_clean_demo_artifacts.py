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
