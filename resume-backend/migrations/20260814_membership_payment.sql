-- 二期商业化基础迁移（SQLite 过渡版）。可在已有数据库安全重复执行。
-- 二期迁移 MySQL/PostgreSQL 时保留 user_id 外键和 owner-first 查询约束。
CREATE TABLE IF NOT EXISTS user_vip (
    user_id TEXT PRIMARY KEY REFERENCES users(user_id),
    vip_level TEXT NOT NULL DEFAULT 'free' CHECK (vip_level IN ('free', 'basic', 'premium')),
    expire_time TEXT,
    auto_renew INTEGER NOT NULL DEFAULT 0,
    create_time TEXT NOT NULL
);

-- total_amount 保存人民币分；payment_channel 预留 demo/wechat_pay/alipay。
CREATE TABLE IF NOT EXISTS order_record (
    order_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(user_id),
    package_type TEXT NOT NULL CHECK (package_type IN ('monthly', 'quarterly', 'annual')),
    total_amount INTEGER NOT NULL CHECK (total_amount >= 0),
    payment_status TEXT NOT NULL CHECK (payment_status IN ('pending', 'paid', 'closed')),
    create_time TEXT NOT NULL,
    payment_channel TEXT,
    entitlement_expire_time TEXT,
    auto_renew INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_order_record_owner_created
ON order_record (user_id, create_time DESC, order_id DESC);
