from pathlib import Path


def test_github_actions_ci_runs_core_validation_commands():
    workflow = Path(".github/workflows/ci.yml")

    assert workflow.exists()
    content = workflow.read_text(encoding="utf-8")
    assert "python -m pytest -q" in content
    assert "python -m compileall app.py core ui agents scripts run_algorithm_lab.py run_acp_prompt.py run_acp_workflow.py run_xai_voice.py" in content
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
    assert '"demo:clean:dry": "node scripts/demo_clean.js dry"' in package_json
    assert '"demo:clean": "node scripts/demo_clean.js apply"' in package_json


def test_demo_clean_uses_the_docker_python_runner_when_host_python_is_unavailable():
    launcher = Path("scripts/demo_clean.js")

    assert launcher.exists()
    content = launcher.read_text(encoding="utf-8")
    assert "python:3.13-slim" in content
    assert "scripts/clean_demo_artifacts.py" in content
    assert "spawnSync('docker', ['info']" in content


def test_validate_mvp_single_command_uses_docker_python_runner():
    script = Path("scripts/validate_mvp.ps1")
    package_json = Path("package.json").read_text(encoding="utf-8")

    assert script.exists()
    content = script.read_text(encoding="utf-8")
    for expected in (
        "docker compose up -d",
        "git diff --check",
        "python:3.13-slim",
        "host.docker.internal",
        "python -m pytest -q",
        "python -m compileall app.py core ui agents scripts run_algorithm_lab.py run_acp_prompt.py run_acp_workflow.py run_xai_voice.py",
        "python run_algorithm_lab.py --suite lead_score --export",
        "python run_acp_workflow.py",
        "python scripts/ui_smoke_local.py",
        "python scripts/clean_demo_artifacts.py",
    ):
        assert expected in content
    assert "$LASTEXITCODE" in content
    assert '"validate:mvp": "powershell -ExecutionPolicy Bypass -File scripts/validate_mvp.ps1"' in package_json
    assert '"validate:mvp:provider": "powershell -ExecutionPolicy Bypass -File scripts/validate_mvp.ps1 -RunProviderSmoke"' in package_json


def test_npm_test_uses_cross_platform_docker_validation_runner():
    package_json = Path("package.json").read_text(encoding="utf-8")
    runner = Path("scripts/test_mvp.js")

    assert runner.exists()
    assert '"test": "npm run test:docker"' in package_json
    assert '"test:docker": "node scripts/test_mvp.js"' in package_json
    content = runner.read_text(encoding="utf-8")
    assert "validate_mvp.ps1" in content
    assert "validate_mvp.sh" in content


def test_validate_mvp_provider_uses_dedicated_responses_smoke_script():
    shell_script = Path("scripts/validate_mvp.ps1").read_text(encoding="utf-8")
    python_script = Path("scripts/xai_responses_smoke.py")

    assert python_script.exists()
    content = python_script.read_text(encoding="utf-8")
    assert "sys.path.insert" in content
    assert "XaiLiveRunner" in content
    assert "_run_responses_basic" in content
    assert "response_id" not in shell_script
    assert "python scripts/xai_responses_smoke.py" in shell_script


def test_validate_mvp_unix_runner_mirrors_windows_validation_flow():
    script = Path("scripts/validate_mvp.sh")
    package_json = Path("package.json").read_text(encoding="utf-8")

    assert script.exists()
    content = script.read_text(encoding="utf-8")
    for expected in (
        "set -euo pipefail",
        "docker compose up -d",
        "git diff --check",
        "python:3.13-slim",
        "host.docker.internal",
        "python -m pytest -q",
        "python -m compileall app.py core ui agents scripts run_algorithm_lab.py run_acp_prompt.py run_acp_workflow.py run_xai_voice.py",
        "python run_algorithm_lab.py --suite lead_score --export",
        "python run_acp_workflow.py",
        "python scripts/ui_smoke_local.py",
        "python scripts/clean_demo_artifacts.py",
        "python scripts/xai_responses_smoke.py",
    ):
        assert expected in content
    assert "MSYS_NO_PATHCONV=1" in content
    assert "cygpath -w" in content
    assert '"validate:mvp:unix": "bash scripts/validate_mvp.sh"' in package_json
    assert '"validate:mvp:provider:unix": "bash scripts/validate_mvp.sh --provider-smoke"' in package_json


def test_validate_mvp_scripts_explain_how_to_recover_when_docker_is_unavailable():
    windows_script = Path("scripts/validate_mvp.ps1").read_text(encoding="utf-8")
    unix_script = Path("scripts/validate_mvp.sh").read_text(encoding="utf-8")

    assert "Docker Desktop/Engine não está pronto" in windows_script
    assert "Docker Desktop/Engine não está pronto" in unix_script


def test_local_ai_context_state_is_ignored_by_git():
    gitignore = Path(".gitignore").read_text(encoding="utf-8")

    assert ".context/" in gitignore
    assert ".codex/" in gitignore


def test_docs_explain_windows_and_unix_mvp_validation_commands():
    combined = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (
            Path("README.md"),
            Path("docs/MVP_TEST_CHECKLIST.md"),
        )
    )

    assert "Windows/PowerShell" in combined
    assert "Linux/macOS" in combined
    assert "npm run validate:mvp:unix" in combined
    assert "npm run validate:mvp:provider:unix" in combined


def test_primary_copy_makes_context_ready_a_hard_gate():
    combined = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (
            Path("ui/home.py"),
            Path("ui/tutorial.py"),
            Path("ui/context_builder.py"),
            Path("docs/MVP_TEST_CHECKLIST.md"),
        )
    )

    assert "Sem Context Builder Ready = não implementar" in combined
    assert "preserve exports if Project Health depends on them" in combined


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
