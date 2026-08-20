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
    op.execute(
        "CREATE TABLE IF NOT EXISTS push_send_log ("
        "id TEXT PRIMARY KEY, event_type TEXT NOT NULL, "
        "user_id TEXT NOT NULL REFERENCES users(user_id), source_ref TEXT NOT NULL, "
        "target_type TEXT NOT NULL, dispatcher_mode TEXT NOT NULL, status TEXT NOT NULL, "
        "payload_summary TEXT NOT NULL DEFAULT '{}', error_trace TEXT, created_at TEXT NOT NULL, "
        "UNIQUE (event_type, target_type, source_ref))"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_push_send_log_owner_created "
        "ON push_send_log (user_id, created_at DESC, id DESC)"
    )
    op.execute(
        "CREATE TABLE IF NOT EXISTS resume_import ("
        "id TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(user_id), "
        "draft_id TEXT NOT NULL REFERENCES user_draft(id) ON DELETE CASCADE, "
        "stored_filename TEXT NOT NULL, original_filename TEXT NOT NULL, "
        "content_type TEXT NOT NULL, byte_size INTEGER NOT NULL, status TEXT NOT NULL, "
        "parsed_resume_json TEXT NOT NULL, created_at TEXT NOT NULL)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_resume_import_owner_draft_created "
        "ON resume_import (user_id, draft_id, created_at DESC, id DESC)"
    )


def downgrade() -> None:
    op.drop_table("resume_import")
    op.drop_table("push_send_log")
    op.drop_column("users", "role")
