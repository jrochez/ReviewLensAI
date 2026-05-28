"""Seed initial user from environment variables

Revision ID: 002
Revises: 001
Create Date: 2026-05-27
"""

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None

import os
from datetime import datetime
from uuid import uuid4

from alembic import op
import bcrypt
import sqlalchemy as sa


def upgrade() -> None:
    email = os.environ.get("INITIAL_USER_EMAIL", "").lower().strip()
    password = os.environ.get("INITIAL_USER_PASSWORD", "")

    if not email or not password:
        return

    conn = op.get_bind()
    exists = conn.execute(
        sa.text("SELECT id FROM users WHERE email = :email"),
        {"email": email},
    ).fetchone()

    if exists:
        return

    conn.execute(
        sa.text(
            "INSERT INTO users (id, email, hashed_password, created_at)"
            " VALUES (:id, :email, :hashed_password, :created_at)"
        ),
        {
            "id": str(uuid4()),
            "email": email,
            "hashed_password": bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode(),
            "created_at": datetime.utcnow().isoformat(),
        },
    )


def downgrade() -> None:
    email = os.environ.get("INITIAL_USER_EMAIL", "").lower().strip()
    if not email:
        return

    conn = op.get_bind()
    conn.execute(
        sa.text("DELETE FROM users WHERE email = :email"),
        {"email": email},
    )
