"""Create versioned schema mapping tables."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260715_0003"
down_revision: str | None = "20260715_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "dataset_schema_profiles",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("dataset_id", sa.String(36), sa.ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("schema_version", sa.Integer, nullable=False),
        sa.Column("inference_version", sa.String(30), nullable=False),
        sa.Column(
            "status",
            sa.Enum("pending", "inferred", "needs_review", "confirmed", "superseded", "failed", name="schemastatus"),
            nullable=False,
        ),
        sa.Column("total_columns", sa.Integer, nullable=False),
        sa.Column("mapped_columns", sa.Integer, nullable=False),
        sa.Column("confirmed_columns", sa.Integer, nullable=False),
        sa.Column("unresolved_columns", sa.Integer, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by_type", sa.String(30), nullable=False),
        sa.Column("profile_summary_json", sa.JSON, nullable=False),
        sa.Column("warnings_json", sa.JSON, nullable=False),
        sa.Column("configuration_json", sa.JSON, nullable=False),
        sa.Column("source_checksum", sa.String(64), nullable=False),
        sa.Column("sample_row_count", sa.Integer, nullable=False),
        sa.Column("rerun_reason", sa.String(500), nullable=True),
        sa.UniqueConstraint("dataset_id", "schema_version"),
    )
    op.create_index("ix_schema_dataset_status", "dataset_schema_profiles", ["dataset_id", "status"])
    op.create_index(op.f("ix_dataset_schema_profiles_dataset_id"), "dataset_schema_profiles", ["dataset_id"])
    op.create_index(op.f("ix_dataset_schema_profiles_status"), "dataset_schema_profiles", ["status"])
    op.create_table(
        "dataset_column_profiles",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "schema_profile_id",
            sa.String(36),
            sa.ForeignKey("dataset_schema_profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("dataset_id", sa.String(36), sa.ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("column_index", sa.Integer, nullable=False),
        sa.Column("column_name", sa.String(255), nullable=False),
        sa.Column("normalized_column_name", sa.String(255), nullable=False),
        sa.Column(
            "physical_type",
            sa.Enum(
                "integer",
                "float",
                "boolean",
                "date",
                "datetime",
                "categorical",
                "identifier",
                "text",
                "empty",
                "mixed",
                "unknown",
                name="physicaltype",
            ),
            nullable=False,
        ),
        sa.Column("semantic_role", sa.String(50), nullable=False),
        sa.Column("confidence_score", sa.Float, nullable=False),
        sa.Column(
            "confirmation_status",
            sa.Enum(
                "proposed", "confirmed", "manually_overridden", "rejected", "unresolved", name="confirmationstatus"
            ),
            nullable=False,
        ),
        sa.Column(
            "decision_source",
            sa.Enum(
                "deterministic_inference", "user_confirmation", "user_override", "system_default", name="decisionsource"
            ),
            nullable=False,
        ),
        sa.Column("nullable", sa.Boolean, nullable=False),
        sa.Column("null_count", sa.Integer, nullable=False),
        sa.Column("sample_count", sa.Integer, nullable=False),
        sa.Column("unique_count", sa.Integer, nullable=False),
        sa.Column("parse_success_rate", sa.Float, nullable=False),
        sa.Column("numeric_min", sa.Float, nullable=True),
        sa.Column("numeric_max", sa.Float, nullable=True),
        sa.Column("numeric_mean", sa.Float, nullable=True),
        sa.Column("date_min", sa.String(40), nullable=True),
        sa.Column("date_max", sa.String(40), nullable=True),
        sa.Column("string_min_length", sa.Integer, nullable=True),
        sa.Column("string_max_length", sa.Integer, nullable=True),
        sa.Column("sample_values_json", sa.JSON, nullable=False),
        sa.Column("evidence_json", sa.JSON, nullable=False),
        sa.Column("alternatives_json", sa.JSON, nullable=False),
        sa.Column("warnings_json", sa.JSON, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("schema_profile_id", "column_index"),
    )
    op.create_index(
        op.f("ix_dataset_column_profiles_schema_profile_id"), "dataset_column_profiles", ["schema_profile_id"]
    )
    op.create_index(op.f("ix_dataset_column_profiles_dataset_id"), "dataset_column_profiles", ["dataset_id"])
    op.create_table(
        "schema_mapping_audits",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "schema_profile_id",
            sa.String(36),
            sa.ForeignKey("dataset_schema_profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "column_profile_id",
            sa.String(36),
            sa.ForeignKey("dataset_column_profiles.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("action_type", sa.String(50), nullable=False),
        sa.Column("schema_version", sa.Integer, nullable=False),
        sa.Column("column_name", sa.String(255), nullable=True),
        sa.Column("old_role", sa.String(50), nullable=True),
        sa.Column("new_role", sa.String(50), nullable=True),
        sa.Column("source", sa.String(30), nullable=False),
        sa.Column("reason", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(op.f("ix_schema_mapping_audits_schema_profile_id"), "schema_mapping_audits", ["schema_profile_id"])


def downgrade() -> None:
    op.drop_table("schema_mapping_audits")
    op.drop_table("dataset_column_profiles")
    op.drop_table("dataset_schema_profiles")
