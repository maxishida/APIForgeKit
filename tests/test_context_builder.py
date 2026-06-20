import json
from pathlib import Path

from core.context_builder import (
    build_final_ai_prompt,
    build_context_readiness,
    build_guided_context_bundle,
    build_technical_context,
    export_guided_context_bundle,
)


def test_context_builder_includes_rules_cases_results_and_nextjs_files():
    context = build_technical_context(
        [
            {
                "id": "lead-1",
                "lead_name": "Marina",
                "source": "WhatsApp",
                "message": "quero orçamento urgente",
                "score": 95,
                "classification": "urgent_lead",
                "recommended_action": "Enviar para atendimento humano agora",
                "nextjs_impact": "Criar função calculateLeadScore em /lib/lead-score.ts",
                "status": "success",
                "error": None,
            }
        ]
    )

    assert "Contexto Técnico — Lead Algorithm Lab" in context
    assert "Implementar algoritmo determinístico de lead score" in context
    assert "WhatsApp: +25" in context
    assert "lead-1" in context
    assert "urgent_lead" in context
    assert "/lib/lead-score.ts" in context
    assert "Este algoritmo não depende de IA para decidir." in context


def test_guided_context_builder_marks_missing_evidence_as_needs_tests():
    bundle = build_guided_context_bundle(
        source_mode="algorithm_api",
        live_context="",
        algorithm_context="",
        api_context="",
        token_context="",
        algorithm_metrics={"total_results": 0, "passed": 0, "failed": 0},
        api_metrics={"total_results": 0, "passed": 0, "failed": 0},
        live_metrics={"total_tests": 0, "success": 0, "failures": 0},
        token_metrics={"total_estimates": 0},
    )

    assert bundle["readiness"]["overall"]["status"] == "Needs tests"
    assert "Bloqueios antes de implementar" in bundle["context"]
    assert "Rode pelo menos uma suite" in bundle["context"]


def test_guided_context_builder_marks_algorithm_and_api_evidence_as_ready():
    bundle = build_guided_context_bundle(
        source_mode="algorithm_api",
        live_context="# Live\n\n- evento validado",
        algorithm_context="# Algorithm\n\n- lead_score passou",
        api_context="# API\n\n- whatsapp passou",
        token_context="# Token\n\n- custo estimado",
        algorithm_metrics={"total_results": 17, "passed": 17, "failed": 0},
        api_metrics={"total_results": 4, "passed": 4, "failed": 0, "evidence_modes": {"dry_run_contract": 4}},
        live_metrics={"total_tests": 2, "success": 2, "failures": 0},
        token_metrics={"total_estimates": 1},
    )

    assert bundle["readiness"]["overall"]["status"] == "Ready"
    assert bundle["source_mode"] == "algorithm_api"
    assert "Resumo Executivo" in bundle["context"]
    assert "Evidências Disponíveis" in bundle["context"]
    assert "Impacto para Implementação Futura" in bundle["context"]
    assert "lead_score passou" in bundle["context"]
    assert "whatsapp passou" in bundle["context"]
    assert bundle["readiness"]["api"]["evidence_modes"]["dry_run_contract"] == 4
    assert "dry_run_contract=4" in bundle["context"]


def test_guided_context_builder_marks_failures_as_has_failures():
    readiness = build_context_readiness(
        source_mode="algorithm",
        algorithm_metrics={"total_results": 17, "passed": 16, "failed": 1},
        api_metrics={"total_results": 0, "passed": 0, "failed": 0},
        live_metrics={"total_tests": 0, "success": 0, "failures": 0},
        token_metrics={"total_estimates": 0},
    )

    assert readiness["overall"]["status"] == "Has failures"
    assert readiness["algorithm"]["status"] == "Has failures"


def test_full_evidence_requires_every_declared_source_before_ready():
    readiness = build_context_readiness(
        source_mode="full",
        algorithm_metrics={"total_results": 17, "passed": 17, "failed": 0},
        api_metrics={"total_results": 0, "passed": 0, "failed": 0},
        live_metrics={"total_tests": 0, "success": 0, "failures": 0},
        token_metrics={"total_estimates": 0},
        acp_metrics={"total_events": 0, "successful_prompts": 0, "failed_prompts": 0},
    )

    assert readiness["overall"]["status"] == "Needs tests"


def test_guided_context_builder_exports_markdown_json_html_and_zip(tmp_path):
    bundle = build_guided_context_bundle(
        source_mode="algorithm",
        live_context="",
        algorithm_context="# Algorithm\n\n- lead_score passou",
        api_context="",
        token_context="",
        algorithm_metrics={"total_results": 17, "passed": 17, "failed": 0},
        api_metrics={"total_results": 0, "passed": 0, "failed": 0},
        live_metrics={"total_tests": 0, "success": 0, "failures": 0},
        token_metrics={"total_estimates": 0},
    )

    paths = export_guided_context_bundle(tmp_path, bundle)

    assert set(paths) == {"markdown", "json", "html", "zip"}
    assert Path(paths["markdown"]).exists()
    assert Path(paths["json"]).exists()
    assert Path(paths["html"]).read_text(encoding="utf-8").startswith("<!doctype html>")
    assert Path(paths["zip"]).exists()
    payload = json.loads(Path(paths["json"]).read_text(encoding="utf-8"))
    assert payload["source_mode"] == "algorithm"
    assert payload["readiness"]["overall"]["status"] == "Ready"
    assert payload["algorithm_metrics"]["total_results"] == 17
    assert "lead_score passou" in payload["context"]


def test_final_ai_prompt_is_short_and_evidence_bounded():
    bundle = build_guided_context_bundle(
        source_mode="algorithm_api",
        live_context="# Live\n\n- responses_api validada",
        algorithm_context="# Algorithm\n\n- lead_score passou",
        api_context="# API\n\n- whatsapp dry-run passou",
        token_context="# Token\n\n- custo estimado",
        algorithm_metrics={"total_results": 17, "passed": 17, "failed": 0, "evidence_modes": {"seed_validation": 17}},
        api_metrics={"total_results": 4, "passed": 4, "failed": 0, "evidence_modes": {"dry_run_contract": 4}},
        live_metrics={"total_tests": 1, "success": 1, "failures": 0, "evidence_modes": {"real_http": 3}},
        token_metrics={"total_estimates": 1, "evidence_modes": {"seeded_estimate": 1}},
    )

    prompt = build_final_ai_prompt(bundle)

    assert "Readiness: Ready" in prompt
    assert "seed_validation=17" in prompt
    assert "dry_run_contract=4" in prompt
    assert "real_http=3" in prompt
    assert "Nao invente payloads, regras ou endpoints" in prompt
    assert "Implementar somente comportamento validado" in prompt
