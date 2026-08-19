from __future__ import annotations

import json
from pathlib import Path
import sqlite3
import re
from typing import Any

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


_default_timeout_seconds = 3.0
DatabaseTarget = Path | str


def database_kind(target: DatabaseTarget) -> str:
    value = str(target)
    return "postgresql" if value.startswith(("postgresql://", "postgresql+psycopg://")) else "sqlite"


class PostgresConnection:
    """Small compatibility adapter for the repository execute contract."""

    def __init__(self, connection: Any) -> None:
        self._connection = connection

    def __enter__(self) -> "PostgresConnection":
        self._connection.__enter__()
        return self

    def __exit__(self, *arguments: object) -> bool | None:
        return self._connection.__exit__(*arguments)

    def execute(self, statement: str, parameters: Any = ()) -> Any:
        return self._connection.execute(_postgres_statement(statement), parameters)

    def executemany(self, statement: str, parameters: Any) -> Any:
        return self._connection.executemany(_postgres_statement(statement), parameters)


def _postgres_statement(statement: str) -> str:
    normalized = statement.replace("BEGIN IMMEDIATE", "BEGIN").replace("datetime('now')", "CURRENT_TIMESTAMP")
    normalized = normalized.replace("?", "%s")
    if re.match(r"^\s*INSERT\s+OR\s+IGNORE\s+INTO\s+", normalized, flags=re.IGNORECASE):
        normalized = re.sub(r"INSERT\s+OR\s+IGNORE\s+INTO", "INSERT INTO", normalized, count=1, flags=re.IGNORECASE)
        suffix = ";" if normalized.rstrip().endswith(";") else ""
        normalized = normalized.rstrip().rstrip(";") + " ON CONFLICT DO NOTHING" + suffix
    return normalized


def configure_connection_timeout(timeout_seconds: float) -> None:
    global _default_timeout_seconds
    _default_timeout_seconds = max(0.1, timeout_seconds)


def connect(database_path: DatabaseTarget, *, timeout_seconds: float | None = None) -> sqlite3.Connection | PostgresConnection:
    if database_kind(database_path) == "postgresql":
        return _connect_postgres(str(database_path))
    timeout = _default_timeout_seconds if timeout_seconds is None else max(0.1, timeout_seconds)
    connection = sqlite3.connect(_sqlite_path(database_path), timeout=timeout)
    connection.row_factory = sqlite3.Row
    # 本期 SQLite 必须逐连接启用外键；二期数据库迁移由同一仓储 user_id 接口承接。
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute(f"PRAGMA busy_timeout = {int(timeout * 1000)}")
    return connection


def _sqlite_path(target: DatabaseTarget) -> Path | str:
    value = str(target)
    return value.removeprefix("sqlite:///") if value.startswith("sqlite:///") else target


def _connect_postgres(url: str) -> PostgresConnection:
    try:
        from psycopg import connect as psycopg_connect
        from psycopg.rows import dict_row
    except ImportError as error:
        raise RuntimeError("PostgreSQL support requires the psycopg package. Install resume-backend requirements.") from error
    return PostgresConnection(
        psycopg_connect(url.replace("postgresql+psycopg://", "postgresql://", 1), row_factory=dict_row)
    )


def initialize_database(database_path: DatabaseTarget, *, timeout_seconds: float | None = None) -> None:
    if database_kind(database_path) == "postgresql":
        _initialize_postgres(database_path)
        return
    database_path = Path(_sqlite_path(database_path))
    database_path.parent.mkdir(parents=True, exist_ok=True)
    if timeout_seconds is not None:
        configure_connection_timeout(timeout_seconds)
    with connect(database_path) as connection:
        connection.execute("PRAGMA journal_mode = WAL")
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                phone TEXT NOT NULL UNIQUE,
                token_version INTEGER NOT NULL DEFAULT 1 CHECK (token_version >= 1),
                created_at TEXT NOT NULL,
                last_login TEXT NOT NULL,
                is_deleted INTEGER NOT NULL DEFAULT 0 CHECK (is_deleted IN (0, 1)),
                deleted_at TEXT,
                privacy_consent_at TEXT
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
            -- 二期商业化底座：每个用户一行当前权益，所有过期降级在仓储层完成。
            CREATE TABLE IF NOT EXISTS user_vip (
                user_id TEXT PRIMARY KEY REFERENCES users(user_id),
                vip_level TEXT NOT NULL DEFAULT 'free' CHECK (vip_level IN ('free', 'basic', 'premium')),
                expire_time TEXT,
                auto_renew INTEGER NOT NULL DEFAULT 0,
                create_time TEXT NOT NULL
            );
            -- total_amount 为人民币分，避免 SQLite REAL 的金额精度问题。
            CREATE TABLE IF NOT EXISTS order_record (
                order_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL REFERENCES users(user_id),
                package_type TEXT NOT NULL CHECK (package_type IN ('monthly', 'quarterly', 'annual')),
                total_amount INTEGER NOT NULL CHECK (total_amount >= 0),
                payment_status TEXT NOT NULL CHECK (payment_status IN ('pending', 'paid', 'closed', 'expired')),
                create_time TEXT NOT NULL,
                payment_channel TEXT,
                provider_transaction_id TEXT,
                entitlement_expire_time TEXT,
                auto_renew INTEGER NOT NULL DEFAULT 0
            );
            CREATE INDEX IF NOT EXISTS idx_order_record_owner_created
            ON order_record (user_id, create_time DESC, order_id DESC);
            CREATE TABLE IF NOT EXISTS job_favorite (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL REFERENCES users(user_id),
                role_name TEXT NOT NULL,
                note TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                UNIQUE (user_id, role_name)
            );
            CREATE INDEX IF NOT EXISTS idx_job_favorite_owner_created
            ON job_favorite (user_id, created_at DESC, id DESC);
            CREATE TABLE IF NOT EXISTS job_match_subscription (
                user_id TEXT PRIMARY KEY REFERENCES users(user_id),
                enabled INTEGER NOT NULL DEFAULT 0 CHECK (enabled IN (0, 1)),
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS job_favorite (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL REFERENCES users(user_id),
                role_name TEXT NOT NULL,
                note TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                UNIQUE (user_id, role_name)
            );
            CREATE INDEX IF NOT EXISTS idx_job_favorite_owner_created
            ON job_favorite (user_id, created_at DESC, id DESC);
            CREATE TABLE IF NOT EXISTS job_match_subscription (
                user_id TEXT PRIMARY KEY REFERENCES users(user_id),
                enabled INTEGER NOT NULL DEFAULT 0 CHECK (enabled IN (0, 1)),
                updated_at TEXT NOT NULL
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
        _migrate_phase7_lifecycle(connection)
        _seed_initial_data(connection)
        _migrate_legacy_job_cache(connection)


def _initialize_postgres(database_url: DatabaseTarget) -> None:
    try:
        with connect(database_url) as connection:
            connection.execute("SELECT 1 FROM template_table LIMIT 1")
            _seed_initial_data(connection)
    except Exception as error:
        raise RuntimeError(
            "PostgreSQL schema is unavailable. Run 'alembic upgrade head' before starting the backend."
        ) from error


def _seed_initial_data(connection: Any) -> None:
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
            (role.role_name, role.family, json.dumps(role.aliases, ensure_ascii=False), 1_000 + index)
            for index, role in enumerate(ROLE_SEEDS)
        ],
    )


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


def _migrate_phase7_lifecycle(connection: sqlite3.Connection) -> None:
    _ensure_column(connection, "users", "is_deleted", "INTEGER NOT NULL DEFAULT 0")
    _ensure_column(connection, "users", "deleted_at", "TEXT")
    _ensure_column(connection, "users", "privacy_consent_at", "TEXT")
    _ensure_column(connection, "job_match_subscription", "match_filter", "TEXT NOT NULL DEFAULT ''")
    _ensure_column(connection, "job_match_subscription", "last_notify_at", "TEXT")
    _ensure_column(connection, "order_record", "provider_transaction_id", "TEXT")
    _migrate_order_statuses(connection)


def _ensure_column(connection: sqlite3.Connection, table: str, column: str, definition: str) -> None:
    columns = {str(row["name"]) for row in connection.execute(f"PRAGMA table_info({table})")}
    if column not in columns:
        connection.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def _migrate_order_statuses(connection: sqlite3.Connection) -> None:
    row = connection.execute(
        "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'order_record'"
    ).fetchone()
    if row is None or "'expired'" in str(row["sql"]):
        return
    connection.executescript(
        """
        ALTER TABLE order_record RENAME TO order_record_legacy;
        CREATE TABLE order_record (
            order_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL REFERENCES users(user_id),
            package_type TEXT NOT NULL CHECK (package_type IN ('monthly', 'quarterly', 'annual')),
            total_amount INTEGER NOT NULL CHECK (total_amount >= 0),
            payment_status TEXT NOT NULL CHECK (payment_status IN ('pending', 'paid', 'closed', 'expired')),
            create_time TEXT NOT NULL,
            payment_channel TEXT,
            provider_transaction_id TEXT,
            entitlement_expire_time TEXT,
            auto_renew INTEGER NOT NULL DEFAULT 0
        );
        INSERT INTO order_record (
            order_id, user_id, package_type, total_amount, payment_status, create_time,
            payment_channel, entitlement_expire_time, auto_renew
        ) SELECT
            order_id, user_id, package_type, total_amount, payment_status, create_time,
            payment_channel, entitlement_expire_time, auto_renew
        FROM order_record_legacy;
        DROP TABLE order_record_legacy;
        CREATE INDEX IF NOT EXISTS idx_order_record_owner_created
        ON order_record (user_id, create_time DESC, order_id DESC);
        """
    )
