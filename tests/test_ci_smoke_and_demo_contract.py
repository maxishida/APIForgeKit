from pathlib import Path


def test_github_actions_ci_runs_core_validation_commands():
    workflow = Path(".github/workflows/ci.yml")

    assert workflow.exists()
    content = workflow.read_text(encoding="utf-8")
    assert "python -m pytest -q" in content
    assert "python -m compileall app.py core ui agents run_algorithm_lab.py run_acp_prompt.py" in content
    assert "git diff --check" in content


def test_ui_smoke_script_and_npm_helper_cover_main_pages():
    script = Path("scripts/ui_smoke.py")
    package_json = Path("package.json").read_text(encoding="utf-8")

    assert script.exists()
    content = script.read_text(encoding="utf-8")
    for route in (
        "/",
        "/tutorial",
        "/token-calculator",
        "/algorithm-test-lab",
        "/api-test-lab",
        "/context-builder",
        "/logs",
        "/live-dashboard",
    ):
        assert route in content
    assert '"ui:smoke": "python scripts/ui_smoke.py"' in package_json


def test_demo_script_documents_evidence_first_walkthrough():
    demo_doc = Path("docs/DEMO_SCRIPT.md")

    assert demo_doc.exists()
    content = demo_doc.read_text(encoding="utf-8")
    for phrase in (
        "npm run db",
        "/tutorial",
        "/token-calculator",
        "/validate-lead-score",
        "Context Builder",
        "Evidence Pack",
    ):
        assert phrase in content
