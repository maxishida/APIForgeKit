from __future__ import annotations

from dataclasses import asdict, dataclass, field
from uuid import uuid4


STRONG_KEYWORDS = (
    "comprar",
    "preço",
    "preco",
    "orçamento",
    "orcamento",
    "urgente",
    "hoje",
    "agora",
    "whatsapp",
    "ligação",
    "ligacao",
)

SPAM_PATTERNS = (
    "spam",
    "ganhe dinheiro",
    "clique aqui",
    "promoção suspeita",
    "promocao suspeita",
)

SOURCE_POINTS = {
    "WhatsApp": 25,
    "Ligação": 30,
    "Landing Page": 20,
    "Instagram": 15,
    "LinkedIn": 10,
}

URGENCY_POINTS = {"alta": 25, "média": 15, "media": 15, "baixa": 5}
INTEREST_POINTS = {"alto": 25, "médio": 15, "medio": 15, "baixo": 5}


@dataclass(frozen=True)
class LeadInput:
    lead_name: str
    source: str
    message: str
    budget: str
    urgency: str
    interest: str
    has_phone: bool
    has_email: bool
    previous_customer: bool

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class LeadScoreResult:
    lead_id: str
    score: int
    status: str
    confidence: float
    reasons: list[str] = field(default_factory=list)
    recommended_action: str = ""
    nextjs_impact: str = "Criar função calculateLeadScore em /lib/lead-score.ts"

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _normalize(value: str) -> str:
    return (value or "").strip().lower()


def _contains_spam(message: str) -> bool:
    normalized = _normalize(message)
    return any(pattern in normalized for pattern in SPAM_PATTERNS)


def _classification(score: int) -> str:
    if score <= 30:
        return "cold_lead"
    if score <= 60:
        return "warm_lead"
    if score <= 80:
        return "hot_lead"
    return "urgent_lead"


def _recommended_action(status: str) -> str:
    return {
        "invalid_lead": "Solicitar mensagem válida antes de qualificar",
        "urgent_lead": "Enviar para atendimento humano agora",
        "hot_lead": "Priorizar contato comercial no próximo horário disponível",
        "warm_lead": "Enviar follow-up com proposta e prova social",
        "cold_lead": "Nutrir com conteúdo e capturar mais dados de contato",
    }[status]


def _confidence(score: int, reasons: list[str], invalid: bool = False) -> float:
    if invalid:
        return 0.92
    value = 0.55 + (score / 200) + min(len(reasons), 10) * 0.01
    return round(min(value, 0.95), 2)


def calculate_lead_score(lead: LeadInput) -> LeadScoreResult:
    message = lead.message.strip()
    reasons: list[str] = []

    if not message:
        reasons.append("Mensagem vazia: lead inválido")
        return LeadScoreResult(
            lead_id=str(uuid4()),
            score=0,
            status="invalid_lead",
            confidence=_confidence(0, reasons, invalid=True),
            reasons=reasons,
            recommended_action=_recommended_action("invalid_lead"),
        )

    if _contains_spam(message):
        reasons.append("Mensagem contém padrão de spam: lead inválido")
        return LeadScoreResult(
            lead_id=str(uuid4()),
            score=0,
            status="invalid_lead",
            confidence=_confidence(0, reasons, invalid=True),
            reasons=reasons,
            recommended_action=_recommended_action("invalid_lead"),
        )

    score = 0
    normalized_message = _normalize(message)
    for keyword in STRONG_KEYWORDS:
        if keyword in normalized_message:
            score += 10
            reasons.append(f"Mensagem contém palavra forte: {keyword} (+10)")

    source_points = SOURCE_POINTS.get(lead.source, 0)
    if source_points:
        score += source_points
        reasons.append(f"Origem {lead.source} adicionou {source_points} pontos")

    urgency_points = URGENCY_POINTS.get(_normalize(lead.urgency), 0)
    if urgency_points:
        score += urgency_points
        reasons.append(f"Urgência {lead.urgency} adicionou {urgency_points} pontos")

    interest_points = INTEREST_POINTS.get(_normalize(lead.interest), 0)
    if interest_points:
        score += interest_points
        reasons.append(f"Interesse {lead.interest} adicionou {interest_points} pontos")

    if lead.has_phone:
        score += 10
        reasons.append("Telefone informado adicionou 10 pontos")

    if lead.has_email:
        score += 5
        reasons.append("E-mail informado adicionou 5 pontos")

    if lead.previous_customer:
        score += 20
        reasons.append("Cliente anterior adicionou 20 pontos")

    if not lead.has_phone and not lead.has_email:
        score -= 20
        reasons.append("Lead sem telefone e sem e-mail removeu 20 pontos")

    if len(message) < 12:
        score -= 10
        reasons.append("Mensagem muito curta removeu 10 pontos")

    final_score = max(0, min(score, 100))
    status = _classification(final_score)
    return LeadScoreResult(
        lead_id=str(uuid4()),
        score=final_score,
        status=status,
        confidence=_confidence(final_score, reasons),
        reasons=reasons,
        recommended_action=_recommended_action(status),
    )
