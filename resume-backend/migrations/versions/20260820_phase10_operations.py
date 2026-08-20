"""Add Phase 10 operator roles.

Revision ID: 20260820_phase10
Revises: 20260819_phase9
Create Date: 2026-08-20
"""

from __future__ import annotations

from alembic import op
from sqlalchemy import inspect


revision = "20260820_phase10"
down_revision = "20260819_phase9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    columns = {column["name"] for column in inspect(op.get_bind()).get_columns("users")}
    if "role" not in columns:
        op.execute("ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'user'")


def downgrade() -> None:
    op.drop_column("users", "role")
