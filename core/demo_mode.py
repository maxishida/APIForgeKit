from __future__ import annotations

from core.algorithm_test_lab import AlgorithmTestRepository, AlgorithmTestRunner, ensure_default_algorithms
from core.api_test_lab import ApiTestRepository, ApiTestRunner, ensure_default_api_suites
from core.token_usage import TokenUsageRepository, calculate_token_cost


def run_demo_mode(
    *,
    algorithm_repository: AlgorithmTestRepository,
    api_repository: ApiTestRepository,
    token_repository: TokenUsageRepository,
) -> dict[str, object]:
    ensure_default_algorithms(algorithm_repository)
    ensure_default_api_suites(api_repository)

    algorithm_definition = algorithm_repository.get_definition_by_name("lead_score")
    algorithm_run = AlgorithmTestRunner(algorithm_repository).run_suite(str(algorithm_definition["id"]))

    api_suite = api_repository.get_suite_by_name("whatsapp_validation_pack")
    api_run = ApiTestRunner(api_repository).run_contract_suite(str(api_suite["id"]))

    estimate = calculate_token_cost(
        provider="xai",
        model="grok-4.3",
        input_tokens_per_request=2_000,
        output_tokens_per_request=800,
        users=5,
        requests_per_user_per_day=10,
        days=30,
    )
    token_estimate = token_repository.save_estimate(estimate)

    demo_ready = algorithm_run["status"] == "passed" and api_run["status"] == "passed"
    return {
        "algorithm_run": algorithm_run,
        "api_run": api_run,
        "token_estimate": token_estimate,
        "summary": {
            "demo_ready": demo_ready,
            "algorithm_passed": algorithm_run["passed"],
            "api_passed": api_run["passed"],
            "estimated_cost_usd": token_estimate["estimated_cost_usd"],
        },
    }
