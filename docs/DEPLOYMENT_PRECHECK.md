# Deployment Pre-check

Complete every item before setting `PRODUCTION=true`. SQLite remains for
development only; production needs PostgreSQL, backup validation, a worker
deployment decision, and an external HTTPS reverse proxy.

## Public VPS Safety Baseline

- Public deployment must set `PRODUCTION=true`. This disables FastAPI debug
  tracebacks and OpenAPI documentation endpoints; do not expose development
  configuration, `/docs`, or a wildcard CORS policy on the public internet.
- The supplied Compose file uses `unless-stopped` restart policies and health
  checks for the API and worker. It starts the worker only after the API health
  endpoint is ready. Monitor restart loops; automatic restart is not a
  substitute for fixing a failed migration or missing secret.
- Compose explicitly sets `AUTH_DEMO_MODE=false`, `SMS_PROVIDER=disabled`,
  `PAYMENT_DEMO_MODE=false`, `PUSH_DISPATCHER_MODE=mock`, and
  `WEB_SEARCH_PROVIDER=disabled`. It does not connect SMS, payment, push, or
  job-search third parties.
- For a personal deployment without an SMS provider, use the 账号密码 tab to
  register a local account. Passwords are stored only as bcrypt hashes; set a
  strong `JWT_SECRET` and retain `PASSWORD_BCRYPT_ROUNDS=12` or higher after
  measuring the server capacity.

## External Service Qualifications

No external service is enabled by this release. Before changing the mock or
disabled settings, obtain and verify the platform requirements for the exact
legal entity, region, and account type. This checklist is operational guidance,
not legal advice.

| 功能 | 上线前的资质与配置确认 |
| --- | --- |
| 商业短信 | 短信供应商通常会校验主体、签名和模板。以阿里云为例，资质申请和中国大陆短信签名有对应的主体材料要求；先完成[阿里云短信资质申请](https://help.aliyun.com/zh/sms/user-guide/qualification-application-description)，再配置密钥。 |
| 微信支付 | 微信支付商户入驻需要按主体类型提交材料；官方指引列出了营业执照、经营者或法人证件等常见材料。完成[微信支付商户入驻](https://pay.weixin.qq.com/static/help_guide/business_registration.shtml)及回调验签后，才可接入真实支付。 |
| 微信订阅消息 | 订阅消息需要已获用户授权、可用模板 ID 和符合平台规则的小程序主体能力。按[微信订阅消息文档](https://developers.weixin.qq.com/miniprogram/dev/framework/open-ability/subscribe-message.html)完成账号资质、模板和用户授权核验后，才可启用发送。 |

## Phase 8 Database and Backups

- Keep `DATABASE_URL` empty for local SQLite development. Production PostgreSQL
  uses `postgresql+psycopg://...`; run `alembic upgrade head` before FastAPI.
- Back up before every migration and periodically afterward. Use
  `scripts/backup-database.ps1` on Windows or `scripts/backup-database.sh` on
  Linux, set `BACKUP_DIR` and `BACKUP_RETENTION_DAYS`, then prove a restore.
- Follow [PostgreSQL migration](POSTGRESQL_MIGRATION.md) to move an existing
  SQLite database. Temporary `download_file` records are intentionally not
  copied because their referenced files are machine-local and expire.
- Set exact HTTPS origins in `CORS_ORIGINS`; production requests from an
  unlisted browser origin are rejected. Never use a wildcard with credentials.
- Keep SMS, WeChat, payment, JWT, and database secrets outside source control.
  Do not put them in frontend build variables or Docker image layers.
- Compose serves HTTP only. Place Nginx or Caddy in front of it for HTTPS,
  redirect HTTP to HTTPS, and configure forwarded headers at that proxy.

## Phase 9 Worker Service

- Run `alembic upgrade head` once before starting application containers. The
  Compose backend also runs the migration command at startup for convenience,
  but release automation should make this an explicit, verified deployment
  step.
- The `worker` Compose service runs `python worker.py` separately from FastAPI.
  It scans job subscriptions, cleans expired export files, and closes overdue
  unpaid orders. It does not bind an HTTP port.
- Set `WORKER_ENABLED=true` for the worker process and configure
  `TASK_SCAN_INTERVAL_SECONDS` and `WORKER_LOCK_TTL_SECONDS` to exceed the
  expected task duration. Run a single worker instance by default.
- The database task lease reduces duplicate execution across instances, but it
  is not a replacement for operational ownership, synchronized clocks, or
  observing worker logs. Verify one manual worker cycle after deployment.
- Subscription alerts are stored as in-app pending records only. SMS, WeChat,
  and other push delivery remain intentionally unimplemented.

## Phase 10 Final Launch Checklist

- Keep the established port contract: H5 development runs on
  `127.0.0.1:5186`; FastAPI runs on `127.0.0.1:8000`. Production H5 assets
  must call the HTTPS API domain through the reverse proxy, not a browser-side
  loopback address.
- Set `OPERATOR_PHONE_ALLOWLIST` to a minimal, reviewed comma-separated list.
  A listed phone receives the persistent `operator` role at login; operator
  APIs are protected by the backend JWT role check, not just by hidden H5
  navigation.
- Leave `PUSH_DISPATCHER_MODE=mock` until a provider integration has passed
  security review. `real` currently records dispatch intent and failures only:
  it does not make a WeChat subscription-message or SMS HTTP request.
- Store all SMS, WeChat Open Platform, payment, push, PostgreSQL, and JWT
  secrets in the deployment secret manager. Rotate leaked secrets immediately;
  do not place them in `.env` files committed to the repository or H5 build
  variables.
- Confirm the external HTTPS reverse proxy, WeChat domain whitelist, SMS sign
  name/template, payment callback verification, and push provider account are
  ready before enabling their respective production integrations.
- Set a writable, private `TEMP_FILE_PATH`, a suitable
  `RESUME_IMPORT_MAX_FILE_BYTES`, and retention rules. Resume upload accepts
  only PDF/Word by extension and MIME type. Malware scanning and real document
  parsing are still integration points, not enabled protection.
- Verify `/health` after release for the database kind, worker status, and
  push dispatcher mode. The endpoint masks secrets and is a hint, not a full
  monitoring system.
- Run migrations, restore-test a backup, and execute one worker cycle before
  accepting traffic. Keep one active worker unless the shared task lease and
  clocks have been operationally validated for multiple instances.

## Troubleshooting

- **Token rejected:** confirm the same `JWT_SECRET` is present on every
  backend instance and that a soft-deleted account has not invalidated it.
- **SMS failed:** verify the provider HTTPS endpoint, access credentials, sign
  name, and template ID; development mode alone accepts code `123456`.
- **Database lock:** SQLite supports local development only. Check the single
  process, `SQLITE_TIMEOUT_SECONDS`, and move concurrent production traffic to
  PostgreSQL.
- **Export permission failure:** ensure `TEMP_FILE_PATH` exists, is writable by
  the backend account, and is not a shared user-media directory.
- **Operator page unavailable:** log out and back in after adding the phone to
  `OPERATOR_PHONE_ALLOWLIST`; existing tokens retain the role captured at
  login and the backend will reject a stale role claim.
- **Resume import rejected:** use a PDF, `.doc`, or `.docx` file within
  `RESUME_IMPORT_MAX_FILE_BYTES`; retry after checking the backend account can
  create the private temporary directory.
- **Push log is skipped:** this is expected with the default mock mode. Real
  provider calls are deliberately not implemented in this release.

## Authentication

- Set a unique 32+ character `JWT_SECRET` outside source control.
- Set `AUTH_DEMO_MODE=false`; the development code `123456` must never be
  accepted in production.
- Configure `SMS_PROVIDER=http`, `SMS_HTTP_ENDPOINT`, `SMS_ACCESS_KEY`,
  `SMS_ACCESS_SECRET`, `SMS_SIGN_NAME`, and `SMS_TEMPLATE_ID`.
- Verify the provider endpoint accepts the documented JSON request contract and
  returns an HTTP success only after accepting a message for delivery.
- Set practical `AUTH_RATE_LIMIT_*` and `SMS_CODE_*` values for the expected
  traffic. In-memory limits are process-local; use shared storage before a
  multi-instance deployment.

## WeChat Open Platform

- Register an HTTPS redirect domain in WeChat Open Platform before using the
  callback placeholder.
- Configure `WECHAT_OPEN_APP_ID`, `WECHAT_OPEN_APP_SECRET`, and
  `WECHAT_OPEN_REDIRECT_URI` as deployment secrets.
- The callback route intentionally does not exchange authorization codes yet.
  Implement and test provider-specific code exchange, state validation, and
  redirect handling before enabling WeChat login.

## Payments

- Configure merchant/provider secrets outside source control.
- Set `PAYMENT_CALLBACK_SECRET` only for the current HMAC callback skeleton.
- Verify the provider's signed callback specification before replacing the
  placeholder. No payment request initiation or real provider integration is
  enabled in this release.
- Confirm `ORDER_PAYMENT_EXPIRE_MINUTES` with the billing policy.

## Privacy

- Publish the privacy policy referenced in the Account page before release.
- Validate ZIP exports and soft deletion against the retention policy with
  legal/privacy review. Deletion anonymizes resume and career records while
  retaining membership orders for audit.
- Move temporary exports and account data to managed storage before production
  scale; this phase serves the archive directly from memory.
