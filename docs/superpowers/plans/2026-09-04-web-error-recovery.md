# Web Error Recovery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make recoverable Web reads and idempotent queries actionable while preventing duplicate mutation submissions.

**Architecture:** Add a small pure error-copy mapper beside the existing API errors. Each view keeps its current request function and wires a retry button only to safe read/query failures; mutation failures remain message-only.

**Tech Stack:** Vue 3, TypeScript, Vitest, native Fetch/AbortController.

## Global Constraints

- No automatic retry loops or backoff.
- No global error event bus.
- No backend, mini-program, dependency, or payment changes.
- No persistence of API results.
- All production behavior changes require a failing test before implementation.

---

### Task 1: Shared API error copy

**Files:**
- Create: `web-frontend/src/lib/api-error.ts`
- Create: `web-frontend/src/tests/api-error.spec.ts`

**Interfaces:**
- `getApiErrorMessage(reason: unknown, fallback: string): string` returns Chinese user-facing copy.
- `ApiTimeoutError` maps to `请求超时，请稍后重试`.
- `ApiRequestError` status `401` maps to `登录已过期，请重新登录后继续`.
- `ApiRequestError` status `403` maps to `当前功能暂不可用，请查看会员权益`.
- Network-like errors map to `网络连接失败，请检查网络后重试`.
- All other reasons return the caller-provided fallback.

- [ ] **Step 1: Write failing tests**

Add cases for timeout, 401, 403, `TypeError`, and generic fallback using the real exported helper and API error classes.

- [ ] **Step 2: Run focused tests to verify they fail**

Run: `npm.cmd run test -- src/tests/api-error.spec.ts`

Expected: FAIL because `api-error.ts` does not exist.

- [ ] **Step 3: Implement the minimal mapper**

Use `instanceof ApiTimeoutError` / `instanceof ApiRequestError`, status checks, and a narrow network-error predicate. Do not add retries or logging.

- [ ] **Step 4: Run focused tests to verify they pass**

Run: `npm.cmd run test -- src/tests/api-error.spec.ts`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add web-frontend/src/lib/api-error.ts web-frontend/src/tests/api-error.spec.ts
git commit -m "feat(web): centralize api error copy"
```

### Task 2: Add safe read retries

**Files:**
- Modify: `web-frontend/src/views/ResumeView.vue`
- Modify: `web-frontend/src/views/CareerView.vue`
- Modify: `web-frontend/src/views/EvidenceView.vue`
- Modify: `web-frontend/src/views/ApplicationsView.vue`
- Modify: `web-frontend/src/views/MembershipView.vue`
- Modify: `web-frontend/src/views/AccountView.vue`
- Create: `web-frontend/src/tests/read-recovery.spec.ts`

**Interfaces:**
- Existing page `refresh` functions remain the only read entry points.
- Read failures call `getApiErrorMessage(reason, fallback)`.
- Their `ErrorNotice` renders an `AsyncButton` that calls the same `refresh` function.
- Mutation catches remain message-only and do not render a retry slot.

- [ ] **Step 1: Write failing source-contract tests**

Assert each view imports `getApiErrorMessage`, maps its refresh catch, and places a retry action inside the page-level `ErrorNotice`. Assert mutation handlers do not use the page retry callback.

- [ ] **Step 2: Run focused tests to verify they fail**

Run: `npm.cmd run test -- src/tests/read-recovery.spec.ts src/tests/interaction.spec.ts`

Expected: FAIL because the views still use generic catches and lack retry slots.

- [ ] **Step 3: Implement read recovery**

Update only refresh catches and page-level error notices. Keep all existing form inputs, list state, and mutation handlers intact.

- [ ] **Step 4: Run focused tests to verify they pass**

Run: `npm.cmd run test -- src/tests/read-recovery.spec.ts src/tests/interaction.spec.ts`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add web-frontend/src/views/ResumeView.vue web-frontend/src/views/CareerView.vue web-frontend/src/views/EvidenceView.vue web-frontend/src/views/ApplicationsView.vue web-frontend/src/views/MembershipView.vue web-frontend/src/views/AccountView.vue web-frontend/src/tests/read-recovery.spec.ts
git commit -m "feat(web): add safe read retries"
```

### Task 3: Add safe query retries

**Files:**
- Modify: `web-frontend/src/views/JobsView.vue`
- Modify: `web-frontend/src/views/InsightsView.vue`
- Modify: `web-frontend/src/tests/query-continuity.spec.ts`

**Interfaces:**
- Jobs and Insights query catches use `getApiErrorMessage(reason, fallback)`.
- Their error notices retry `queryRole` / `queryInsights` with the existing refs.
- Query input snapshots remain input-only and user-scoped.

- [ ] **Step 1: Write failing tests**

Extend query continuity assertions to require the shared mapper, caught reason parameter, and retry action wired to each query function.

- [ ] **Step 2: Run focused tests to verify they fail**

Run: `npm.cmd run test -- src/tests/query-continuity.spec.ts`

Expected: FAIL because the views currently use generic catches and no query retry action.

- [ ] **Step 3: Implement query recovery**

Map query errors and add one `AsyncButton` retry action to each query error notice. Preserve the existing input snapshots and result handling.

- [ ] **Step 4: Run focused tests to verify they pass**

Run: `npm.cmd run test -- src/tests/query-continuity.spec.ts`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add web-frontend/src/views/JobsView.vue web-frontend/src/views/InsightsView.vue web-frontend/src/tests/query-continuity.spec.ts
git commit -m "feat(web): retry failed queries"
```

### Task 4: Full verification and handoff

**Files:** None beyond Tasks 1-3.

- [ ] **Step 1: Run the full Web test suite**

Run: `npm.cmd run test` from `web-frontend`.

- [ ] **Step 2: Run strict TypeScript and production build**

Run strict `tsc` for changed library files and `npm.cmd run build`.

- [ ] **Step 3: Run detector and diff checks**

Run the Impeccable detector on changed Web sources and `git diff --check`.

- [ ] **Step 4: Review the final diff**

Confirm no backend, mini-program, dependency, API-result persistence, or mutation auto-retry changes entered the diff.
