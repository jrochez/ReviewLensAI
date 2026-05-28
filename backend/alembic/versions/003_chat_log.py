"""Add chat_logs audit table

Revision ID: 003
Revises: 002
Create Date: 2026-05-27
"""

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade() -> None:
    op.create_table(
        "chat_logs",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("dataset_id", sa.String, sa.ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.String, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("user_message", sa.Text, nullable=False),
        sa.Column("assistant_reply", sa.Text, nullable=False),
        sa.Column("scope_refused", sa.Boolean, nullable=False, server_default="0"),
        sa.Column("history_length", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )
    op.create_index("ix_chat_logs_dataset_id", "chat_logs", ["dataset_id"])
    op.create_index("ix_chat_logs_user_id", "chat_logs", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_chat_logs_user_id", table_name="chat_logs")
    op.drop_index("ix_chat_logs_dataset_id", table_name="chat_logs")
    op.drop_table("chat_logs")
