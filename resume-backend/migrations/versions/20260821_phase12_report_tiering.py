"""Add role-aware annual employment insights.

Revision ID: 20260821_phase12
Revises: 20260821_phase11
Create Date: 2026-08-21
"""

from __future__ import annotations

from alembic import context, op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "20260821_phase12"
down_revision = "20260821_phase11"
branch_labels = None
depends_on = None


def upgrade() -> None:
    has_role_name = False
    if not context.is_offline_mode():
        columns = {
            column["name"]
            for column in inspect(op.get_bind()).get_columns("annual_employment_insight")
        }
        has_role_name = "role_name" in columns
    if not has_role_name:
        op.add_column(
            "annual_employment_insight",
            sa.Column(
                "role_name",
                sa.String(length=120),
                nullable=False,
                server_default=sa.text("''"),
            ),
        )


def downgrade() -> None:
    with op.batch_alter_table("annual_employment_insight") as batch:
        batch.drop_column("role_name")
