"""baseline forecasting registry

Revision ID: 20260716_0006
Revises: 20260716_0005
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260716_0006"
down_revision: str | None = "20260716_0005"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "forecast_experiments",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("prepared_dataset_id", sa.String(36), nullable=False),
        sa.Column("experiment_version", sa.Integer(), nullable=False),
        sa.Column("forecasting_engine_version", sa.String(30), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("target_column", sa.String(255), nullable=False),
        sa.Column("date_column", sa.String(255), nullable=False),
        sa.Column("group_columns_json", sa.JSON(), nullable=False),
        sa.Column("frequency", sa.String(20), nullable=False),
        sa.Column("forecast_horizon", sa.Integer(), nullable=False),
        sa.Column("selection_metric", sa.String(20), nullable=False),
        sa.Column("random_seed", sa.Integer(), nullable=False),
        sa.Column("configuration_json", sa.JSON(), nullable=False),
        sa.Column("configuration_hash", sa.String(64), nullable=False),
        sa.Column("prepared_artifact_checksum", sa.String(64), nullable=False),
        sa.Column("source_dataset_checksum", sa.String(64), nullable=False),
        *[
            sa.Column(x, sa.String(40), nullable=False)
            for x in ("train_start", "train_end", "validation_start", "validation_end", "test_start", "test_end")
        ],
        sa.Column("backtest_fold_count", sa.Integer(), nullable=False),
        sa.Column("selected_model_run_id", sa.String(36)),
        sa.Column("validation_completed_at", sa.DateTime(timezone=True)),
        sa.Column("test_evaluated_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("failure_message", sa.Text()),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["prepared_dataset_id"], ["prepared_datasets.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("prepared_dataset_id", "experiment_version"),
    )
    op.create_index("ix_forecast_prepared_status", "forecast_experiments", ["prepared_dataset_id", "status"])
    op.create_index("ix_forecast_experiments_prepared_dataset_id", "forecast_experiments", ["prepared_dataset_id"])
    op.create_index("ix_forecast_experiments_status", "forecast_experiments", ["status"])
    op.create_table(
        "forecast_model_runs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("experiment_id", sa.String(36), nullable=False),
        sa.Column("model_name", sa.String(80), nullable=False),
        sa.Column("model_family", sa.String(50), nullable=False),
        sa.Column("model_version", sa.String(30), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("hyperparameters_json", sa.JSON(), nullable=False),
        sa.Column("fitted_on", sa.String(30), nullable=False),
        sa.Column("supports_groups", sa.Boolean(), nullable=False),
        sa.Column("supports_trend", sa.Boolean(), nullable=False),
        sa.Column("supports_seasonality", sa.Boolean(), nullable=False),
        sa.Column("artifact_storage_key", sa.String(255)),
        sa.Column("artifact_checksum", sa.String(64)),
        sa.Column("training_duration_ms", sa.Integer(), nullable=False),
        sa.Column("backtest_duration_ms", sa.Integer(), nullable=False),
        sa.Column("validation_metrics_json", sa.JSON(), nullable=False),
        sa.Column("aggregate_backtest_metrics_json", sa.JSON(), nullable=False),
        sa.Column("per_fold_metrics_json", sa.JSON(), nullable=False),
        sa.Column("per_group_metrics_json", sa.JSON(), nullable=False),
        sa.Column("residual_summary_json", sa.JSON(), nullable=False),
        sa.Column("rank", sa.Integer()),
        sa.Column("selection_score", sa.Float()),
        sa.Column("selected", sa.Boolean(), nullable=False),
        sa.Column("failure_message", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(["experiment_id"], ["forecast_experiments.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_forecast_model_runs_experiment_id", "forecast_model_runs", ["experiment_id"])
    op.create_index("ix_forecast_model_runs_status", "forecast_model_runs", ["status"])
    metric_columns = [
        sa.Column(x, sa.Float())
        for x in ("mae", "rmse", "wape", "smape", "mase", "bias", "mean_error", "median_absolute_error")
    ]
    op.create_table(
        "forecast_evaluations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("model_run_id", sa.String(36), nullable=False),
        sa.Column("evaluation_type", sa.String(30), nullable=False),
        sa.Column("split_name", sa.String(30), nullable=False),
        sa.Column("fold_number", sa.Integer()),
        sa.Column("group_value", sa.String(500)),
        sa.Column("horizon", sa.Integer(), nullable=False),
        sa.Column("row_count", sa.Integer(), nullable=False),
        *metric_columns,
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("metrics_json", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["model_run_id"], ["forecast_model_runs.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_forecast_evaluations_model_run_id", "forecast_evaluations", ["model_run_id"])
    op.create_index("ix_forecast_evaluations_evaluation_type", "forecast_evaluations", ["evaluation_type"])
    op.create_table(
        "forecast_prediction_artifacts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("experiment_id", sa.String(36), nullable=False),
        sa.Column("model_run_id", sa.String(36), nullable=False),
        sa.Column("artifact_type", sa.String(40), nullable=False),
        sa.Column("storage_key", sa.String(255), nullable=False),
        sa.Column("checksum", sa.String(64), nullable=False),
        sa.Column("row_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["experiment_id"], ["forecast_experiments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["model_run_id"], ["forecast_model_runs.id"], ondelete="CASCADE"),
    )
    for column in ("experiment_id", "model_run_id", "artifact_type"):
        op.create_index(f"ix_forecast_prediction_artifacts_{column}", "forecast_prediction_artifacts", [column])


def downgrade() -> None:
    op.drop_table("forecast_prediction_artifacts")
    op.drop_table("forecast_evaluations")
    op.drop_table("forecast_model_runs")
    op.drop_index("ix_forecast_prepared_status", table_name="forecast_experiments")
    op.drop_table("forecast_experiments")
