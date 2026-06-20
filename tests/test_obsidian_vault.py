import json
import subprocess
import sys
from pathlib import Path

from core.obsidian_vault import build_repository_snapshot, sync_vault, validate_vault


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_sync_creates_map_resume_note_and_canonical_hubs(tmp_path):
    result = sync_vault(vault_path=tmp_path, repo_root=PROJECT_ROOT)

    project_map = tmp_path / "00 - Mapa do Projeto.md"
    resume_note = tmp_path / "00 - Retomar Agora.md"
    assert result["status"] == "ok"
    assert project_map.exists()
    assert resume_note.exists()
    assert (tmp_path / "06 - Engenharia" / "Arquitetura do Sistema.md").exists()
    assert (tmp_path / "06 - Engenharia" / "Gerado" / "APIForgeKit - Snapshot de Arquitetura.md").exists()
    assert "[[Arquitetura do Sistema]]" in project_map.read_text(encoding="utf-8")
    assert "[[00 - Mapa do Projeto]]" in resume_note.read_text(encoding="utf-8")


def test_sync_replaces_only_generated_text_and_preserves_user_notes(tmp_path):
    resume = tmp_path / "00 - Retomar Agora.md"
    resume.write_text(
        "<!-- @generated:start -->old generated text<!-- @generated:end -->\n\n## Notas da sessão\nNão apagar.",
        encoding="utf-8",
    )

    sync_vault(vault_path=tmp_path, repo_root=PROJECT_ROOT)

    content = resume.read_text(encoding="utf-8")
    assert "Não apagar." in content
    assert "old generated text" not in content
    assert "<!-- @generated:start -->" in content
    assert "<!-- @generated:end -->" in content


def test_validate_vault_reports_unresolved_wikilinks(tmp_path):
    (tmp_path / "00 - Mapa do Projeto.md").write_text("[[Nota Ausente]]", encoding="utf-8")

    result = validate_vault(vault_path=tmp_path)

    assert result["valid"] is False
    assert result["broken_links"] == ["Nota Ausente"]


def test_second_sync_is_idempotent_and_does_not_read_environment_values(tmp_path, monkeypatch):
    monkeypatch.setenv("XAI_API_KEY", "must-not-appear-in-vault")

    sync_vault(vault_path=tmp_path, repo_root=PROJECT_ROOT)
    manifest = tmp_path / ".apiforgekit-vault-manifest.json"
    first_manifest = manifest.read_text(encoding="utf-8")
    second = sync_vault(vault_path=tmp_path, repo_root=PROJECT_ROOT)

    content = "\n".join(path.read_text(encoding="utf-8") for path in tmp_path.rglob("*.md"))
    assert second["status"] == "ok"
    assert second["updated"] == []
    assert manifest.read_text(encoding="utf-8") == first_manifest
    assert "must-not-appear-in-vault" not in content


def test_sync_cli_creates_and_validates_vault(tmp_path):
    sync = subprocess.run(
        [sys.executable, "scripts/sync_obsidian_vault.py", "sync", "--vault", str(tmp_path)],
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    validation = subprocess.run(
        [sys.executable, "scripts/sync_obsidian_vault.py", "validate", "--vault", str(tmp_path)],
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert json.loads(sync.stdout)["status"] == "ok"
    assert json.loads(validation.stdout)["valid"] is True


def test_sync_requires_existing_vault_directory(tmp_path):
    missing_vault = tmp_path / "does-not-exist"

    result = sync_vault(vault_path=missing_vault, repo_root=PROJECT_ROOT)

    assert result["status"] == "error"
    assert "does not exist" in result["error"]
    assert not missing_vault.exists()


def test_repository_snapshot_accepts_safe_git_metadata_from_environment(monkeypatch):
    monkeypatch.setenv("APIFORGEKIT_GIT_BRANCH", "main")
    monkeypatch.setenv("APIFORGEKIT_GIT_COMMIT", "abc1234")
    monkeypatch.setenv("APIFORGEKIT_GIT_SUBJECT", "feat: synced context")

    snapshot = build_repository_snapshot(PROJECT_ROOT)

    assert snapshot["branch"] == "main"
    assert snapshot["commit"] == "abc1234"
    assert snapshot["latest_subject"] == "feat: synced context"


def test_npm_obsidian_commands_use_the_docker_launcher():
    package = json.loads((PROJECT_ROOT / "package.json").read_text(encoding="utf-8"))
    launcher = (PROJECT_ROOT / "scripts" / "obsidian_vault.js").read_text(encoding="utf-8")

    assert package["scripts"]["obsidian:sync"] == "node scripts/obsidian_vault.js sync"
    assert package["scripts"]["obsidian:validate"] == "node scripts/obsidian_vault.js validate"
    assert "docker" in launcher
    assert '"/vault"' in launcher
