"""Create governed datasets table."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260715_0002"
down_revision: str | None = "20260715_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "datasets",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("stored_filename", sa.String(length=64), nullable=False),
        sa.Column("storage_key", sa.String(length=255), nullable=False),
        sa.Column("file_extension", sa.String(length=10), nullable=False),
        sa.Column("mime_type", sa.String(length=100), nullable=False),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("checksum_sha256", sa.String(length=64), nullable=False),
        sa.Column("row_count", sa.BigInteger(), nullable=False),
        sa.Column("column_count", sa.Integer(), nullable=False),
        sa.Column("column_names", sa.JSON(), nullable=False),
        sa.Column("delimiter", sa.String(length=10), nullable=True),
        sa.Column("encoding", sa.String(length=30), nullable=True),
        sa.Column(
            "status",
            sa.Enum("uploading", "validating", "ready", "failed", "archived", name="datasetstatus"),
            nullable=False,
        ),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ingestion_version", sa.Integer(), nullable=False),
        sa.Column("source_type", sa.String(length=30), nullable=False),
        sa.Column("preview_available", sa.Boolean(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("preview_json", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("storage_key"),
        sa.UniqueConstraint("stored_filename"),
    )
    op.create_index(op.f("ix_datasets_checksum_sha256"), "datasets", ["checksum_sha256"], unique=True)
    op.create_index(op.f("ix_datasets_status"), "datasets", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_datasets_status"), table_name="datasets")
    op.drop_index(op.f("ix_datasets_checksum_sha256"), table_name="datasets")
    op.drop_table("datasets")
