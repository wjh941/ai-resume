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

JOB_CATALOG = (
    (
        "数据工程师",
        "数据与平台",
        ("data engineer", "数据开发工程师", "ETL工程师", "数仓工程师", "工程师"),
        10,
    ),
    (
        "AI Agent工程师",
        "人工智能",
        ("agent工程师", "ai agent engineer", "大模型工程师", "LLM工程师", "工程师"),
        20,
    ),
    (
        "后端开发工程师",
        "软件研发",
        ("backend engineer", "后端工程师", "服务端工程师", "Java工程师", "工程师"),
        30,
    ),
    (
        "前端开发工程师",
        "软件研发",
        ("frontend engineer", "前端工程师", "Vue工程师", "React工程师", "工程师"),
        40,
    ),
    (
        "测试开发工程师",
        "质量工程",
        ("test engineer", "测试工程师", "自动化测试", "SDET", "工程师"),
        50,
    ),
    (
        "算法工程师",
        "人工智能",
        ("algorithm engineer", "机器学习工程师", "深度学习工程师", "工程师"),
        60,
    ),
    (
        "运维开发工程师",
        "云与基础设施",
        ("devops engineer", "运维工程师", "SRE", "平台工程师", "工程师"),
        70,
    ),
    (
        "信息安全工程师",
        "安全",
        ("security engineer", "网络安全工程师", "安全工程师", "工程师"),
        80,
    ),
    (
        "数据分析师",
        "数据与平台",
        ("data analyst", "商业分析师", "BI分析师", "数据分析"),
        90,
    ),
    (
        "产品经理",
        "产品",
        ("product manager", "产品专员", "互联网产品经理", "产品"),
        100,
    ),
    (
        "运营专员",
        "运营",
        ("operations specialist", "运营经理", "内容运营", "用户运营", "运营"),
        110,
    ),
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
                normalized_role TEXT NOT NULL,
                provider_mode TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                created_at TEXT NOT NULL,
                PRIMARY KEY (normalized_role, provider_mode)
            );
            CREATE TABLE IF NOT EXISTS download_file (
                token TEXT PRIMARY KEY,
                file_path TEXT NOT NULL,
                filename TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS job_catalog (
                role_name TEXT PRIMARY KEY,
                category TEXT NOT NULL,
                aliases_json TEXT NOT NULL,
                sort_order INTEGER NOT NULL
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
        connection.executemany(
            """
            INSERT OR IGNORE INTO job_catalog (role_name, category, aliases_json, sort_order)
            VALUES (?, ?, ?, ?)
            """,
            [
                (role_name, category, json.dumps(aliases, ensure_ascii=False), sort_order)
                for role_name, category, aliases, sort_order in JOB_CATALOG
            ],
        )
        _migrate_legacy_job_cache(connection)


def _migrate_legacy_job_cache(connection: sqlite3.Connection) -> None:
    columns = connection.execute("PRAGMA table_info(job_cache)").fetchall()
    primary_key_columns = [
        row["name"] for row in sorted(columns, key=lambda row: row["pk"]) if row["pk"]
    ]
    if primary_key_columns != ["normalized_role"]:
        return

    connection.executescript(
        """
        ALTER TABLE job_cache RENAME TO job_cache_legacy;
        CREATE TABLE job_cache (
            normalized_role TEXT NOT NULL,
            provider_mode TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            created_at TEXT NOT NULL,
            PRIMARY KEY (normalized_role, provider_mode)
        );
        INSERT INTO job_cache (
            normalized_role, provider_mode, payload_json, expires_at, created_at
        )
        SELECT normalized_role, provider_mode, payload_json, expires_at, created_at
        FROM job_cache_legacy;
        DROP TABLE job_cache_legacy;
        """
    )
