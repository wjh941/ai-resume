from __future__ import annotations

import json
from pathlib import Path
import sqlite3


TEMPLATES = (
    ("business", "Business", "A clear, conservative business resume.", {"accent": "navy"}),
    ("technology", "Technology", "A skills-forward technical resume.", {"accent": "teal"}),
    ("graduate", "Graduate", "An education-first graduate resume.", {"accent": "green"}),
    ("analytics", "Analytics", "An analytical, data-oriented resume.", {"accent": "blue"}),
)


def connect(database_path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database(database_path: Path) -> None:
    database_path.parent.mkdir(parents=True, exist_ok=True)
    with connect(database_path) as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS user_draft (
                id TEXT PRIMARY KEY,
                client_id TEXT NOT NULL,
                job_title TEXT NOT NULL,
                template_id TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS template_table (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                config_json TEXT NOT NULL,
                docx_template_path TEXT,
                active INTEGER NOT NULL DEFAULT 1
            );
            CREATE TABLE IF NOT EXISTS job_cache (
                normalized_role TEXT PRIMARY KEY,
                provider_mode TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )
        connection.executemany(
            """
            INSERT OR IGNORE INTO template_table (id, name, description, config_json)
            VALUES (?, ?, ?, ?)
            """,
            [(template_id, name, description, json.dumps(config)) for template_id, name, description, config in TEMPLATES],
        )
