from __future__ import annotations

import json
from pathlib import Path
import sqlite3

from app.services.career_catalog import ROLE_SEEDS, seed_career_catalog


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
        "数据库运维工程师",
        "数据与平台",
        ("database operations", "dba", "数据库管理员", "数据库运维", "数据"),
        95,
    ),
    (
        "数据清洗专员",
        "数据与平台",
        ("data cleaning", "数据处理", "数据质检", "数据清洗", "数据"),
        96,
    ),
    (
        "数据标注专员",
        "人工智能",
        ("data annotation", "数据标注", "标注员", "数据"),
        97,
    ),
    (
        "数据质量工程师",
        "数据与平台",
        ("data quality engineer", "数据质量", "数据治理", "数据"),
        98,
    ),
    (
        "数据治理工程师",
        "数据与平台",
        ("data governance", "数据治理", "主数据", "数据"),
        99,
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
    # 本期 SQLite 必须逐连接启用外键；二期数据库迁移由同一仓储 user_id 接口承接。
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database(database_path: Path) -> None:
    database_path.parent.mkdir(parents=True, exist_ok=True)
    with connect(database_path) as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                phone TEXT NOT NULL UNIQUE,
                token_version INTEGER NOT NULL DEFAULT 1 CHECK (token_version >= 1),
                created_at TEXT NOT NULL,
                last_login TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS user_draft (
                id TEXT PRIMARY KEY,
                client_id TEXT NOT NULL,
                user_id TEXT REFERENCES users(user_id),
                job_title TEXT NOT NULL,
                template_id TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS resume_evidence (
                id TEXT PRIMARY KEY,
                client_id TEXT NOT NULL,
                user_id TEXT REFERENCES users(user_id),
                kind TEXT NOT NULL,
                title TEXT NOT NULL,
                context TEXT NOT NULL,
                actions TEXT NOT NULL,
                outcome TEXT NOT NULL,
                proof_note TEXT NOT NULL,
                verified INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_resume_evidence_client_updated
            ON resume_evidence (client_id, updated_at DESC, id DESC);
            CREATE TABLE IF NOT EXISTS application_tracker (
                id TEXT PRIMARY KEY,
                client_id TEXT NOT NULL,
                user_id TEXT REFERENCES users(user_id),
                company TEXT NOT NULL,
                role_name TEXT NOT NULL,
                city TEXT NOT NULL,
                source TEXT NOT NULL,
                status TEXT NOT NULL,
                applied_at TEXT,
                next_action_at TEXT,
                interview_notes TEXT NOT NULL,
                draft_id TEXT,
                notes TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_application_tracker_client_status
            ON application_tracker (client_id, status, next_action_at, updated_at DESC);
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
                user_id TEXT REFERENCES users(user_id),
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
            CREATE TABLE IF NOT EXISTS role_profile (
                role_name TEXT PRIMARY KEY,
                family TEXT NOT NULL,
                aliases_json TEXT NOT NULL,
                recommended_majors_json TEXT NOT NULL,
                adjacent_majors_json TEXT NOT NULL,
                relevant_courses_json TEXT NOT NULL,
                required_skills_json TEXT NOT NULL,
                entry_skills_json TEXT NOT NULL,
                alternative_roles_json TEXT NOT NULL,
                internship_roles_json TEXT NOT NULL,
                entry_difficulty INTEGER NOT NULL CHECK (entry_difficulty BETWEEN 1 AND 5),
                industry_tags_json TEXT NOT NULL,
                description TEXT NOT NULL,
                catalog_origin TEXT NOT NULL DEFAULT 'seed',
                source_key TEXT,
                source_version TEXT,
                source_url TEXT,
                updated_at TEXT
            );
            CREATE TABLE IF NOT EXISTS major_catalog (
                major_name TEXT PRIMARY KEY,
                category TEXT NOT NULL,
                aliases_json TEXT NOT NULL,
                related_families_json TEXT NOT NULL,
                transferable_skills_json TEXT NOT NULL,
                catalog_origin TEXT NOT NULL DEFAULT 'seed',
                source_key TEXT,
                source_version TEXT,
                source_url TEXT,
                updated_at TEXT
            );
            CREATE TABLE IF NOT EXISTS career_profile (
                client_id TEXT PRIMARY KEY,
                user_id TEXT REFERENCES users(user_id),
                identity_code TEXT NOT NULL,
                major TEXT NOT NULL,
                education_level TEXT NOT NULL,
                graduation_year INTEGER,
                city_preferences_json TEXT NOT NULL,
                minimum_salary TEXT,
                industry_preferences_json TEXT NOT NULL,
                work_types_json TEXT NOT NULL,
                skills_json TEXT NOT NULL,
                draft_id TEXT,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS career_assessment (
                client_id TEXT PRIMARY KEY,
                user_id TEXT REFERENCES users(user_id),
                assessment_version INTEGER NOT NULL,
                answers_json TEXT NOT NULL,
                result_json TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS annual_employment_insight (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                year INTEGER NOT NULL,
                scope TEXT NOT NULL,
                audience TEXT NOT NULL,
                category TEXT NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                source_label TEXT NOT NULL,
                publication_date TEXT NOT NULL,
                confidence_note TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS official_dataset_source (
                source_key TEXT PRIMARY KEY,
                display_name TEXT NOT NULL,
                direct_url TEXT,
                allowed_hosts_json TEXT NOT NULL DEFAULT '[]',
                file_format TEXT NOT NULL,
                parser_kind TEXT NOT NULL,
                enabled INTEGER NOT NULL DEFAULT 0,
                disabled_reason TEXT,
                last_version TEXT,
                last_checksum TEXT,
                last_synced_at TEXT
            );
            CREATE TABLE IF NOT EXISTS knowledge_sync_run (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mode TEXT NOT NULL,
                status TEXT NOT NULL,
                started_at TEXT NOT NULL,
                completed_at TEXT,
                added_roles INTEGER NOT NULL DEFAULT 0,
                added_majors INTEGER NOT NULL DEFAULT 0,
                skipped_rows INTEGER NOT NULL DEFAULT 0,
                errors_json TEXT NOT NULL DEFAULT '[]'
            );
            """
        )
        _migrate_user_ownership(connection)
        _migrate_catalog_provenance(connection)
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
        seed_career_catalog(connection)
        connection.executemany(
            """
            INSERT OR IGNORE INTO job_catalog (role_name, category, aliases_json, sort_order)
            VALUES (?, ?, ?, ?)
            """,
            [
                (
                    role.role_name,
                    role.family,
                    json.dumps(role.aliases, ensure_ascii=False),
                    1_000 + index,
                )
                for index, role in enumerate(ROLE_SEEDS)
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


def _migrate_catalog_provenance(connection: sqlite3.Connection) -> None:
    migrations = {
        "role_profile": (
            ("catalog_origin", "TEXT NOT NULL DEFAULT 'seed'"),
            ("source_key", "TEXT"),
            ("source_version", "TEXT"),
            ("source_url", "TEXT"),
            ("updated_at", "TEXT"),
        ),
        "major_catalog": (
            ("catalog_origin", "TEXT NOT NULL DEFAULT 'seed'"),
            ("source_key", "TEXT"),
            ("source_version", "TEXT"),
            ("source_url", "TEXT"),
            ("updated_at", "TEXT"),
        ),
    }
    for table, columns in migrations.items():
        existing = {str(row["name"]) for row in connection.execute(f"PRAGMA table_info({table})")}
        for column, definition in columns:
            if column not in existing:
                connection.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def _migrate_user_ownership(connection: sqlite3.Connection) -> None:
    """本期 SQLite 增量迁移：历史未归属记录保留 NULL，绝不自动分配给新账号。"""
    owned_tables = (
        "user_draft",
        "resume_evidence",
        "application_tracker",
        "career_profile",
        "career_assessment",
        "download_file",
    )
    for table in owned_tables:
        columns = {str(row["name"]) for row in connection.execute(f"PRAGMA table_info({table})")}
        if "user_id" not in columns:
            connection.execute(
                f"ALTER TABLE {table} ADD COLUMN user_id TEXT REFERENCES users(user_id)"
            )

    # 二期迁移 MySQL/PostgreSQL 时保留这些 owner-first 索引与查询顺序。
    for table, index_name, columns in (
        ("user_draft", "idx_user_draft_owner_updated", "user_id, updated_at DESC, id DESC"),
        ("resume_evidence", "idx_resume_evidence_owner_updated", "user_id, updated_at DESC, id DESC"),
        ("application_tracker", "idx_application_tracker_owner_status", "user_id, status, next_action_at, updated_at DESC"),
        ("career_profile", "idx_career_profile_owner", "user_id"),
        ("career_assessment", "idx_career_assessment_owner", "user_id"),
        ("download_file", "idx_download_file_owner", "user_id"),
    ):
        connection.execute(f"CREATE INDEX IF NOT EXISTS {index_name} ON {table} ({columns})")
