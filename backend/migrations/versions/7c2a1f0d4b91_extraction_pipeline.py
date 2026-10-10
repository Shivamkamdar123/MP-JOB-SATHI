"""extraction provenance and source hashes

Revision ID: 7c2a1f0d4b91
Revises: 23883486fee3
Create Date: 2026-10-08

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "7c2a1f0d4b91"
down_revision: Union[str, Sequence[str], None] = "23883486fee3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("notifications") as batch_op:
        batch_op.alter_column("title", existing_type=sa.String(length=500), nullable=True)
        batch_op.alter_column("status", existing_type=sa.String(length=40), nullable=True)
    with op.batch_alter_table("posts") as batch_op:
        batch_op.alter_column("title", existing_type=sa.String(length=500), nullable=True)
    with op.batch_alter_table("field_provenance") as batch_op:
        batch_op.add_column(sa.Column("source_page", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("confidence", sa.Float(), nullable=False, server_default="0"))
        batch_op.add_column(sa.Column("method", sa.String(length=20), nullable=False, server_default="regex"))

    op.create_table(
        "source_hashes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("content_sha256", sa.String(length=64), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("notification_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["notification_id"], ["notifications.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source_url"),
    )
    op.create_index("ix_source_hashes_source_url", "source_hashes", ["source_url"], unique=True)
    op.create_index("ix_source_hashes_notification_id", "source_hashes", ["notification_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_source_hashes_notification_id", table_name="source_hashes")
    op.drop_index("ix_source_hashes_source_url", table_name="source_hashes")
    op.drop_table("source_hashes")
    with op.batch_alter_table("field_provenance") as batch_op:
        batch_op.drop_column("method")
        batch_op.drop_column("confidence")
        batch_op.drop_column("source_page")
    with op.batch_alter_table("posts") as batch_op:
        batch_op.alter_column("title", existing_type=sa.String(length=500), nullable=False)
    with op.batch_alter_table("notifications") as batch_op:
        batch_op.alter_column("status", existing_type=sa.String(length=40), nullable=False)
        batch_op.alter_column("title", existing_type=sa.String(length=500), nullable=False)