from __future__ import annotations

import argparse
from pathlib import Path
import sqlite3


TABLES = (
    "users", "template_table", "job_catalog", "role_profile", "major_catalog", "official_dataset_source",
    "user_draft", "resume_evidence", "application_tracker", "career_profile", "career_assessment",
    "user_vip", "order_record", "job_favorite", "job_match_subscription", "job_cache",
    "annual_employment_insight", "knowledge_sync_run",
)
BOOLEAN_COLUMNS = {"users": {"is_deleted"}, "resume_evidence": {"verified"}, "template_table": {"active"}, "user_vip": {"auto_renew"}, "order_record": {"auto_renew"}, "job_match_subscription": {"enabled"}, "official_dataset_source": {"enabled"}}


def copy_database(sqlite_path: Path, database_url: str) -> None:
    try:
        import psycopg
        from psycopg.rows import dict_row
    except ImportError as error:
        raise RuntimeError("Install psycopg before migrating SQLite data to PostgreSQL.") from error
    if not sqlite_path.is_file():
        raise FileNotFoundError(sqlite_path)
    with sqlite3.connect(sqlite_path) as source, psycopg.connect(database_url.replace("postgresql+psycopg://", "postgresql://", 1), row_factory=dict_row) as target:
        source.row_factory = sqlite3.Row
        for table in TABLES:
            columns = [row["name"] for row in source.execute(f"PRAGMA table_info({table})")]
            if not columns:
                continue
            if target.execute(f"SELECT 1 FROM {table} LIMIT 1").fetchone() is not None:
                raise RuntimeError(f"PostgreSQL target table '{table}' is not empty.")
            rows = source.execute(f"SELECT * FROM {table}").fetchall()
            if not rows:
                continue
            values = []
            for row in rows:
                values.append(tuple(bool(row[column]) if column in BOOLEAN_COLUMNS.get(table, set()) and row[column] is not None else row[column] for column in columns))
            quoted_columns = ", ".join(columns)
            placeholders = ", ".join("%s" for _ in columns)
            target.executemany(f"INSERT INTO {table} ({quoted_columns}) VALUES ({placeholders})", values)
        for table in ("annual_employment_insight", "knowledge_sync_run"):
            target.execute(f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), COALESCE((SELECT MAX(id) FROM {table}), 1), true)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Copy an initialized SQLite database into an empty Alembic-migrated PostgreSQL database.")
    parser.add_argument("--sqlite-path", required=True, type=Path)
    parser.add_argument("--database-url", required=True)
    arguments = parser.parse_args()
    copy_database(arguments.sqlite_path, arguments.database_url)
    print("SQLite data copied to PostgreSQL. Validate counts and application login before switching traffic.")
