from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_skill_is_short_enough_for_acp_prompt_context():
    skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")

    assert len(skill.splitlines()) <= 220
    assert len(skill) <= 9000


def test_skill_keeps_operational_acp_contract():
    skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")

    for expected in [
        "version: 1",
        "No implementation without evidence",
        "ACP Execution Contract",
        "/validate-lead-score",
        "/validate-api-suite whatsapp_validation_pack",
        "/validate-token-cost provider=xai model=grok-4.3 users=10 requests=20",
        "/validate-context-readiness",
        "/validate-voice-roundtrip",
        "/token-cost provider=xai model=grok-4.3 users=10 requests=20",
        "ContentBlock[]",
        "agent_message_chunk",
        "real_http",
        "dry_run_contract",
        "seed_validation",
        "docs/MVP_100_PERCENT_MAP.md",
    ]:
        assert expected in skill
