# Phase 8 Production Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add portable database migration support and production hardening without changing API contracts or the H5 `5186` to FastAPI `8000` topology.

**Architecture:** Repositories retain their `connect(...).execute(...)` boundary. `DATABASE_URL` selects a PostgreSQL adapter while SQLite remains the default. Alembic supplies a portable baseline schema; production security and export checks remain at application boundaries.

**Tech Stack:** FastAPI, sqlite3, psycopg 3, SQLAlchemy/Alembic, Vue 3/uni-app, PowerShell, POSIX shell, Docker Compose.

## Global Constraints

- Preserve API payloads, data, and repository method contracts.
- Keep SQLite as default without `DATABASE_URL`; select PostgreSQL through `DATABASE_URL` only.
- Preserve H5 `127.0.0.1:5186` proxying to FastAPI `127.0.0.1:8000`.
- Compose handles HTTP only; external Nginx or Caddy terminates HTTPS.
- Leave notification workers, calendar reminders, resume versions, administration, and collaboration out of scope.

---

### Task 1: Database target and Alembic baseline

**Files:**
- Modify: `resume-backend/app/config.py`, `resume-backend/app/db.py`, `resume-backend/main.py`, `resume-backend/requirements.txt`
- Create: `resume-backend/alembic.ini`, `resume-backend/migrations/env.py`, `resume-backend/migrations/versions/20260819_phase8_portable_schema.py`
- Test: `resume-backend/tests/test_phase8_database.py`

**Interfaces:** Consumes `DATABASE_PATH`, optional `DATABASE_URL`, and current `connect(target)` callers. Produces `Settings.database_target`, `Settings.database_kind`, `database_kind(target)`, portable connections, and `alembic upgrade head` support.

- [ ] **Step 1: Write the failing tests**

```python
def test_database_url_selects_postgresql_target(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://user:secret@db/resume")
    settings = load_settings()
    assert settings.database_kind == "postgresql"
    assert settings.database_target == "postgresql+psycopg://user:secret@db/resume"

def test_alembic_upgrades_a_fresh_sqlite_database(tmp_path):
    run_alembic_upgrade(f"sqlite:///{tmp_path / 'phase8.db'}")
    assert table_exists(tmp_path / "phase8.db", "users")
```

- [ ] **Step 2: Run the focused test**

Run: `python -m pytest tests/test_phase8_database.py -q`

Expected: FAIL because target selection and Alembic configuration are absent.

- [ ] **Step 3: Implement the smallest compatibility boundary**

```python
@property
def database_target(self) -> Path | str:
    return self.database_url or self.database_path

def database_kind(target: Path | str) -> str:
    return "postgresql" if str(target).startswith(("postgresql://", "postgresql+psycopg://")) else "sqlite"
```

Keep the existing SQLite initializer. For PostgreSQL use mapping rows, parameter
translation, and only the three already-used SQLite query idioms: `BEGIN
IMMEDIATE`, `INSERT OR IGNORE`, and `datetime('now')`. Create a
dialect-neutral Alembic revision for all tables, indexes, constraints, and
Phase 7 fields. Support offline PostgreSQL SQL generation without a running
database.

- [ ] **Step 4: Re-run the focused test**

Run: `python -m pytest tests/test_phase8_database.py -q`

Expected: PASS for SQLite migration and PostgreSQL offline SQL generation.

- [ ] **Step 5: Commit the slice**

Run: `git add resume-backend && git commit -m "feat: add portable database migration support"`

### Task 2: Production boundaries and export storage

**Files:**
- Modify: `resume-backend/app/config.py`, `resume-backend/main.py`, `resume-backend/app/api/system.py`, `resume-backend/app/services/downloads.py`, `resume-backend/app/api/exports.py`
- Test: `resume-backend/tests/test_phase8_hardening.py`

**Interfaces:** Consumes production settings, CORS origins, export directory, and `DownloadService`. Produces security headers, strict production origins, docs restriction, storage ownership checks, TTL cleanup, and additive health fields.

- [ ] **Step 1: Write the failing tests**

```python
def test_production_hides_docs_rejects_unknown_origin_and_sets_headers(production_client):
    assert production_client.get("/docs").status_code == 404
    assert production_client.get("/health", headers={"Origin": "https://unknown.example"}).status_code == 403
    assert production_client.get("/health").headers["x-content-type-options"] == "nosniff"

def test_download_registration_rejects_path_outside_temp_directory(tmp_path):
    service = DownloadService(tmp_path / "db", tmp_path / "exports", 60)
    with pytest.raises(ExportPathError):
        service.register("user", tmp_path / "outside.pdf", "resume.pdf")
```

- [ ] **Step 2: Run the focused test**

Run: `python -m pytest tests/test_phase8_hardening.py -q`

Expected: FAIL because production restrictions and output-path ownership are absent.

- [ ] **Step 3: Implement boundary-only hardening**

```python
if settings.production and origin and origin not in settings.cors_origins:
    return JSONResponse(status_code=403, content=error("origin_forbidden", "Origin is not allowed."))

output_path.relative_to(self._temp_directory)
```

Disable docs/OpenAPI in production, add conservative response headers, expose
only configuration booleans in health responses, reject output registration
outside `TEMP_FILE_PATH`, and remove expired records plus orphaned owned files.
Keep tokens, routes, and response envelopes unchanged.

- [ ] **Step 4: Re-run the focused test**

Run: `python -m pytest tests/test_phase8_hardening.py -q`

Expected: PASS and existing CORS/export tests remain green.

- [ ] **Step 5: Commit the slice**

Run: `git add resume-backend && git commit -m "feat: harden production runtime and exports"`

### Task 3: Backups, migration utility, and deployment assets

**Files:**
- Create: `scripts/backup-database.ps1`, `scripts/backup-database.sh`, `scripts/migrate_sqlite_to_postgres.py`, `docker-compose.yml`
- Create: `resume-backend/Dockerfile`, `resume-miniprogram/Dockerfile`, `resume-miniprogram/nginx.conf`
- Modify: `resume-backend/.env.example`, `docs/DEPLOYMENT_PRECHECK.md`
- Create: `docs/POSTGRESQL_MIGRATION.md`
- Test: `resume-backend/tests/test_phase8_operations.py`

**Interfaces:** Consumes `DATABASE_PATH`, `DATABASE_URL`, `BACKUP_DIR`, and `BACKUP_RETENTION_DAYS`. Produces compressed timestamped backups, dependency-ordered SQLite-to-PostgreSQL copying, and an HTTP-only compose stack.

- [ ] **Step 1: Write the failing operational tests**

```python
def test_backup_script_creates_compressed_sqlite_backup(tmp_path):
    result = run_backup_script(database_path=tmp_path / "resume.db", backup_dir=tmp_path / "backups")
    assert result.suffix == ".zip"
    assert result.is_file()

def test_compose_keeps_backend_internal_and_frontend_http_only():
    compose = read_compose_file()
    assert compose["services"]["frontend"]["ports"] == ["80:80"]
    assert compose["services"]["backend"]["expose"] == ["8000"]
```

- [ ] **Step 2: Run the focused test**

Run: `python -m pytest tests/test_phase8_operations.py -q`

Expected: FAIL because operational assets do not exist.

- [ ] **Step 3: Implement assets and deployment guidance**

```powershell
$retentionDays = [int]($env:BACKUP_RETENTION_DAYS ?? 14)
```

Backup scripts create a SQLite archive or PostgreSQL custom dump and delete
only aged backup artifacts. Include a scheduled-task registration comment. The
copy utility checks paths, copies foreign-key order, converts boolean fields,
and resets sequences. Compose runs PostgreSQL, internal FastAPI `8000`, and
frontend HTTP `80`; the documentation covers migration, backup/restore,
database differences, strict CORS, secret safety, external TLS, and production
troubleshooting.

- [ ] **Step 4: Re-run and manually exercise SQLite backup**

Run: `python -m pytest tests/test_phase8_operations.py -q`

Expected: PASS; PowerShell creates a compressed backup from a temporary database.

- [ ] **Step 5: Commit the slice**

Run: `git add scripts docker-compose.yml resume-backend resume-miniprogram docs && git commit -m "ops: add Phase8 backup and deployment assets"`

### Task 4: Frontend guidance and complete validation

**Files:**
- Modify: `resume-miniprogram/src/services/http.ts`, `resume-miniprogram/src/pages/login/index.vue`, `resume-miniprogram/src/pages/membership/index.vue`, `resume-miniprogram/src/pages/account/index.vue`
- Test: `resume-miniprogram/src/tests/http.spec.ts`, `resume-miniprogram/src/tests/phase8-config-errors.spec.ts`
- Create: `docs/phase8-changelog.md`

**Interfaces:** Consumes sanitized server error text. Produces friendly missing SMS, WeChat OAuth, payment, and export-storage guidance without exposing server details.

- [ ] **Step 1: Write the failing frontend test**

```ts
it("explains missing SMS configuration without exposing server detail", () => {
  expect(toUserMessage(new Error("SMS delivery is not configured or temporarily unavailable.")))
    .toContain("SMS")
})
```

- [ ] **Step 2: Run the focused frontend test**

Run: `npm.cmd run test:unit -- src/tests/phase8-config-errors.spec.ts`

Expected: FAIL because known configuration failures remain generic.

- [ ] **Step 3: Add narrow error mapping and changelog**

```ts
const CONFIGURATION_HINTS: Array<[RegExp, string]> = [
  [/sms delivery is not configured/i, "SMS sign-in is not configured for this environment."],
  [/wechat.*not configured|https whitelisted redirect/i, "WeChat sign-in needs an approved HTTPS callback domain."],
  [/payment channel.*not configured/i, "Payment is not configured for this environment."],
]
```

Use existing inline page errors and preserve layout, routes, and request logic.

- [ ] **Step 4: Run complete validation**

Run: `python -m pytest tests -q` in `resume-backend`, then `npm.cmd run test:unit` and `npm.cmd run build:h5` in `resume-miniprogram`.

Expected: complete test suites pass and the H5 production build completes.

- [ ] **Step 5: Commit and push the final slice**

Run: `git add resume-miniprogram docs && git commit -m "feat: improve production configuration guidance" && git push origin feature/ai-resume-demo`
