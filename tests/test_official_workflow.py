from core.workflow import OFFICIAL_VALIDATION_JOURNEY, official_journey_titles
from scripts.ui_smoke import SMOKE_PATHS


def test_official_validation_journey_has_the_eight_required_steps():
    assert official_journey_titles() == [
        "Abrir Tutorial",
        "Rodar Algorithm Suite",
        "Rodar API Contract Dry-run",
        "Ver Dashboard",
        "Abrir Logs",
        "Gerar Context Builder",
        "Baixar Evidence Pack",
        "Usar contexto com IA",
    ]
    assert [step["number"] for step in OFFICIAL_VALIDATION_JOURNEY] == list(range(1, 9))


def test_official_validation_journey_routes_are_smoke_tested():
    smoke_routes = set(SMOKE_PATHS)
    smoke_routes.add("/")

    for step in OFFICIAL_VALIDATION_JOURNEY:
        assert step["route"] in smoke_routes
        assert step["cta_label"]
        assert step["evidence"]
        assert step["help"]


def test_official_validation_journey_has_commands_for_automation_steps():
    commands = {step["title"]: step["command"] for step in OFFICIAL_VALIDATION_JOURNEY}

    assert commands["Rodar Algorithm Suite"] == "npm run algorithm:suite"
    assert commands["Gerar Context Builder"] == 'python run_acp_prompt.py "/build-context"'
    assert commands["Baixar Evidence Pack"] == "Export ZIP no Context Builder"
