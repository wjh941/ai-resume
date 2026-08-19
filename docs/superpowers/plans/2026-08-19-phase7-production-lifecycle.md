# Phase 7 Production Lifecycle Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add production-safe auth branching and complete the privacy, order,
and job-subscription lifecycle while preserving Phase 6 routes and SQLite data.

**Architecture:** New services own one-time SMS codes and privacy archives.
Existing repositories receive additive fields and lifecycle methods. The client
uses the existing request/session layer and only adds controls for new API
fields.

**Tech Stack:** FastAPI, SQLite, Python standard-library ZIP/HMAC/HTTP,
Vue 3/uni-app, Vitest, pytest.

## Global Constraints

- Preserve existing APIs, tables, and mock development workflows.
- Do not connect real payment collection, WeChat OAuth deployment, job-source
  sync, or scheduled notification workers.
- Keep SQLite; defer server database migration and deployment operations.
- Add a failing test before each behaviour change.

---

### Task 1: SMS Authentication Branches

**Files:** `app/config.py`, `app/services/sms.py`, `app/services/auth.py`,
`app/api/auth.py`, `tests/test_phase7_auth.py`.

- [ ] Add failing tests for the production gateway path, invalid code, and
  development `123456` login.
- [ ] Add a small SMS service that issues single-use, hashed, expiring codes
  and delegates production delivery to the configured HTTPS endpoint.
- [ ] Wire the existing auth routes through the service without changing route
  paths or JWT payloads.
- [ ] Run the focused auth tests and commit the verified backend change.

### Task 2: Privacy Lifecycle

**Files:** `app/db.py`, `app/repositories/users.py`,
`app/repositories/account_privacy.py`, `app/api/account.py`,
`tests/test_phase7_privacy.py`.

- [ ] Add failing tests for ZIP export, token invalidation, soft deletion, and
  anonymized user-owned records.
- [ ] Add idempotent SQLite columns and repository methods for export,
  explicit consent, and soft deletion.
- [ ] Keep the existing POST data-export response shape and add a protected ZIP
  download route.
- [ ] Run the focused privacy tests and commit the verified backend change.

### Task 3: Order and Subscription Lifecycle

**Files:** `app/db.py`, `app/repositories/membership.py`,
`app/services/membership.py`, `app/api/membership.py`,
`app/repositories/job_collections.py`, `app/schemas/job_collections.py`,
`app/api/job_collections.py`, `tests/test_phase7_membership_jobs.py`.

- [ ] Add failing tests for idempotent signed callbacks, expired pending orders,
  and subscription filter persistence.
- [ ] Add additive order status/verification logic and subscription fields.
- [ ] Preserve the demo callback and existing favourite CRUD endpoints.
- [ ] Run focused lifecycle tests and commit the verified backend change.

### Task 4: Client and Deployment Documentation

**Files:** login, account, membership, job-collection pages and services,
`.env.example`, `docs/DEPLOYMENT_PRECHECK.md`, `docs/phase7-changelog.md`,
frontend unit tests.

- [ ] Add failing adapter tests for additive response fields and login OAuth
  placeholder request handling.
- [ ] Add the WeChat placeholder button, privacy policy/export controls,
  membership expiry and orders, plus subscription filter input.
- [ ] Document production prerequisites and explicitly deferred integrations.
- [ ] Run frontend unit tests, H5 build, and the full backend suite.

### Task 5: Verification and Delivery

- [ ] Smoke test development mock login, production SMS configuration failure,
  ZIP export/deletion, and membership order state transitions.
- [ ] Run `git diff --check`, commit atomic changes, and push the branch.
