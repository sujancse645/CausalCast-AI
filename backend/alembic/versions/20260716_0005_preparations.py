"""governed time-series preparations

Revision ID: 20260716_0005
Revises: 20260716_0004
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260716_0005"
down_revision: str | None = "20260716_0004"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "prepared_datasets",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("source_dataset_id", sa.String(36), nullable=False),
        sa.Column("source_schema_profile_id", sa.String(36), nullable=False),
        sa.Column("source_quality_report_id", sa.String(36), nullable=False),
        sa.Column("preparation_version", sa.Integer(), nullable=False),
        sa.Column("preparation_engine_version", sa.String(30), nullable=False),
        sa.Column("status", sa.String(10), nullable=False),
        sa.Column("readiness_status", sa.String(22), nullable=False),
        sa.Column("configuration_json", sa.JSON(), nullable=False),
        sa.Column("configuration_hash", sa.String(64), nullable=False),
        sa.Column("source_checksum", sa.String(64), nullable=False),
        sa.Column("prepared_checksum", sa.String(64)),
        sa.Column("storage_key", sa.String(255), nullable=False),
        sa.Column("artifact_format", sa.String(20), nullable=False),
        sa.Column("row_count", sa.Integer(), nullable=False),
        sa.Column("column_count", sa.Integer(), nullable=False),
        sa.Column("feature_count", sa.Integer(), nullable=False),
        sa.Column("target_column", sa.String(255), nullable=False),
        sa.Column("date_column", sa.String(255), nullable=False),
        sa.Column("group_columns_json", sa.JSON(), nullable=False),
        sa.Column("frequency", sa.String(20), nullable=False),
        sa.Column("forecast_horizon", sa.Integer(), nullable=False),
        *[
            sa.Column(x, sa.String(40))
            for x in ("train_start", "train_end", "validation_start", "validation_end", "test_start", "test_end")
        ],
        *[
            sa.Column(x, sa.Integer(), nullable=False)
            for x in ("train_rows", "validation_rows", "test_rows", "dropped_rows", "generated_rows", "duration_ms")
        ],
        sa.Column("warnings_json", sa.JSON(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("failed_at", sa.DateTime(timezone=True)),
        sa.Column("failure_message", sa.Text()),
        sa.Column("superseded_at", sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(["source_dataset_id"], ["datasets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_schema_profile_id"], ["dataset_schema_profiles.id"]),
        sa.ForeignKeyConstraint(["source_quality_report_id"], ["dataset_quality_reports.id"]),
        sa.UniqueConstraint("source_dataset_id", "preparation_version"),
    )
    op.create_index("ix_prepared_source_status", "prepared_datasets", ["source_dataset_id", "status"])
    for name in ("source_dataset_id", "source_schema_profile_id", "source_quality_report_id"):
        op.create_index(f"ix_prepared_datasets_{name}", "prepared_datasets", [name])
    op.create_table(
        "prepared_features",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("prepared_dataset_id", sa.String(36), nullable=False),
        sa.Column("feature_name", sa.String(255), nullable=False),
        sa.Column("source_columns_json", sa.JSON(), nullable=False),
        sa.Column("feature_type", sa.String(40), nullable=False),
        sa.Column("transformation_type", sa.String(50), nullable=False),
        sa.Column("semantic_role", sa.String(50), nullable=False),
        sa.Column("physical_type", sa.String(30), nullable=False),
        sa.Column("availability_type", sa.String(40), nullable=False),
        sa.Column("leakage_risk", sa.String(30), nullable=False),
        sa.Column("included", sa.Boolean(), nullable=False),
        sa.Column("generated", sa.Boolean(), nullable=False),
        sa.Column("parameters_json", sa.JSON(), nullable=False),
        sa.Column("lineage_json", sa.JSON(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["prepared_dataset_id"], ["prepared_datasets.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_prepared_features_prepared_dataset_id", "prepared_features", ["prepared_dataset_id"])
    op.create_table(
        "preparation_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("prepared_dataset_id", sa.String(36), nullable=False),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["prepared_dataset_id"], ["prepared_datasets.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_preparation_events_prepared_dataset_id", "preparation_events", ["prepared_dataset_id"])


def downgrade() -> None:
    op.drop_table("preparation_events")
    op.drop_table("prepared_features")
    op.drop_index("ix_prepared_source_status", table_name="prepared_datasets")
    op.drop_table("prepared_datasets")
