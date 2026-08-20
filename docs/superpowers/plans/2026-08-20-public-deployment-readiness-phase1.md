# Public Deployment Readiness Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add bcrypt-backed account-password authentication and public-VPS deployment guardrails without changing existing APIs or enabling real third-party services.

**Architecture:** A dedicated `password_account` table maps a normalized account name to an existing user ID and bcrypt hash. New additive auth endpoints reuse the current JWT issuer; Compose and docs make mock-only public defaults explicit.

**Tech Stack:** FastAPI, Pydantic, bcrypt, Alembic, SQLite/PostgreSQL, Vue 3 Uni-App, Docker Compose, pytest, Vitest.

## Global Constraints

- Existing phone-SMS auth, JWT payloads, API routes, and tables remain compatible.
- SMS, payment, job APIs, and push stay disabled or mock-only.
- New visible UI copy is Simplified Chinese; source comments remain English.
- Password values are neither stored in plaintext nor written to logs.

---

### Task 1: Password Account Persistence

**Files:** Modify `resume-backend/requirements.txt`, `resume-backend/app/config.py`, `resume-backend/app/db.py`, `resume-backend/app/repositories/users.py`, and `resume-backend/app/services/auth.py`. Create `resume-backend/app/repositories/password_accounts.py` and `resume-backend/tests/test_password_auth.py`.

**Interfaces:** Produce `PasswordAccountRepository`, `AuthService.register_password_account(account, password)`, and `AuthService.login_password_account(account, password)`.

- [ ] **Step 1: Write the failing backend test**

```python
def test_password_register_then_login_issues_existing_jwt(api_client):
    created = api_client.post("/api/auth/register-password", json={"account": "owner", "password": "a-strong-password"})
    logged_in = api_client.post("/api/auth/login-password", json={"account": "OWNER", "password": "a-strong-password"})
    assert created.status_code == logged_in.status_code == 200
```

- [ ] **Step 2: Run red test**

`python -m pytest tests/test_password_auth.py -q`

- [ ] **Step 3: Implement minimum secure persistence**

```python
password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=settings.password_bcrypt_rounds)).decode("utf-8")
valid = bcrypt.checkpw(password.encode("utf-8"), record.password_hash.encode("utf-8"))
```

Create `local:{uuid}` internal phones for local users and normalize account names before each repository query.

- [ ] **Step 4: Run green test**

`python -m pytest tests/test_password_auth.py -q`

- [ ] **Step 5: Commit**

`git add resume-backend && git commit -m "feat(auth): add bcrypt password accounts"`

### Task 2: Additive APIs and Migration

**Files:** Modify `resume-backend/app/api/auth.py`, `resume-backend/app/schemas/auth.py`, and `resume-backend/tests/test_phase8_database.py`. Create `resume-backend/migrations/versions/20260821_phase11_password_accounts.py`.

**Interfaces:** Produce `POST /api/auth/register-password` and `POST /api/auth/login-password`, preserving the existing JWT response fields.

- [ ] **Step 1: Add failing API and migration tests**

```python
def test_password_account_migration_renders_postgresql_sql():
    command.upgrade(config, "head", sql=True)
    assert "CREATE TABLE IF NOT EXISTS password_account" in output.getvalue()
```

- [ ] **Step 2: Run red test**

`python -m pytest tests/test_password_auth.py tests/test_phase8_database.py -q`

- [ ] **Step 3: Add validation, routes, and revision**

Use a 3-32 character ASCII account pattern, a 10-72 byte password limit, HTTP 409 for duplicates, and a generic HTTP 401 for invalid credentials. The migration uses portable table DDL.

- [ ] **Step 4: Run migration checks**

`python -m pytest tests/test_password_auth.py tests/test_phase8_database.py tests/test_phase10_rbac.py -q`

- [ ] **Step 5: Commit**

`git add resume-backend && git commit -m "feat(auth): expose password login fallback"`

### Task 3: H5 Login Tabs

**Files:** Modify `resume-miniprogram/src/types/auth.ts`, `resume-miniprogram/src/stores/session.ts`, `resume-miniprogram/src/services/auth-api.ts`, `resume-miniprogram/src/pages/login/index.vue`, and `resume-miniprogram/src/pages/account/index.vue`. Create `resume-miniprogram/src/tests/password-auth.spec.ts`.

**Interfaces:** Produce `registerPasswordAccount(account, password)` and `loginPasswordAccount(account, password)` with the current session response shape.

- [ ] **Step 1: Write failing client request test**

```ts
it("sends credentials to password login", async () => {
  await loginPasswordAccount("owner", "a-strong-password")
  expect(requestOptions?.url).toContain("/api/auth/login-password")
})
```

- [ ] **Step 2: Run red test**

`npm.cmd run test:unit -- --run src/tests/password-auth.spec.ts`

- [ ] **Step 3: Implement compact Chinese UI**

Use fixed-size segmented tabs, local validation, inline errors, the current session storage, and the existing unavailable WeChat action. The account page displays account metadata when present.

- [ ] **Step 4: Run green test and H5 build**

`npm.cmd run test:unit -- --run src/tests/password-auth.spec.ts`

`npm.cmd run build:h5`

- [ ] **Step 5: Commit**

`git add resume-miniprogram/src && git commit -m "feat(h5): add account password login"`

### Task 4: Compose and Deployment Docs

**Files:** Modify `docker-compose.yml`, `resume-backend/.env.example`, and `docs/DEPLOYMENT_PRECHECK.md`. Create `resume-backend/tests/test_public_deployment_config.py`.

**Interfaces:** Produce backend/worker healthchecks, `unless-stopped` restart policies, and forced disabled/mock third-party public defaults.

- [ ] **Step 1: Write failing deployment test**

```python
def test_compose_keeps_public_third_party_services_mock_only():
    compose = Path("../docker-compose.yml").read_text(encoding="utf-8")
    assert "restart: unless-stopped" in compose
    assert 'AUTH_DEMO_MODE: "false"' in compose
```

- [ ] **Step 2: Run red test**

`python -m pytest tests/test_public_deployment_config.py -q`

- [ ] **Step 3: Add health and documentation controls**

Add backend `/health` and worker-PID healthchecks, restart policies, worker startup after a healthy backend, production safety guidance, password fallback guidance, and official-platform qualification checks for commercial SMS, WeChat Pay, and subscription messages.

- [ ] **Step 4: Run green test**

`python -m pytest tests/test_public_deployment_config.py -q`

- [ ] **Step 5: Commit**

`git add docker-compose.yml resume-backend/.env.example docs/DEPLOYMENT_PRECHECK.md resume-backend/tests/test_public_deployment_config.py && git commit -m "docs: harden public deployment defaults"`

### Task 5: Full Verification

- [ ] Run `python -m pytest tests -q` in `resume-backend`.
- [ ] Run `npm.cmd run test:unit` in `resume-miniprogram`.
- [ ] Run `npm.cmd run build:h5` in `resume-miniprogram`.
- [ ] Run `alembic heads` and `git diff --check`.
