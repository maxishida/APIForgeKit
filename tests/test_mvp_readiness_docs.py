from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_mvp_map_and_checklist_document_real_dry_run_legacy_and_blocked_states():
    map_path = ROOT / "docs" / "MVP_100_PERCENT_MAP.md"
    checklist_path = ROOT / "docs" / "MVP_100_PERCENT_CHECKLIST.md"

    assert map_path.exists()
    assert checklist_path.exists()
    map_text = map_path.read_text(encoding="utf-8")
    checklist_text = checklist_path.read_text(encoding="utf-8")

    for expected in ["real_http", "dry_run_contract", "seed_validation", "legacy", "blocked"]:
        assert expected in map_text
    assert "Algorithm Test Lab" in map_text
    assert "Lead Algorithm Lab" in map_text
    assert "Voice/Agents" in map_text
    assert "Context Builder exportando" in checklist_text
    assert "Todo mock/dry-run rotulado" in checklist_text


def test_primary_visible_labels_do_not_use_ambiguous_demo_language():
    home_text = (ROOT / "ui" / "home.py").read_text(encoding="utf-8")
    shell_text = (ROOT / "ui" / "app_shell.py").read_text(encoding="utf-8")
    readme_text = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "Run Demo" not in home_text
    assert "Full demo" not in home_text
    assert "Run Demo" not in shell_text
    assert "modo demo" not in readme_text.lower()
    assert "Seed Validation" in home_text
