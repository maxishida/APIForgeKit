from core.lead_algorithm import LeadInput, calculate_lead_score


def test_high_intent_whatsapp_lead_clamps_to_urgent_score():
    result = calculate_lead_score(
        LeadInput(
            lead_name="Marina Costa",
            source="WhatsApp",
            message="Quero comprar hoje pelo WhatsApp. Preciso de orçamento urgente.",
            budget="5000",
            urgency="alta",
            interest="alto",
            has_phone=True,
            has_email=True,
            previous_customer=True,
        )
    )

    assert result.score == 100
    assert result.status == "urgent_lead"
    assert result.confidence >= 0.9
    assert any("comprar" in reason for reason in result.reasons)
    assert any("Origem WhatsApp" in reason for reason in result.reasons)
    assert result.recommended_action == "Enviar para atendimento humano agora"
    assert result.nextjs_impact == "Criar função calculateLeadScore em /lib/lead-score.ts"


def test_empty_message_is_invalid_even_with_good_business_data():
    result = calculate_lead_score(
        LeadInput(
            lead_name="Lead sem mensagem",
            source="Ligação",
            message="   ",
            budget="1000",
            urgency="alta",
            interest="alto",
            has_phone=True,
            has_email=True,
            previous_customer=True,
        )
    )

    assert result.score == 0
    assert result.status == "invalid_lead"
    assert result.recommended_action == "Solicitar mensagem válida antes de qualificar"
    assert any("Mensagem vazia" in reason for reason in result.reasons)


def test_spam_message_is_invalid():
    result = calculate_lead_score(
        LeadInput(
            lead_name="Spam",
            source="Instagram",
            message="Ganhe dinheiro rapido com clique aqui e promoção suspeita",
            budget="",
            urgency="baixa",
            interest="baixo",
            has_phone=False,
            has_email=True,
            previous_customer=False,
        )
    )

    assert result.score == 0
    assert result.status == "invalid_lead"
    assert any("spam" in reason.lower() for reason in result.reasons)


def test_no_contact_and_short_message_apply_penalties():
    result = calculate_lead_score(
        LeadInput(
            lead_name="Contato ausente",
            source="LinkedIn",
            message="preço",
            budget="",
            urgency="baixa",
            interest="baixo",
            has_phone=False,
            has_email=False,
            previous_customer=False,
        )
    )

    assert result.score == 0
    assert result.status == "cold_lead"
    assert any("sem telefone e sem e-mail" in reason for reason in result.reasons)
    assert any("Mensagem muito curta" in reason for reason in result.reasons)


def test_classification_boundaries_are_deterministic():
    assert calculate_lead_score(
        LeadInput("A", "LinkedIn", "mensagem simples", "", "baixa", "baixo", False, True, False)
    ).status == "cold_lead"
    assert calculate_lead_score(
        LeadInput("B", "Instagram", "quero orçamento", "", "média", "médio", False, False, False)
    ).status == "warm_lead"
    assert calculate_lead_score(
        LeadInput("C", "Landing Page", "quero orçamento", "", "baixa", "médio", True, True, False)
    ).status == "hot_lead"
    assert calculate_lead_score(
        LeadInput("D", "Ligação", "quero comprar agora", "", "alta", "alto", True, True, False)
    ).status == "urgent_lead"
