"""deep forecasting infrastructure and readiness foundation

Revision ID: 20260717_0008
Revises: 20260716_0007
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260717_0008"
down_revision: str | None = "20260716_0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    experiment_columns = [
        sa.Column("experiment_family", sa.String(40), nullable=False, server_default="classical"),
        sa.Column("deep_forecasting_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("deep_engine", sa.String(40), nullable=True),
        sa.Column("deep_data_config_json", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("deep_runtime_config_json", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("deep_readiness_status", sa.String(40), nullable=True),
    ]
    run_columns = [
        sa.Column("model_framework", sa.String(50), nullable=True),
        sa.Column("model_architecture", sa.String(80), nullable=True),
        sa.Column("accelerator", sa.String(20), nullable=True),
        sa.Column("device_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("deterministic", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("input_size", sa.Integer(), nullable=True),
        sa.Column("sequence_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("parameter_count", sa.Integer(), nullable=True),
        sa.Column("checkpoint_available", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("checkpoint_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("checkpoint_checksum", sa.String(64), nullable=True),
        sa.Column("training_framework_version", sa.String(50), nullable=True),
        sa.Column("torch_version", sa.String(50), nullable=True),
        sa.Column("cuda_version", sa.String(50), nullable=True),
        sa.Column("deep_model_status", sa.String(40), nullable=True),
    ]
    for column in experiment_columns:
        op.add_column("forecast_experiments", column)
    for column in run_columns:
        op.add_column("forecast_model_runs", column)
    op.create_table(
        "deep_forecast_checkpoints",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("model_run_id", sa.String(36), nullable=False),
        sa.Column("checkpoint_type", sa.String(30), nullable=False),
        sa.Column("epoch", sa.Integer(), nullable=True),
        sa.Column("global_step", sa.Integer(), nullable=True),
        sa.Column("monitored_metric", sa.String(50), nullable=True),
        sa.Column("monitored_value", sa.Float(), nullable=True),
        sa.Column("artifact_id", sa.String(36), nullable=True),
        sa.Column("checksum", sa.String(64), nullable=False),
        sa.Column("file_size_bytes", sa.Integer(), nullable=False),
        sa.Column("framework_version", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["model_run_id"], ["forecast_model_runs.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_deep_forecast_checkpoints_model_run_id", "deep_forecast_checkpoints", ["model_run_id"])
    op.create_table(
        "deep_forecast_readiness_snapshots",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("prepared_dataset_id", sa.String(36), nullable=False),
        sa.Column("readiness_status", sa.String(40), nullable=False),
        sa.Column("engine", sa.String(40), nullable=False),
        sa.Column("model_name", sa.String(60), nullable=False),
        sa.Column("target_column", sa.String(255), nullable=False),
        sa.Column("time_column", sa.String(255), nullable=False),
        sa.Column("group_columns_json", sa.JSON(), nullable=False),
        sa.Column("horizon", sa.Integer(), nullable=False),
        sa.Column("input_size", sa.Integer(), nullable=False),
        sa.Column("series_count", sa.Integer(), nullable=False),
        sa.Column("eligible_series_count", sa.Integer(), nullable=False),
        sa.Column("historical_covariates_json", sa.JSON(), nullable=False),
        sa.Column("future_covariates_json", sa.JSON(), nullable=False),
        sa.Column("static_covariates_json", sa.JSON(), nullable=False),
        sa.Column("warnings_json", sa.JSON(), nullable=False),
        sa.Column("blockers_json", sa.JSON(), nullable=False),
        sa.Column("report_json", sa.JSON(), nullable=False),
        sa.Column("artifact_checksums_json", sa.JSON(), nullable=False),
        sa.Column("checksum", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["prepared_dataset_id"], ["prepared_datasets.id"], ondelete="CASCADE"),
    )
    op.create_index(
        "ix_deep_forecast_readiness_snapshots_prepared_dataset_id",
        "deep_forecast_readiness_snapshots",
        ["prepared_dataset_id"],
    )
    op.create_index(
        "ix_deep_forecast_readiness_snapshots_readiness_status",
        "deep_forecast_readiness_snapshots",
        ["readiness_status"],
    )
    op.create_index(
        "ix_deep_readiness_prepared_created",
        "deep_forecast_readiness_snapshots",
        ["prepared_dataset_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_deep_readiness_prepared_created", table_name="deep_forecast_readiness_snapshots")
    op.drop_index(
        "ix_deep_forecast_readiness_snapshots_readiness_status", table_name="deep_forecast_readiness_snapshots"
    )
    op.drop_index(
        "ix_deep_forecast_readiness_snapshots_prepared_dataset_id", table_name="deep_forecast_readiness_snapshots"
    )
    op.drop_table("deep_forecast_readiness_snapshots")
    op.drop_index("ix_deep_forecast_checkpoints_model_run_id", table_name="deep_forecast_checkpoints")
    op.drop_table("deep_forecast_checkpoints")
    for name in (
        "deep_model_status",
        "cuda_version",
        "torch_version",
        "training_framework_version",
        "checkpoint_checksum",
        "checkpoint_count",
        "checkpoint_available",
        "parameter_count",
        "sequence_count",
        "input_size",
        "deterministic",
        "device_count",
        "accelerator",
        "model_architecture",
        "model_framework",
    ):
        op.drop_column("forecast_model_runs", name)
    for name in (
        "deep_readiness_status",
        "deep_runtime_config_json",
        "deep_data_config_json",
        "deep_engine",
        "deep_forecasting_enabled",
        "experiment_family",
    ):
        op.drop_column("forecast_experiments", name)
