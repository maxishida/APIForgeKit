from pathlib import Path

from ui import tutorial


ROOT = Path(__file__).resolve().parents[1]


def test_system_diagram_doc_contains_full_acp_to_evidence_flow():
    path = ROOT / "docs" / "SYSTEM_DIAGRAM.md"

    assert path.exists()
    text = path.read_text(encoding="utf-8")

    assert "```mermaid" in text
    for expected in [
        "ACP Client / CLI / IDE",
        "agents/acp_agent.py",
        "SKILL.md Decision Gates",
        "SkillExecutor",
        "Algorithm Test Lab",
        "Generic API Lab",
        "Token Calculator",
        "Provider/xAI Validation",
        "PostgreSQL Evidence Store",
        "Dashboard / Logs / Context Builder",
        "Evidence Pack",
    ]:
        assert expected in text


def test_tutorial_exposes_system_diagram_lanes():
    labels = [lane["label"] for lane in tutorial.SYSTEM_DIAGRAM_LANES]

    assert labels == [
        "ACP Client / CLI / IDE",
        "SKILL.md Gates",
        "Validation Labs",
        "PostgreSQL Evidence",
        "Dashboard + Context",
        "Evidence Pack",
    ]
    assert any("Token Calculator" in lane["detail"] for lane in tutorial.SYSTEM_DIAGRAM_LANES)
