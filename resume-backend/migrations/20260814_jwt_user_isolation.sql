-- JWT + SQLite 多用户隔离一期升级脚本。
-- 新部署应直接启动新版服务：app.db.initialize_database 会自动执行等价且幂等的迁移。
-- 已有数据库请先备份；本脚本只能执行一次。历史记录 user_id 保持 NULL，绝不自动归属。

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    phone TEXT NOT NULL UNIQUE,
    token_version INTEGER NOT NULL DEFAULT 1 CHECK (token_version >= 1),
    created_at TEXT NOT NULL,
    last_login TEXT NOT NULL
);

ALTER TABLE user_draft ADD COLUMN user_id TEXT REFERENCES users(user_id);
ALTER TABLE resume_evidence ADD COLUMN user_id TEXT REFERENCES users(user_id);
ALTER TABLE application_tracker ADD COLUMN user_id TEXT REFERENCES users(user_id);
ALTER TABLE career_profile ADD COLUMN user_id TEXT REFERENCES users(user_id);
ALTER TABLE career_assessment ADD COLUMN user_id TEXT REFERENCES users(user_id);
ALTER TABLE download_file ADD COLUMN user_id TEXT REFERENCES users(user_id);

CREATE INDEX IF NOT EXISTS idx_user_draft_owner_updated ON user_draft (user_id, updated_at DESC, id DESC);
CREATE INDEX IF NOT EXISTS idx_resume_evidence_owner_updated ON resume_evidence (user_id, updated_at DESC, id DESC);
CREATE INDEX IF NOT EXISTS idx_application_tracker_owner_status ON application_tracker (user_id, status, next_action_at, updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_career_profile_owner ON career_profile (user_id);
CREATE INDEX IF NOT EXISTS idx_career_assessment_owner ON career_assessment (user_id);
CREATE INDEX IF NOT EXISTS idx_download_file_owner ON download_file (user_id);

-- 二期迁移提示：将 TEXT user_id 外键、owner-first 索引和仓储方法原样迁移至 MySQL/PostgreSQL；
-- 不要恢复任何 client_id 作为权限过滤条件。
