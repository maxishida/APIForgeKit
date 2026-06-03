from sqlalchemy import create_engine

from core.database import build_session_factory, init_db
from core.token_usage import TokenUsageRepository, build_token_usage_context, calculate_token_cost


def _repository() -> TokenUsageRepository:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    init_db(engine)
    return TokenUsageRepository(build_session_factory(engine))


def test_docs_verified_pricing_records_source_and_timestamp():
    estimate = calculate_token_cost(
        provider="xai",
        model="grok-4.3",
        input_tokens_per_request=1000,
        output_tokens_per_request=500,
        users=10,
        requests_per_user_per_day=20,
        days=30,
        pricing_mode="docs_verified",
        pricing_verified_source_url="https://docs.x.ai/developers/models",
    )

    assert estimate["pricing_mode"] == "docs_verified"
    assert estimate["pricing_verified_source_url"] == "https://docs.x.ai/developers/models"
    assert isinstance(estimate["pricing_verified_at"], str)
    assert estimate["pricing_verified_at"]


def test_seeded_estimate_does_not_claim_docs_verification():
    estimate = calculate_token_cost(
        provider="xai",
        model="grok-4.3",
        input_tokens_per_request=1000,
        output_tokens_per_request=500,
    )

    assert estimate["pricing_mode"] == "seeded_estimate"
    assert estimate["pricing_verified_source_url"] == ""
    assert estimate["pricing_verified_at"] == ""


def test_token_context_includes_pricing_verification_audit_fields():
    repository = _repository()
    estimate = calculate_token_cost(
        provider="xai",
        model="grok-4.3",
        input_tokens_per_request=1000,
        output_tokens_per_request=500,
        pricing_mode="docs_verified",
        pricing_verified_source_url="https://docs.x.ai/developers/models",
    )
    repository.save_estimate(estimate)

    context = build_token_usage_context(repository)

    assert "pricing_mode=docs_verified" in context
    assert "verified_at=" in context
    assert "https://docs.x.ai/developers/models" in context
