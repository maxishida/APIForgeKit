from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260601_api_token_lab"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "api_test_suites",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("provider", sa.String(length=80), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("docs_url", sa.String(length=500), nullable=False),
        sa.Column("tags", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_api_test_suites_created_at", "api_test_suites", ["created_at"])
    op.create_index("ix_api_test_suites_name", "api_test_suites", ["name"])
    op.create_index("ix_api_test_suites_provider", "api_test_suites", ["provider"])

    op.create_table(
        "api_test_cases",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("suite_id", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=180), nullable=False),
        sa.Column("method", sa.String(length=20), nullable=False),
        sa.Column("url", sa.String(length=1000), nullable=False),
        sa.Column("headers", sa.JSON(), nullable=False),
        sa.Column("body", sa.JSON(), nullable=False),
        sa.Column("expected", sa.JSON(), nullable=False),
        sa.Column("dry_run", sa.Boolean(), nullable=False),
        sa.Column("mock_response", sa.JSON(), nullable=False),
        sa.Column("timeout_seconds", sa.Integer(), nullable=False),
        sa.Column("tags", sa.JSON(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_api_test_cases_suite_id", "api_test_cases", ["suite_id"])
    op.create_index("ix_api_test_cases_enabled", "api_test_cases", ["enabled"])

    op.create_table(
        "api_test_runs",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("suite_id", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("total_cases", sa.Integer(), nullable=False),
        sa.Column("passed", sa.Integer(), nullable=False),
        sa.Column("failed", sa.Integer(), nullable=False),
        sa.Column("summary", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_api_test_runs_created_at", "api_test_runs", ["created_at"])
    op.create_index("ix_api_test_runs_suite_id", "api_test_runs", ["suite_id"])
    op.create_index("ix_api_test_runs_status", "api_test_runs", ["status"])

    op.create_table(
        "api_test_results",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("run_id", sa.String(length=64), nullable=False),
        sa.Column("suite_id", sa.String(length=64), nullable=False),
        sa.Column("case_id", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("request", sa.JSON(), nullable=False),
        sa.Column("response", sa.JSON(), nullable=False),
        sa.Column("diff", sa.JSON(), nullable=False),
        sa.Column("latency_ms", sa.Float(), nullable=False),
        sa.Column("structured_log", sa.JSON(), nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("recommendation", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_api_test_results_created_at", "api_test_results", ["created_at"])
    op.create_index("ix_api_test_results_run_id", "api_test_results", ["run_id"])
    op.create_index("ix_api_test_results_status", "api_test_results", ["status"])

    op.create_table(
        "token_usage_estimates",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("provider", sa.String(length=80), nullable=False),
        sa.Column("model", sa.String(length=160), nullable=False),
        sa.Column("users", sa.Integer(), nullable=False),
        sa.Column("requests_per_user_per_day", sa.Integer(), nullable=False),
        sa.Column("days", sa.Integer(), nullable=False),
        sa.Column("input_tokens_per_request", sa.Integer(), nullable=False),
        sa.Column("output_tokens_per_request", sa.Integer(), nullable=False),
        sa.Column("cached_input_tokens_per_request", sa.Integer(), nullable=False),
        sa.Column("total_tokens", sa.Integer(), nullable=False),
        sa.Column("estimated_cost_usd", sa.Float(), nullable=False),
        sa.Column("source_url", sa.String(length=500), nullable=False),
        sa.Column("summary", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_token_usage_estimates_created_at", "token_usage_estimates", ["created_at"])
    op.create_index("ix_token_usage_estimates_provider", "token_usage_estimates", ["provider"])
    op.create_index("ix_token_usage_estimates_model", "token_usage_estimates", ["model"])


def downgrade() -> None:
    op.drop_table("token_usage_estimates")
    op.drop_table("api_test_results")
    op.drop_table("api_test_runs")
    op.drop_table("api_test_cases")
    op.drop_table("api_test_suites")
