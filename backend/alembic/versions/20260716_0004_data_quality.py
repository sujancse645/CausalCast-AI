"""Create versioned data-quality reports. Revision ID: 20260716_0004."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260716_0004"
down_revision: str | None = "20260715_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "dataset_quality_reports",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("dataset_id", sa.String(36), sa.ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False),
        sa.Column(
            "schema_profile_id",
            sa.String(36),
            sa.ForeignKey("dataset_schema_profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("report_version", sa.Integer(), nullable=False),
        sa.Column("quality_engine_version", sa.String(30), nullable=False),
        sa.Column(
            "status",
            sa.Enum("pending", "running", "completed", "failed", "superseded", name="qualityreportstatus"),
            nullable=False,
        ),
        sa.Column(
            "readiness_status",
            sa.Enum(
                "not_analyzed",
                "blocked",
                "needs_attention",
                "conditionally_ready",
                "quality_ready",
                name="qualityreadiness",
            ),
            nullable=False,
        ),
        *[
            sa.Column(n, sa.Float(), nullable=False)
            for n in (
                "overall_score",
                "completeness_score",
                "validity_score",
                "consistency_score",
                "uniqueness_score",
                "temporal_score",
                "integrity_score",
                "leakage_safety_score",
            )
        ],
        *[
            sa.Column(n, sa.Integer(), nullable=False)
            for n in (
                "total_findings",
                "blocker_count",
                "error_count",
                "warning_count",
                "info_count",
                "scanned_rows",
                "total_rows",
                "analyzed_columns",
                "schema_version",
                "duration_ms",
            )
        ],
        sa.Column("scan_coverage_ratio", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("superseded_at", sa.DateTime(timezone=True)),
        sa.Column("dataset_checksum", sa.String(64), nullable=False),
        sa.Column("configuration_hash", sa.String(64), nullable=False),
        sa.Column("summary_json", sa.JSON(), nullable=False),
        sa.Column("recommendations_json", sa.JSON(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("failure_message", sa.Text()),
        sa.UniqueConstraint("dataset_id", "report_version"),
    )
    for name, cols in (
        ("ix_quality_dataset_status", ["dataset_id", "status"]),
        ("ix_dataset_quality_reports_dataset_id", ["dataset_id"]),
        ("ix_dataset_quality_reports_schema_profile_id", ["schema_profile_id"]),
        ("ix_dataset_quality_reports_status", ["status"]),
        ("ix_dataset_quality_reports_readiness_status", ["readiness_status"]),
    ):
        op.create_index(name, "dataset_quality_reports", cols)
    op.create_table(
        "dataset_quality_findings",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "quality_report_id",
            sa.String(36),
            sa.ForeignKey("dataset_quality_reports.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("dataset_id", sa.String(36), sa.ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("rule_code", sa.String(50), nullable=False),
        sa.Column("category", sa.String(40), nullable=False),
        sa.Column("severity", sa.Enum("blocker", "error", "warning", "info", name="qualityseverity"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("affected_column", sa.String(255)),
        sa.Column("related_columns_json", sa.JSON(), nullable=False),
        sa.Column("affected_row_count", sa.Integer()),
        sa.Column("affected_ratio", sa.Float()),
        sa.Column("sample_row_indices_json", sa.JSON(), nullable=False),
        sa.Column("evidence_json", sa.JSON(), nullable=False),
        sa.Column("threshold_json", sa.JSON(), nullable=False),
        sa.Column("recommendation", sa.Text(), nullable=False),
        sa.Column("blocking", sa.Boolean(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    for name, cols in (
        ("ix_quality_finding_filter", ["quality_report_id", "category", "severity"]),
        ("ix_dataset_quality_findings_quality_report_id", ["quality_report_id"]),
        ("ix_dataset_quality_findings_dataset_id", ["dataset_id"]),
        ("ix_dataset_quality_findings_rule_code", ["rule_code"]),
        ("ix_dataset_quality_findings_category", ["category"]),
        ("ix_dataset_quality_findings_severity", ["severity"]),
        ("ix_dataset_quality_findings_affected_column", ["affected_column"]),
        ("ix_dataset_quality_findings_blocking", ["blocking"]),
    ):
        op.create_index(name, "dataset_quality_findings", cols)


def downgrade() -> None:
    op.drop_table("dataset_quality_findings")
    op.drop_table("dataset_quality_reports")
