# Membership Payment Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add three membership levels, user-owned payment orders, demo-only payment fulfillment, backend feature enforcement, and the dashboard subscription and order surfaces.

**Architecture:** Keep SQLite and JWT ownership intact. Introduce an entitlement repository and dependency as the source of truth, then compose it into existing routes. The dashboard obtains and locally caches only the current user’s display entitlement, while all security-sensitive checks remain on the API.

**Tech Stack:** FastAPI, Pydantic, SQLite, PyJWT, existing vanilla HTML/CSS/JavaScript dashboard, pytest.

## Global Constraints

- Keep existing JWT authentication, user data isolation, real LLM calls, and SQLite transition storage.
- All protected data and order actions obtain `user_id` exclusively from JWT `sub`.
- Do not implement real payment collection, auto deduction, referrals, coupons, campaigns, support tickets, enterprise plans, or cloud database migration.
- Simulated payment is available only when `PAYMENT_DEMO_MODE=true`; production must reject it.
- Reuse the dashboard’s existing CSS variables and component styles. No dependency or stylesheet is added.

---

### Task 1: Membership Persistence and Entitlement Dependency

**Files:**
- Create: `resume-backend/app/repositories/membership.py`
- Create: `resume-backend/app/services/membership.py`
- Create: `resume-backend/app/schemas/membership.py`
- Modify: `resume-backend/app/db.py`
- Modify: `resume-backend/app/config.py`
- Modify: `resume-backend/.env.example`
- Create: `resume-backend/migrations/20260814_membership_payment.sql`
- Test: `resume-backend/tests/test_membership_api.py`

**Interfaces:**
- Produces `MembershipRepository.current_vip(user_id) -> VipStatus`, `create_order(user_id, package_type) -> OrderRecord`, and `fulfill_demo_order(user_id, order_id) -> VipStatus`.
- Produces `get_current_vip` and `require_vip_feature(feature)` dependencies. `VipPermissionError` maps to `403` / `vip_required`.

- [ ] Write API tests for automatic expiry downgrade and unauthenticated membership route rejection.
- [ ] Run `pytest tests/test_membership_api.py -q` and confirm the routes are absent.
- [ ] Add idempotent tables, settings, schemas, repository, entitlement service, and migration SQL.
- [ ] Run the same test and confirm it passes.

### Task 2: Packages, Orders, Fulfillment, and API Composition

**Files:**
- Create: `resume-backend/app/api/membership.py`
- Modify: `resume-backend/main.py`
- Modify: `resume-backend/tests/test_membership_api.py`

**Interfaces:**
- `GET /api/user/vip-info`, `GET /api/pay/package-list`, `POST /api/pay/create-order`, `POST /api/pay/callback`, `GET /api/user/order-list` require JWT.
- Packages are `monthly`, `quarterly`, `annual`. Demo callback uses `payment_channel: demo` and is idempotent.

- [ ] Write failing tests for package list, order isolation, rejected production demo callback, and successful demo fulfillment.
- [ ] Run the focused test file and confirm these cases fail.
- [ ] Add the router, application state dependencies, error handler, and demo-mode configuration gate.
- [ ] Re-run the focused test file and confirm it passes.

### Task 3: Enforce Tier Limits and Export Watermarks

**Files:**
- Modify: `resume-backend/app/api/drafts.py`
- Modify: `resume-backend/app/api/career.py`
- Modify: `resume-backend/app/api/assessment.py`
- Modify: `resume-backend/app/api/exports.py`
- Modify: `resume-backend/app/services/export_word.py`
- Modify: `resume-backend/app/services/export_pdf.py`
- Modify: `resume-backend/tests/test_membership_api.py`

**Interfaces:**
- Free users can retain up to 3 drafts and compare up to 2 roles; Basic/Premium can compare up to 4 roles.
- Free exports receive `Resume Dashboard Free` watermark, Basic receives `Resume Dashboard Basic`, Premium receives no watermark.

- [ ] Write failing tests for Free draft limit, Free role cap, and watermark selector behavior.
- [ ] Run the focused tests and confirm failures identify the missing entitlement behavior.
- [ ] Use explicit `VipStatus` dependencies in routes, preserve all existing route payloads, and pass watermark intent into both renderers.
- [ ] Re-run focused tests, then `pytest -p no:cacheprovider tests -q`.

### Task 4: Dashboard Membership and Order Experience

**Files:**
- Modify: `premium-dashboard.html`
- Modify: `scripts/verify-premium-dashboard.mjs`

**Interfaces:**
- Adds `state.vip`, `refreshVipStatus()`, `requireVipFeature(feature)`, and `openMembershipModal()`.
- Adds `/membership` and `/orders` page renderers using current navigation and card patterns.
- Handles API `vip_required` centrally; package purchase creates then demo-completes a server order.

- [ ] Extend the static verifier with assertions for the membership endpoints, badge, page routes, and privilege interceptor.
- [ ] Run `node scripts/verify-premium-dashboard.mjs` and confirm it fails.
- [ ] Add scoped VIP cache, top navigation badge, package view, order history view, demo checkout, feature prechecks, and Free draft-count UI guard.
- [ ] Run verifier and browser smoke checks at desktop and mobile widths; repair only concrete defects found.

### Task 5: Release Verification and Delivery

**Files:**
- Modify as required only by verification fixes.

- [ ] Run backend suite, dashboard static verifier, H5 build, and syntax/whitespace checks.
- [ ] Run the Impeccable detector once on `premium-dashboard.html`, inspect desktop and mobile screenshots in one batch, and correct all actionable issues in one pass.
- [ ] Obtain a code-review pass, resolve findings, re-run affected checks, commit cohesive changes, and push `feature/ai-resume-demo` to `origin`.
