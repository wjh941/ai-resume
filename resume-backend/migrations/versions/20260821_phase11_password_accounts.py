"""Add password-account authentication storage.

Revision ID: 20260821_phase11
Revises: 20260820_phase10
Create Date: 2026-08-20
"""

from __future__ import annotations

from alembic import op


revision = "20260821_phase11"
down_revision = "20260820_phase10"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "CREATE TABLE IF NOT EXISTS password_account ("
        "account TEXT PRIMARY KEY, user_id TEXT NOT NULL UNIQUE REFERENCES users(user_id), "
        "password_hash TEXT NOT NULL, created_at TEXT NOT NULL, last_login TEXT NOT NULL)"
    )


def downgrade() -> None:
    op.drop_table("password_account")
