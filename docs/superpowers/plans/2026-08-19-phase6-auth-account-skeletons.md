# Phase6 Auth and Account Skeletons Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Connect JWT login to protected mini-program requests and add non-destructive account, collection, subscription, membership, and order skeletons.

**Architecture:** Session persistence is a frontend-only adapter used by `http.ts`; the backend continues to own JWT verification. New account and job-collection routers follow the existing authenticated repository pattern and use additive SQLite tables only. UI pages call explicit typed service functions and keep all payment, SMS, deletion, export, and job-sync actions as mocks.

**Tech Stack:** Vue 3, Uni-app, Pinia, FastAPI, Pydantic, SQLite, pytest, Vitest.

## Global Constraints

- Preserve all existing API paths, response envelopes, business workflows, database tables, and migration logic.
- Do not connect real SMS, WeChat OAuth, payment, or external job sources.
- Execute P0 login/session work before P1 skeleton work.
- Keep new account deletion and data-export behavior acknowledgement-only.
- Commit independently testable backend and frontend changes with descriptive messages.

---

### Task 1: JWT Session and Phone Login

**Files:**
- Modify: `resume-miniprogram/src/stores/session.ts`, `resume-miniprogram/src/services/http.ts`
- Create: `resume-miniprogram/src/services/auth-api.ts`, `resume-miniprogram/src/types/auth.ts`, `resume-miniprogram/src/pages/login/index.vue`
- Modify: `resume-miniprogram/src/pages.json`
- Test: `resume-miniprogram/src/tests/auth-session.spec.ts`

**Interfaces:**
- Produces `setAuthSession(token, user)`, `clearAuthSession()`, `getAuthToken()`, and `request<T>()` with `Authorization: Bearer <token>`.
- Produces `sendPhoneCode`, `loginPhone`, `logout`, and `getCurrentUser` typed service functions.

- [ ] Write a failing unit test that records the request header after storing a token, then returns a 401 and asserts that the token is cleared and the login prompt is opened.
- [ ] Run `npm.cmd run test:unit -- --run src/tests/auth-session.spec.ts` and confirm the missing session behavior fails.
- [ ] Implement the smallest session adapter, HTTP header injection/401 handler, typed auth API, and phone-login page needed for the test and user flow.
- [ ] Re-run the focused test and commit the frontend P0 slice.

### Task 2: Authenticated Backend Smoke Coverage

**Files:**
- Create: `resume-backend/tests/test_phase6_auth_flow.py`

**Interfaces:**
- Consumes `/api/auth/send-code`, `/api/auth/login-phone`, `/api/auth/logout`, and an existing protected endpoint.

- [ ] Write a smoke test for demo code request, phone login, protected access with the returned Bearer token, invalidated-token 401, and logout acknowledgement.
- [ ] Run `python -m pytest tests/test_phase6_auth_flow.py -q` and confirm the expected existing path or assertion fails before adding only any necessary compatibility fix.
- [ ] Make the smallest backend correction only if the route/header contract does not satisfy the smoke test.
- [ ] Re-run the focused smoke test and commit only if backend production code changes.

### Task 3: Account Lifecycle Skeleton

**Files:**
- Create: `resume-backend/app/api/account.py`, `resume-backend/app/schemas/account.py`
- Modify: `resume-backend/main.py`
- Create: `resume-miniprogram/src/services/account-api.ts`, `resume-miniprogram/src/pages/account/index.vue`
- Modify: `resume-miniprogram/src/pages.json`
- Test: `resume-backend/tests/test_account_api.py`

**Interfaces:**
- Produces authenticated `GET /api/account/data-scope`, `POST /api/account/deletion-request`, and `POST /api/account/data-export` acknowledgement envelopes.

- [ ] Write focused API tests proving the route is JWT-protected and its deletion/export responses do not delete data.
- [ ] Run the focused test and confirm it fails because the route is absent.
- [ ] Implement static manifest and acknowledgement responses with a TODO comment at each irreversible operation boundary, then add the account page with user details and logout.
- [ ] Re-run focused tests and commit the account skeleton.

### Task 4: Favorite Jobs and Subscription Skeleton

**Files:**
- Create: `resume-backend/app/api/job_collections.py`, `resume-backend/app/repositories/job_collections.py`, `resume-backend/app/schemas/job_collections.py`
- Modify: `resume-backend/app/db.py`, `resume-backend/main.py`
- Create: `resume-miniprogram/src/services/job-collection-api.ts`, `resume-miniprogram/src/pages/job-collection/index.vue`
- Modify: `resume-miniprogram/src/pages.json`
- Test: `resume-backend/tests/test_job_collections_api.py`

**Interfaces:**
- Produces authenticated favorites list/create/delete and subscription get/update API envelopes.

- [ ] Write tests for per-user favorite ownership and persisted subscription enabled state.
- [ ] Run them and confirm failure because tables/routes do not exist.
- [ ] Add additive SQLite tables, a small repository, protected router, typed service, and a collection page. Keep external alert dispatch as a documented TODO with no network call.
- [ ] Re-run focused tests and commit the job-collection skeleton.

### Task 5: Membership and Order UI

**Files:**
- Create: `resume-miniprogram/src/services/membership-api.ts`, `resume-miniprogram/src/pages/membership/index.vue`, `resume-miniprogram/src/pages/orders/index.vue`
- Modify: `resume-miniprogram/src/pages.json`, `resume-miniprogram/src/pages/account/index.vue`
- Test: `resume-miniprogram/src/tests/membership-api.spec.ts`

**Interfaces:**
- Consumes existing `/api/user/vip-info`, `/api/pay/package-list`, `/api/pay/create-order`, `/api/pay/callback`, and `/api/user/order-list` contracts.

- [ ] Write a failing service test for the existing package/order payload mapping.
- [ ] Run the test and confirm the new service is absent.
- [ ] Implement typed service and pages; label the only checkout control as a development demo and call the existing `demo` payment callback only after creating an order.
- [ ] Re-run the focused test and commit the UI skeleton.

### Task 6: Privacy Notes, Full Verification, and Changelog

**Files:**
- Create: `docs/ACCOUNT_PRIVACY.md`, `docs/phase6-changelog.md`

- [ ] Document local storage, server record scope, acknowledgement-only deletion/export behavior, and all deferred third-party integrations.
- [ ] Run `python -m pytest tests -q`, `npm.cmd run test:unit`, and `npm.cmd run build:h5`.
- [ ] Run the Phase6 auth smoke plus a local backup/session restoration test and confirm H5 responds on `http://127.0.0.1:5186`.
- [ ] Commit docs and any remaining verification-only changes with a descriptive message.
