"""gradient boosting forecasting metadata

Revision ID: 20260716_0007
Revises: 20260716_0006
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260716_0007"
down_revision: str | None = "20260716_0006"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    for column in (
        sa.Column("tuning_method", sa.String(30)),
        sa.Column("tuning_trial_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed_trial_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("tuning_duration_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("best_iteration", sa.Integer()),
        sa.Column("best_score", sa.Float()),
        sa.Column("feature_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("explanation_available", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("global_model", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("strategy", sa.String(20), nullable=False, server_default="global"),
        sa.Column("dependency_version", sa.String(30)),
    ):
        op.add_column("forecast_model_runs", column)
    op.create_table(
        "forecast_tuning_trials",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("model_run_id", sa.String(36), nullable=False),
        sa.Column("trial_number", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("parameters_json", sa.JSON(), nullable=False),
        sa.Column("backtest_metric", sa.Float()),
        sa.Column("validation_metric", sa.Float()),
        sa.Column("duration_ms", sa.Integer(), nullable=False),
        sa.Column("failure_message", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["model_run_id"], ["forecast_model_runs.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_forecast_tuning_trials_model_run_id", "forecast_tuning_trials", ["model_run_id"])
    op.create_index("ix_forecast_tuning_trials_status", "forecast_tuning_trials", ["status"])


def downgrade() -> None:
    op.drop_table("forecast_tuning_trials")
    for name in (
        "dependency_version",
        "strategy",
        "global_model",
        "explanation_available",
        "feature_count",
        "best_score",
        "best_iteration",
        "tuning_duration_ms",
        "failed_trial_count",
        "tuning_trial_count",
        "tuning_method",
    ):
        op.drop_column("forecast_model_runs", name)
