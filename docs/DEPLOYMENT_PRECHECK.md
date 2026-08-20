# Deployment Pre-check

Complete every item before setting `PRODUCTION=true`. SQLite remains for
development only; production needs PostgreSQL, backup validation, a worker
deployment decision, and an external HTTPS reverse proxy.

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
