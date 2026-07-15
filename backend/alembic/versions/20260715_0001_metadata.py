"""Create application metadata table."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260715_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "application_metadata",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("key", sa.String(length=100), nullable=False),
        sa.Column("value", sa.String(length=500), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_application_metadata_key"), "application_metadata", ["key"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_application_metadata_key"), table_name="application_metadata")
    op.drop_table("application_metadata")
