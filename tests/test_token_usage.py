from sqlalchemy import create_engine

from core.database import build_session_factory, init_db
from core.token_usage import (
    TokenUsageRepository,
    build_token_usage_context,
    calculate_token_cost,
    estimate_context_savings,
    get_pricing_catalog,
)


def test_pricing_catalog_includes_current_provider_doc_sources():
    catalog = get_pricing_catalog()

    assert catalog["xai:grok-4.3"].source_url == "https://docs.x.ai/developers/models"
    assert catalog["openai:gpt-5.5"].input_per_million == 5.00
    assert catalog["anthropic:claude-sonnet-4.6"].output_per_million == 15.00
    assert catalog["gemini:gemini-2.5-flash"].cached_input_per_million == 0.03


def test_token_cost_calculator_projects_per_user_monthly_usage():
    estimate = calculate_token_cost(
        provider="xai",
        model="grok-4.3",
        input_tokens_per_request=1_000,
        output_tokens_per_request=500,
        cached_input_tokens_per_request=0,
        users=10,
        requests_per_user_per_day=20,
        days=30,
    )

    assert estimate["total_requests"] == 6000
    assert estimate["total_input_tokens"] == 6_000_000
    assert estimate["total_output_tokens"] == 3_000_000
    assert estimate["estimated_cost_usd"] == 15.0
    assert estimate["cost_per_user_usd"] == 1.5
    assert estimate["source_url"] == "https://docs.x.ai/developers/models"


def test_context_savings_estimate_compares_raw_prompt_with_structured_context():
    savings = estimate_context_savings(
        provider="openai",
        model="gpt-5.5",
        raw_context_tokens=80_000,
        structured_context_tokens=12_000,
        output_tokens=2_000,
        repeated_calls=5,
    )

    assert savings["raw_cost_usd"] > savings["structured_cost_usd"]
    assert savings["saved_tokens"] == 340_000
    assert savings["savings_percent"] > 70


def test_token_usage_repository_saves_estimates():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    init_db(engine)
    repository = TokenUsageRepository(build_session_factory(engine))
    estimate = calculate_token_cost(
        provider="gemini",
        model="gemini-2.5-flash",
        input_tokens_per_request=2_000,
        output_tokens_per_request=500,
        users=2,
        requests_per_user_per_day=3,
        days=7,
    )

    row = repository.save_estimate(estimate)
    rows = repository.list_estimates()

    assert row["provider"] == "gemini"
    assert rows[0]["model"] == "gemini-2.5-flash"
    assert rows[0]["estimated_cost_usd"] == estimate["estimated_cost_usd"]


def test_token_usage_context_includes_saved_estimates_and_provider_docs():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    init_db(engine)
    repository = TokenUsageRepository(build_session_factory(engine))
    repository.save_estimate(
        calculate_token_cost(
            provider="xai",
            model="grok-4.3",
            input_tokens_per_request=1000,
            output_tokens_per_request=500,
            users=1,
            requests_per_user_per_day=1,
            days=1,
        )
    )

    context = build_token_usage_context(repository)

    assert "Contexto Técnico - Token Usage Calculator" in context
    assert "grok-4.3" in context
    assert "https://docs.x.ai/developers/models" in context
