from core.context_builder import build_technical_context


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
