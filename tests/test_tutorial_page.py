from pathlib import Path

from ui import tutorial


ROOT = Path(__file__).resolve().parents[1]


def test_tutorial_reads_docs_tutorial_file():
    assert tutorial.TUTORIAL_DOC_PATH == ROOT / "docs" / "OPEN_SOURCE_TUTORIAL.md"
    assert tutorial.TUTORIAL_DOC_PATH.exists()


def test_tutorial_sections_explain_mvp_workflow_and_cli_harness():
    titles = [section["title"] for section in tutorial.TUTORIAL_SECTIONS]
    body = "\n".join(section["body"] for section in tutorial.TUTORIAL_SECTIONS)

    assert titles == [
        "1. Abrir Tutorial",
        "2. Rodar Algorithm Suite",
        "3. Rodar API Contract Dry-run",
        "4. Ver Dashboard",
        "5. Abrir Logs",
        "6. Gerar Context Builder",
        "7. Baixar Evidence Pack",
        "8. Usar contexto com IA",
    ]
    assert "python run_acp_prompt.py" in body
    assert "seed_validation" in body
    assert "dry_run_contract" in body
    assert "Download .md" in body
    assert "Export ZIP" in body
