"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-05-27
"""

revision = "001"
down_revision = None
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("email", sa.String, unique=True, nullable=False),
        sa.Column("hashed_password", sa.String, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("last_login_at", sa.DateTime, nullable=True),
    )
    op.create_table(
        "sessions",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("user_id", sa.String, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("expires_at", sa.DateTime, nullable=False),
    )
    op.create_table(
        "datasets",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("asin", sa.String, nullable=False),
        sa.Column("product_name", sa.String, nullable=True),
        sa.Column("product_url", sa.String, nullable=True),
        sa.Column("status", sa.String, nullable=False, server_default="pending"),
        sa.Column("scrape_job_id", sa.String, nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("review_count", sa.Integer, nullable=True),
        sa.Column("avg_star_rating", sa.Float, nullable=True),
        sa.Column("review_date_min", sa.String, nullable=True),
        sa.Column("review_date_max", sa.String, nullable=True),
        sa.Column("created_by", sa.String, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("last_scraped_at", sa.DateTime, nullable=True),
    )
    op.create_table(
        "reviews",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("dataset_id", sa.String, sa.ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("external_review_id", sa.String, nullable=False),
        sa.Column("review_text", sa.Text, nullable=False),
        sa.Column("star_rating", sa.Integer, nullable=False),
        sa.Column("reviewer_name", sa.String, nullable=True),
        sa.Column("review_date", sa.String, nullable=True),
        sa.Column("verified_purchase", sa.Boolean, nullable=False, server_default="0"),
        sa.Column("helpful_votes", sa.Integer, nullable=False, server_default="0"),
        sa.Column("sentiment_label", sa.String, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.UniqueConstraint("dataset_id", "external_review_id", name="uq_review_per_dataset"),
    )
    op.create_table(
        "dataset_themes",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("dataset_id", sa.String, sa.ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("theme", sa.String, nullable=False),
        sa.Column("frequency", sa.Integer, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )
    op.create_table(
        "scrape_usage",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("dataset_id", sa.String, sa.ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.String, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("reviews_fetched", sa.Integer, nullable=False),
        sa.Column("fetched_at", sa.DateTime, nullable=False),
    )


def downgrade() -> None:
    op.drop_table("scrape_usage")
    op.drop_table("dataset_themes")
    op.drop_table("reviews")
    op.drop_table("datasets")
    op.drop_table("sessions")
    op.drop_table("users")
