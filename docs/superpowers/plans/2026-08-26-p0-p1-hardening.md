# P0/P1 Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task.

**Goal:** Fix the release-blocking data-isolation, authentication, persistence, import, and account-lifecycle issues found in the project audit.

**Architecture:** Keep existing Pinia stores, FastAPI routers, and API clients. Add the smallest shared session/storage helpers needed for per-user namespacing, make optional premium requests independently recoverable, and preserve existing public APIs.

**Tech Stack:** Vue 3, Pinia, uni-app, FastAPI, Pydantic, pytest, Vitest.

## Global Constraints

- Preserve existing routes and request payloads unless a security fix requires a header or schema field.
- Write a failing regression test before each production-code change.
- Do not add dependencies; reuse current storage, auth, and test helpers.
- Keep all user-facing copy in Simplified Chinese.

---

### Task 1: Isolate local workspace data by authenticated user

**Files:** `resume-miniprogram/src/stores/session.ts`, `src/stores/{resume,career,consultation,applications}.ts`, `src/main.ts`, related Vitest tests.

Add a user-scoped storage-key helper, restore stores only after a valid session exists, and clear all workspace keys during logout/account deletion. Cover login switching and pending application queues with tests.

### Task 2: Repair authenticated PDF upload and safe import behavior

**Files:** `resume-miniprogram/src/services/resume-api.ts`, import/editor views, backend import service and tests.

Send the bearer token with `uni.uploadFile`; do not overwrite a draft with an empty/mock parse result. Keep unsupported parsing explicit until a real parser is available and test the failure path.

### Task 3: Make assessment and planner state recoverable

**Files:** assessment page/store/API client, career planner store/page, backend assessment tests where needed.

Load assessment questions independently from VIP insights, restore saved reports, and persist/restore planner results. Add regression tests for free users and refresh recovery.

### Task 4: Fix account deletion and production guards

**Files:** account page, backend config/import lifecycle, deployment tests.

Clear local data and route to login after deletion; reject the development JWT secret in production; add import-file expiry/cleanup and deployment checks without changing current demo-mode behavior.

### Task 5: Establish the first visual/accessibility pass

**Files:** job collection, resume editor, dashboard/onboarding, tabs/listbox, shared styles and focused frontend tests.

Restore missing page styles, fix narrow-screen overflow, add modal focus handling and ARIA semantics, improve CTA contrast, remove motion warnings, and unify repeated visual tokens.

### Task 6: Verify and document remaining production gaps

Run frontend/backend tests, typecheck, H5 build, and dashboard verification. Record unresolved external integrations (WeChat, SMS, payment, push, job source) behind explicit feature flags or release notes.
