# Phase4 Hardening and UI Polish Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Harden exports and API failures, expose operational health, and modernize the existing career-planning UI without changing business contracts or database tables.

**Architecture:** FastAPI owns standardized errors, secure export boundaries, and health diagnostics. The existing Uni-App/dashboard surfaces retain their data flow while receiving shared feedback UI, transition states, and responsive CSS refinements.

**Tech Stack:** FastAPI, Pydantic, SQLite, pytest, Vue 3/Uni-App, TypeScript, Vitest, Vite.

## Global Constraints

- Do not change existing API success payloads, endpoint paths, or database table structure.
- Reject untrusted export identifiers and resolve files only under configured storage.
- Never return internal exception details to clients; log a concise exception summary.
- Empty export data must return a structured error before a PDF/XLSX/Word file is registered.
- Keep existing business rules and career recommendation data flow unchanged.
- H5 development server must bind `127.0.0.1:5186`.

---

### Task 1: API and Export Safety

**Files:** Modify `resume-backend/main.py`, `app/api/exports.py`, export/download services, schemas as needed; add backend tests.

- [ ] Add failing tests for database failure mapping, export failure mapping, invalid export token/path input, empty export payload, and health detail status.
- [ ] Verify each test fails because the requested Phase4 behavior is absent.
- [ ] Add concise logger-backed exception handlers that return existing `{code,data,message}` error shape for validation, database, export, and unexpected failures.
- [ ] Validate draft/token identifiers, enforce authenticated ownership before render/download, and assert generated output remains within the configured storage directory.
- [ ] Reject a resume with no visible meaningful content before Word/PDF rendering; ensure failed render output is not registered.
- [ ] Add `/api/system/health-detail` returning database-connect and storage-directory status without exposing paths or credentials.
- [ ] Run the targeted backend tests and commit with a clear Phase4 backend message.

### Task 2: Migration Operations Documentation

**Files:** Modify or add `resume-backend/migrations/README.md` and Phase4 changelog.

- [ ] Document the existing-database runbook: confirm environment, stop writes, back up SQLite/file storage, validate the backup, apply idempotent migration, verify health/detail endpoint, and retain rollback evidence.
- [ ] State explicitly that the Phase4 work is additive/non-destructive and does not drop or rewrite business tables.
- [ ] Commit documentation with the backend safety changes.

### Task 3: Dashboard and Career Visualization

**Files:** Modify existing `premium-dashboard.html`, career planner/comparison pages, app styling, export helper, and focused frontend tests where behavior is unit-testable.

- [ ] Add a shared toast/progress surface and replace browser alerts or raw blocking feedback in the touched flows.
- [ ] Add a selected-tier transition and roadmap treatment to the existing three recommendation gears without changing recommendations or store calls.
- [ ] Add comparison-card state transitions and a clear active weekly-target state.
- [ ] Add non-intrusive export progress feedback around the existing export requests/download flow.
- [ ] Apply an existing-compatible SaaS token layer: restrained shadows, hover feedback, spacing scale, responsive grid collapse, and overflow guards.
- [ ] Change Vite H5 host/port to `127.0.0.1:5186`, run frontend tests and build, and commit with a clear Phase4 frontend message.

### Task 4: Integrated Verification and Delivery

**Files:** Add `docs/PHASE4_CHANGELOG.md`; touch implementation files only for verification fixes.

- [ ] Run the backend suite, frontend unit suite, H5 build, `git diff --check`, and targeted smoke flow covering authenticated draft creation, career planning, export, and permission rejection.
- [ ] Start the H5 server at `http://127.0.0.1:5186`, verify it responds, then stop the temporary process.
- [ ] Review the final diff for API/schema compatibility and commit all uncommitted Phase4 delivery files with a concise message.
