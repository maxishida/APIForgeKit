from ui import token_calculator


def test_token_calculator_declares_four_step_wizard_contract():
    labels = [step["label"] for step in token_calculator.TOKEN_WIZARD_STEPS]

    assert labels == [
        "1. Pricing Source",
        "2. Usage Volume",
        "3. Token Shape",
        "4. Review & Save",
    ]


def test_token_calculator_exposes_pricing_modes_and_context_savings_copy():
    assert token_calculator.PRICING_MODE_OPTIONS == {
        "seeded_estimate": "Seeded estimate",
        "docs_verified": "Docs verified",
    }
    wizard_text = " ".join(step["help"] for step in token_calculator.TOKEN_WIZARD_STEPS)
    assert "Context Builder savings" in wizard_text
    assert "docs_verified" in wizard_text


def test_token_calculator_declares_pricing_audit_fields():
    assert token_calculator.PRICING_AUDIT_FIELDS == [
        "pricing_verified_at",
        "pricing_verified_source_url",
    ]
    wizard_text = " ".join(step["help"] for step in token_calculator.TOKEN_WIZARD_STEPS)
    assert "verification timestamp" in wizard_text
    assert "source URL" in wizard_text
