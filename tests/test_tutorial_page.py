from pathlib import Path

from ui import tutorial


ROOT = Path(__file__).resolve().parents[1]


def test_tutorial_reads_docs_tutorial_file():
    assert tutorial.TUTORIAL_DOC_PATH == ROOT / "docs" / "OPEN_SOURCE_TUTORIAL.md"
    assert tutorial.TUTORIAL_DOC_PATH.exists()


def test_tutorial_sections_explain_mvp_workflow_and_cli_harness():
    titles = [section["title"] for section in tutorial.TUTORIAL_SECTIONS]
    body = "\n".join(section["body"] for section in tutorial.TUTORIAL_SECTIONS)

    assert "1. Evidence First" in titles
    assert "2. Algorithm Test Lab" in titles
    assert "3. ACP Harness" in titles
    assert "python run_acp_prompt.py" in body
    assert "Teste -> Log -> PostgreSQL -> Dashboard -> Context Builder -> Evidence Pack" in body
