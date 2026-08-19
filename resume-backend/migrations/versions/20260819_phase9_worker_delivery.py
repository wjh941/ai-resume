"""Add Phase 9 worker, delivery, version, and task storage.

Revision ID: 20260819_phase9
Revises: 20260819_phase8
Create Date: 2026-08-19
"""

from __future__ import annotations

from alembic import op


revision = "20260819_phase9"
down_revision = "20260819_phase8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    statements = (
        "ALTER TABLE application_tracker ADD COLUMN contact_info TEXT NOT NULL DEFAULT ''",
        "ALTER TABLE application_tracker ADD COLUMN attachment_ref TEXT NOT NULL DEFAULT ''",
        "ALTER TABLE application_tracker ADD COLUMN timeline_json TEXT NOT NULL DEFAULT '[]'",
        "ALTER TABLE application_tracker ADD COLUMN next_interview_at TEXT",
        "CREATE TABLE IF NOT EXISTS interview_reminder (id TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(user_id), application_id TEXT NOT NULL REFERENCES application_tracker(id) ON DELETE CASCADE, reminder_at TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'pending', created_at TEXT NOT NULL, updated_at TEXT NOT NULL)",
        "CREATE INDEX IF NOT EXISTS idx_interview_reminder_owner_due ON interview_reminder (user_id, status, reminder_at ASC)",
        "CREATE TABLE IF NOT EXISTS resume_version (id TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(user_id), draft_id TEXT NOT NULL REFERENCES user_draft(id) ON DELETE CASCADE, note TEXT NOT NULL DEFAULT '', payload_json TEXT NOT NULL, is_active BOOLEAN NOT NULL DEFAULT FALSE, created_at TEXT NOT NULL)",
        "CREATE INDEX IF NOT EXISTS idx_resume_version_owner_draft_created ON resume_version (user_id, draft_id, created_at DESC, id DESC)",
        "CREATE TABLE IF NOT EXISTS career_task (id TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(user_id), plan_id TEXT NOT NULL, title TEXT NOT NULL, description TEXT NOT NULL DEFAULT '', due_date TEXT, status TEXT NOT NULL DEFAULT 'pending', link_to_application_id TEXT, link_to_evidence_id TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL)",
        "CREATE INDEX IF NOT EXISTS idx_career_task_owner_plan_due ON career_task (user_id, plan_id, status, due_date ASC, updated_at DESC)",
        "CREATE TABLE IF NOT EXISTS background_task_lock (task_name TEXT PRIMARY KEY, owner_id TEXT NOT NULL, lease_expires_at TEXT NOT NULL, updated_at TEXT NOT NULL)",
        "CREATE TABLE IF NOT EXISTS job_match_alert (id TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(user_id), alert_key TEXT NOT NULL UNIQUE, match_filter TEXT NOT NULL DEFAULT '', status TEXT NOT NULL DEFAULT 'pending', created_at TEXT NOT NULL)",
        "CREATE INDEX IF NOT EXISTS idx_job_match_alert_owner_created ON job_match_alert (user_id, created_at DESC, id DESC)",
    )
    for statement in statements:
        op.execute(statement)


def downgrade() -> None:
    for table in (
        "job_match_alert",
        "background_task_lock",
        "career_task",
        "resume_version",
        "interview_reminder",
    ):
        op.drop_table(table)
