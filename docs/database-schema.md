# 数据库版本管理与迁移记录

本文记录 ai-resume 后端从 Phase 1 至今的数据库演进路径：每个版本对应什么业务变更、如何前滚、出问题如何回滚。生产操作清单见 [ALEMBIC_PRODUCTION_CHECKLIST](../resume-backend/migrations/ALEMBIC_PRODUCTION_CHECKLIST.md)。

## 两套机制，各管一段

| 机制 | 适用场景 | 入口 |
| --- | --- | --- |
| 启动期幂等建库（`app/db.py`） | 本地 SQLite 开发、Docker 单机部署；`CREATE TABLE IF NOT EXISTS` + 增量 `ALTER` 幂等迁移 | 应用启动自动执行，零手工步骤 |
| Alembic 版本链（`migrations/versions/`） | PostgreSQL 生产部署；可审计、可重复执行的版本化迁移 | `alembic upgrade head`，连接串读 `DATABASE_URL` 或 `-x database_url=` |

两条链描述的是同一个 schema：Alembic 从 Phase 8 引入，作为 PostgreSQL 生产环境的执行机制；Phase 1-7 的变更沉淀为两个幂等 SQL 脚本（历史存档，不再演进）。`migrations/env.py` 优先级为 `-x database_url=` > `DATABASE_URL` 环境变量 > `alembic.ini` 内默认 SQLite 路径，保证同一份迁移脚本能同时服务本地演练与生产。

## 迁移历史总览

| 版本（revision） | 日期 | 阶段 | 业务变更 | 主要对象变更 | 回滚方式 |
| --- | --- | --- | --- | --- | --- |
| `20260814_jwt_user_isolation.sql` | 2026-08-14 | Phase 7 | JWT 多用户隔离：所有业务表挂到 `users` 账号体系，废除匿名 `client_id` 权限语义 | 新建 `users`；`user_draft`/`resume_evidence`/`application_tracker`/`career_profile`/`career_assessment`/`download_file` 各加 `user_id` 外键与 owner-first 索引 | 备份恢复（历史脚本，仅执行一次，无自动回滚） |
| `20260814_membership_payment.sql` | 2026-08-14 | Phase 7 | 商业化基础：会员等级与订单流水 | 新建 `user_vip`、`order_record`（金额存分，含 CHECK 约束与 owner 索引） | 备份恢复（同上） |
| `20260819_phase8` | 2026-08-19 | Phase 8 | 可移植基线 schema：18 张核心表一次建齐，类型写法按方言分派（PG `IDENTITY` / SQLite `AUTOINCREMENT`），为 PostgreSQL 迁移铺路 | 新建 `users`、`user_draft`、`resume_evidence`、`application_tracker`、`template_table`、`job_cache`、`download_file`、`user_vip`、`order_record`、`job_favorite`、`job_match_subscription`、`job_catalog`、`role_profile`、`major_catalog`、`career_profile`、`career_assessment`、`annual_employment_insight`、`official_dataset_source`、`knowledge_sync_run` + 12 个 owner-first 索引 | `alembic downgrade base`（按依赖逆序 `drop_table`；生产优先走备份恢复） |
| `20260819_phase9` | 2026-08-19 | Phase 9 | 独立 worker 与投递深化：面试提醒、简历版本快照、职业任务清单、后台任务租约锁、岗位匹配告警 | `application_tracker` 加 `contact_info`/`attachment_ref`/`timeline_json`/`next_interview_at`；新建 `interview_reminder`、`resume_version`、`career_task`、`background_task_lock`、`job_match_alert` + 3 个复合索引 | `alembic downgrade 20260819_phase8`（逆序 drop 新表；加列保留，属无害冗余） |
| `20260820_phase10` | 2026-08-20 | Phase 10 | 运营能力：运营角色、推送发送日志、简历导入记录、知识库条目 | `users` 加 `role`（默认 `'user'`，先 `inspect` 探列再补，兼容旧库）；新建 `push_send_log`、`resume_import`、`knowledge_item`、`knowledge_item_version`、`background_task_run` + 索引 | `alembic downgrade 20260819_phase9`（drop 新表；`role` 列保留） |
| `20260821_phase11` | 2026-08-21 | Phase 11 | 账号密码登录：独立凭据表，密码只存 bcrypt 哈希 | 新建 `password_account`（`account` 主键 + `user_id` 唯一外键） | `alembic downgrade 20260820_phase10`（`drop_table`，不影响手机号登录） |
| `20260821_phase12` | 2026-08-21 | Phase 12 | 年度洞察按岗位分级：洞察条目关联目标岗位 | `annual_employment_insight` 加 `role_name`（`server_default ''`，同样先探测再补列） | `alembic downgrade 20260821_phase11`（`batch_alter_table` 删列，SQLite 兼容） |

当前链头：`20260821_phase12`。链上无分叉、无多次合并，`down_revision` 严格线性。

## 回滚策略（三层防线）

1. **首选：备份恢复，不做生产反向迁移。** 任何迁移前用 `sqlite3 <db> ".backup '<path>'"`（或平台快照）做一致性备份并跑 `PRAGMA integrity_check` 留档；出问题直接恢复备份、回退应用版本。数据库回滚不恢复导出文件目录，导出存储需单独备份。
2. **次选：代码内 `downgrade()`。** 全部 5 个 Alembic 版本实现了可执行的反向操作，且遵循"新增表可删、新增列可留"的原则——加列操作（`role`、`role_name`、投递扩展列）在回滚时有意保留，避免生产环境做高破坏性的列删除；需要精确回退列时才用 `batch_alter_table`（Phase 12）。
3. **兜底：迁移脚本全部幂等/带探测。** `CREATE TABLE IF NOT EXISTS`、加列前 `inspect()` 探测列是否存在，意味着同一脚本重复执行不会产生半成品状态，跨环境（有历史数据的旧库 / 全新库）行为一致。

## 生产迁移操作（摘要）

```text
# 前滚
alembic upgrade head                      # 或 alembic upgrade 20260819_phase9 精确到版本
alembic current                           # 确认当前版本
alembic history                           # 审计链条

# 指定库
alembic -x database_url=postgresql+psycopg://user:pass@host/db upgrade head

# 校验
GET /health/detail                        # database.status=connected, storage.status=ready
```

完整的前置条件（维护窗口、备份校验、冒烟步骤）与回滚流程见 [ALEMBIC_PRODUCTION_CHECKLIST](../resume-backend/migrations/ALEMBIC_PRODUCTION_CHECKLIST.md)。

## 当前核心表一览（Phase 12）

- **账号域**：`users`（含 `token_version`、`role`）、`password_account`
- **简历域**：`user_draft`、`resume_version`、`resume_import`、`resume_evidence`
- **求职执行域**：`application_tracker`、`interview_reminder`、`career_task`、`job_favorite`、`job_match_subscription`、`job_match_alert`
- **知识库域**：`job_catalog`、`role_profile`、`major_catalog`、`annual_employment_insight`、`official_dataset_source`、`knowledge_sync_run`、`knowledge_item`、`knowledge_item_version`
- **商业化域**：`user_vip`、`order_record`
- **支撑域**：`template_table`、`job_cache`、`download_file`、`career_profile`、`career_assessment`、`push_send_log`、`background_task_lock`、`background_task_run`

所有业务表以 `user_id` 外键归属账号，查询一律 owner-first（`WHERE user_id = ?` + 对应复合索引），这是 JWT 单体多用户隔离的存储侧保证。
