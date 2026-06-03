from __future__ import annotations

from dataclasses import asdict, dataclass
from uuid import uuid4

from sqlalchemy import desc, select
from sqlalchemy.orm import Session, sessionmaker

from core.models import TokenUsageEstimate


@dataclass(frozen=True)
class ProviderPricing:
    provider: str
    model: str
    input_per_million: float
    output_per_million: float
    cached_input_per_million: float
    source_url: str
    notes: str = ""

    @property
    def key(self) -> str:
        return f"{self.provider}:{self.model}"


DEFAULT_PRICING = (
    ProviderPricing(
        provider="xai",
        model="grok-4.3",
        input_per_million=1.25,
        output_per_million=2.50,
        cached_input_per_million=0.25,
        source_url="https://docs.x.ai/developers/models",
        notes="Seed baseado na tabela oficial de modelos e preços da xAI.",
    ),
    ProviderPricing(
        provider="xai",
        model="grok-build-0.1",
        input_per_million=1.00,
        output_per_million=2.00,
        cached_input_per_million=0.20,
        source_url="https://docs.x.ai/developers/models",
        notes="Modelo de baixo custo útil para harness e validações repetidas.",
    ),
    ProviderPricing(
        provider="openai",
        model="gpt-5.5",
        input_per_million=5.00,
        output_per_million=30.00,
        cached_input_per_million=0.50,
        source_url="https://platform.openai.com/docs/pricing",
        notes="Use para estimar prompts grandes e relatórios complexos.",
    ),
    ProviderPricing(
        provider="openai",
        model="gpt-5.4-mini",
        input_per_million=0.75,
        output_per_million=4.50,
        cached_input_per_million=0.075,
        source_url="https://platform.openai.com/docs/pricing",
        notes="Boa opção para estimativas de contexto técnico compacto.",
    ),
    ProviderPricing(
        provider="anthropic",
        model="claude-sonnet-4.6",
        input_per_million=3.00,
        output_per_million=15.00,
        cached_input_per_million=0.30,
        source_url="https://docs.anthropic.com/en/docs/about-claude/pricing",
        notes="Preço seedado para comparação de custo por usuário.",
    ),
    ProviderPricing(
        provider="anthropic",
        model="claude-haiku-4.5",
        input_per_million=1.00,
        output_per_million=5.00,
        cached_input_per_million=0.10,
        source_url="https://docs.anthropic.com/en/docs/about-claude/pricing",
        notes="Modelo econômico para fluxos repetitivos.",
    ),
    ProviderPricing(
        provider="gemini",
        model="gemini-2.5-pro",
        input_per_million=1.25,
        output_per_million=10.00,
        cached_input_per_million=0.125,
        source_url="https://ai.google.dev/gemini-api/docs/pricing",
        notes="Seed para estimativa de workloads maiores.",
    ),
    ProviderPricing(
        provider="gemini",
        model="gemini-2.5-flash",
        input_per_million=0.30,
        output_per_million=2.50,
        cached_input_per_million=0.03,
        source_url="https://ai.google.dev/gemini-api/docs/pricing",
        notes="Modelo econômico para cálculo de uso por usuário.",
    ),
)

USAGE_PRESETS: dict[str, dict[str, object]] = {
    "dev_solo": {
        "label": "Dev solo",
        "users": 1,
        "requests_per_user_per_day": 12,
        "days": 30,
        "input_tokens_per_request": 1800,
        "output_tokens_per_request": 600,
        "cached_input_tokens_per_request": 0,
        "raw_context_tokens": 40_000,
        "structured_context_tokens": 8_000,
        "repeated_calls": 4,
    },
    "saas_small": {
        "label": "SaaS pequeno",
        "users": 50,
        "requests_per_user_per_day": 15,
        "days": 30,
        "input_tokens_per_request": 1400,
        "output_tokens_per_request": 500,
        "cached_input_tokens_per_request": 200,
        "raw_context_tokens": 80_000,
        "structured_context_tokens": 12_000,
        "repeated_calls": 8,
    },
    "agency": {
        "label": "Agência",
        "users": 120,
        "requests_per_user_per_day": 8,
        "days": 30,
        "input_tokens_per_request": 2200,
        "output_tokens_per_request": 900,
        "cached_input_tokens_per_request": 400,
        "raw_context_tokens": 120_000,
        "structured_context_tokens": 18_000,
        "repeated_calls": 12,
    },
    "high_volume": {
        "label": "High volume",
        "users": 1000,
        "requests_per_user_per_day": 25,
        "days": 30,
        "input_tokens_per_request": 900,
        "output_tokens_per_request": 350,
        "cached_input_tokens_per_request": 300,
        "raw_context_tokens": 200_000,
        "structured_context_tokens": 30_000,
        "repeated_calls": 30,
    },
}


def get_pricing_catalog() -> dict[str, ProviderPricing]:
    return {pricing.key: pricing for pricing in DEFAULT_PRICING}


def get_usage_presets() -> dict[str, dict[str, object]]:
    return {key: dict(value) for key, value in USAGE_PRESETS.items()}


def provider_options() -> dict[str, list[str]]:
    options: dict[str, list[str]] = {}
    for pricing in DEFAULT_PRICING:
        options.setdefault(pricing.provider, []).append(pricing.model)
    return options


def get_pricing(provider: str, model: str) -> ProviderPricing:
    key = f"{provider}:{model}"
    catalog = get_pricing_catalog()
    if key not in catalog:
        supported = ", ".join(sorted(catalog))
        raise ValueError(f"Unsupported provider/model: {key}. Supported: {supported}")
    return catalog[key]


def calculate_token_cost(
    *,
    provider: str,
    model: str,
    input_tokens_per_request: int,
    output_tokens_per_request: int,
    cached_input_tokens_per_request: int = 0,
    users: int = 1,
    requests_per_user_per_day: int = 1,
    days: int = 30,
    pricing_mode: str = "seeded_estimate",
) -> dict[str, object]:
    pricing = get_pricing(provider, model)
    pricing_mode = pricing_mode if pricing_mode in {"seeded_estimate", "docs_verified"} else "seeded_estimate"
    users = max(int(users), 1)
    requests_per_user_per_day = max(int(requests_per_user_per_day), 0)
    days = max(int(days), 1)
    input_tokens_per_request = max(int(input_tokens_per_request), 0)
    output_tokens_per_request = max(int(output_tokens_per_request), 0)
    cached_input_tokens_per_request = max(int(cached_input_tokens_per_request), 0)

    total_requests = users * requests_per_user_per_day * days
    total_input = input_tokens_per_request * total_requests
    total_output = output_tokens_per_request * total_requests
    total_cached = cached_input_tokens_per_request * total_requests
    billable_input = max(total_input - total_cached, 0)

    input_cost = (billable_input / 1_000_000) * pricing.input_per_million
    cached_cost = (total_cached / 1_000_000) * pricing.cached_input_per_million
    output_cost = (total_output / 1_000_000) * pricing.output_per_million
    total_cost = round(input_cost + cached_cost + output_cost, 6)

    return {
        "provider": provider,
        "model": model,
        "users": users,
        "requests_per_user_per_day": requests_per_user_per_day,
        "days": days,
        "total_requests": total_requests,
        "input_tokens_per_request": input_tokens_per_request,
        "output_tokens_per_request": output_tokens_per_request,
        "cached_input_tokens_per_request": cached_input_tokens_per_request,
        "total_input_tokens": total_input,
        "total_output_tokens": total_output,
        "total_cached_input_tokens": total_cached,
        "total_tokens": total_input + total_output,
        "input_cost_usd": round(input_cost, 6),
        "cached_input_cost_usd": round(cached_cost, 6),
        "output_cost_usd": round(output_cost, 6),
        "estimated_cost_usd": total_cost,
        "cost_per_user_usd": round(total_cost / users, 6),
        "cost_per_request_usd": round(total_cost / total_requests, 8) if total_requests else 0,
        "pricing_mode": pricing_mode,
        "pricing": asdict(pricing),
        "source_url": pricing.source_url,
        "recommendation": _usage_recommendation(total_cost, users, total_requests),
    }


def estimate_context_savings(
    *,
    provider: str,
    model: str,
    raw_context_tokens: int,
    structured_context_tokens: int,
    output_tokens: int,
    repeated_calls: int = 1,
) -> dict[str, object]:
    raw = calculate_token_cost(
        provider=provider,
        model=model,
        input_tokens_per_request=raw_context_tokens,
        output_tokens_per_request=output_tokens,
        users=1,
        requests_per_user_per_day=max(repeated_calls, 1),
        days=1,
    )
    structured = calculate_token_cost(
        provider=provider,
        model=model,
        input_tokens_per_request=structured_context_tokens,
        output_tokens_per_request=output_tokens,
        users=1,
        requests_per_user_per_day=max(repeated_calls, 1),
        days=1,
    )
    saved_tokens = max(raw_context_tokens - structured_context_tokens, 0) * max(repeated_calls, 1)
    raw_cost = float(raw["estimated_cost_usd"])
    structured_cost = float(structured["estimated_cost_usd"])
    saved_cost = round(max(raw_cost - structured_cost, 0), 6)
    return {
        "provider": provider,
        "model": model,
        "repeated_calls": max(repeated_calls, 1),
        "raw_cost_usd": raw_cost,
        "structured_cost_usd": structured_cost,
        "saved_cost_usd": saved_cost,
        "saved_tokens": saved_tokens,
        "savings_percent": round((saved_cost / raw_cost) * 100, 2) if raw_cost else 0,
        "source_url": str(raw["source_url"]),
        "recommendation": "Use logs estruturados e contexto técnico compacto antes de pedir implementação à IA.",
    }


class TokenUsageRepository:
    def __init__(self, session_factory: sessionmaker[Session]):
        self.session_factory = session_factory

    def save_estimate(self, estimate: dict[str, object]) -> dict[str, object]:
        with self.session_factory() as session:
            row = TokenUsageEstimate(
                id=str(uuid4()),
                provider=str(estimate["provider"]),
                model=str(estimate["model"]),
                users=int(estimate["users"]),
                requests_per_user_per_day=int(estimate["requests_per_user_per_day"]),
                days=int(estimate["days"]),
                input_tokens_per_request=int(estimate["input_tokens_per_request"]),
                output_tokens_per_request=int(estimate["output_tokens_per_request"]),
                cached_input_tokens_per_request=int(estimate["cached_input_tokens_per_request"]),
                total_tokens=int(estimate["total_tokens"]),
                estimated_cost_usd=float(estimate["estimated_cost_usd"]),
                source_url=str(estimate["source_url"]),
                summary=estimate,
            )
            session.add(row)
            session.commit()
            session.refresh(row)
            return row.to_dict()

    def list_estimates(self, limit: int = 50) -> list[dict[str, object]]:
        with self.session_factory() as session:
            rows = session.scalars(select(TokenUsageEstimate).order_by(desc(TokenUsageEstimate.created_at)).limit(limit)).all()
            return [row.to_dict() for row in rows]


def build_token_usage_context(repository: TokenUsageRepository, limit: int = 50) -> str:
    estimates = repository.list_estimates(limit=limit)
    lines = []
    for estimate in estimates:
        lines.append(
            f"- `{estimate['provider']}/{estimate['model']}` users={estimate['users']} "
            f"requests_day={estimate['requests_per_user_per_day']} tokens={estimate['total_tokens']} "
            f"cost=${estimate['estimated_cost_usd']} pricing_mode={estimate.get('summary', {}).get('pricing_mode', 'seeded_estimate')} "
            f"source={estimate['source_url']}"
        )
    return f"""# Contexto Técnico - Token Usage Calculator

## Estimativas salvas

{chr(10).join(lines) if lines else "- Nenhuma estimativa salva ainda."}

## Como usar na implementação

- Projetar custo por usuário antes de escolher modelo.
- Medir input/output reais nos logs do provider.
- Trocar conversa longa por contexto técnico compacto sempre que possível.
- Conferir preços nos docs oficiais antes de decisão financeira.
- Tratar `seeded_estimate` como planejamento; decisão financeira exige `docs_verified`.
"""


def _usage_recommendation(total_cost: float, users: int, total_requests: int) -> str:
    if total_requests == 0:
        return "Sem requests projetados. Aumente requests por usuário para calcular custo real."
    if total_cost < 1:
        return "Custo baixo para validação local. Bom candidato para harness automatizado."
    cost_per_user = total_cost / max(users, 1)
    if cost_per_user > 10:
        return "Custo por usuário alto. Reduza contexto, use cache ou rode validações por amostragem."
    return "Custo controlado. Monitore tokens por usuário e mantenha relatórios compactos."
