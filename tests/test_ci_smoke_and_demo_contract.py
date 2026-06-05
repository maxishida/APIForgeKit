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
        "/voice-lab",
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
        "1. Abrir Tutorial",
        "2. Rodar Algorithm Suite",
        "3. Rodar API Contract Dry-run",
        "4. Ver Dashboard",
        "5. Abrir Logs",
        "6. Gerar Context Builder",
        "7. Baixar Evidence Pack",
        "8. Usar contexto com IA",
        "Download .md",
        "Export ZIP",
        "Context Builder",
        "Evidence Pack",
    ):
        assert phrase in content


def test_primary_copy_avoids_ambiguous_seed_and_context_labels():
    combined = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (
            Path("ui/home.py"),
            Path("ui/algorithm_lab.py"),
            Path("docs/IMPLEMENTATION_CHECKLIST.md"),
        )
    )

    assert "Run Full Seed Validation" not in combined
    assert "Executar Suite" not in combined
    assert "Generate AI Context" not in combined
    assert "Run Contract Dry-run" in combined
    assert "Open Context Builder" in combined
