# Web Query Continuity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task with verification checkpoints.

**Goal:** Preserve job-search intent across refreshes and make timeout failures readable and retryable in the Web workbench.

**Architecture:** Extend the existing Fetch wrapper with a timeout-specific error while keeping caller aborts unchanged. Reuse the existing user-scoped `workspace-recovery` helpers in Jobs and Insights for small typed input snapshots; API results remain server-fetched.

**Tech Stack:** Vue 3, TypeScript, Vitest, native Fetch/AbortController/sessionStorage.

## Global Constraints

- No new npm dependencies.
- No URL query parameters or shareable links.
- No persistence of API results or full resume payloads.
- No backend or mini-program changes.
- All production behavior changes require a failing test before implementation.

---

### Task 1: Localize timeout failures

**Files:**
- Modify: `web-frontend/src/lib/api.ts`
- Modify: `web-frontend/src/tests/api.spec.ts`

**Interfaces:**
- Export `ApiTimeoutError` as an `ApiRequestError` subtype with status `0` and message `请求超时，请稍后重试`.
- `requestApi` and `downloadApi` preserve caller-provided abort errors unchanged.

- [ ] **Step 1: Write failing tests**

Add JSON and binary timeout assertions requiring `ApiTimeoutError` and the exact Chinese message. Keep an intentional caller abort assertion requiring the original `DOMException` instance.

- [ ] **Step 2: Run focused tests to verify they fail**

Run: `npm.cmd run test -- src/tests/api.spec.ts`
Expected: FAIL because timeouts currently surface as raw `AbortError`.

- [ ] **Step 3: Implement timeout classification**

Track whether the internal timeout controller fired. When an abort error occurs after that timer, throw `ApiTimeoutError`; when the caller signal caused it, rethrow the original error. Apply this to fetch and response-body reads in both API functions.

- [ ] **Step 4: Run focused tests to verify they pass**

Run: `npm.cmd run test -- src/tests/api.spec.ts`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add web-frontend/src/lib/api.ts web-frontend/src/tests/api.spec.ts
git commit -m "fix(web): localize request timeout errors"
```

### Task 2: Recover Jobs and Insights query inputs

**Files:**
- Modify: `web-frontend/src/views/JobsView.vue`
- Modify: `web-frontend/src/views/InsightsView.vue`
- Modify: `web-frontend/src/tests/interaction.spec.ts`
- Create: `web-frontend/src/tests/query-continuity.spec.ts`

**Interfaces:**
- Jobs snapshot feature key: `jobs-query`, shape `{ roleName: string; reportMode: "simplified" | "professional" }`.
- Insights snapshot feature key: `insights-query`, shape `{ roleName: string; year: string; reportMode: "simplified" | "professional" }`.

- [ ] **Step 1: Write failing tests**

Add source assertions that both views read/write `workspace-recovery` snapshots and a pure test that invalid mode/year values fall back to defaults. Update no existing behavior assertions unrelated to query continuity.

- [ ] **Step 2: Run focused tests to verify they fail**

Run: `npm.cmd run test -- src/tests/query-continuity.spec.ts`
Expected: FAIL because the views do not reference query recovery.

- [ ] **Step 3: Implement Jobs recovery**

Guard `sessionStorage` access, read a validated `jobs-query` snapshot during setup, initialize `roleName`/`reportMode`, and watch the two refs deeply enough to persist changes. Do not persist `result`.

- [ ] **Step 4: Implement Insights recovery**

Guard storage access, read a validated `insights-query` snapshot during setup, initialize `roleName`/`year`/`reportMode`, and persist input changes. Accept only years from 2000 through 2100 and the two known modes.

- [ ] **Step 5: Run focused tests to verify they pass**

Run: `npm.cmd run test -- src/tests/query-continuity.spec.ts src/tests/interaction.spec.ts`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add web-frontend/src/views/JobsView.vue web-frontend/src/views/InsightsView.vue web-frontend/src/tests/query-continuity.spec.ts web-frontend/src/tests/interaction.spec.ts
git commit -m "feat(web): preserve job query intent"
```

### Task 3: Full verification and handoff

**Files:** None beyond Tasks 1-2.

- [ ] **Step 1: Run full Web tests**

Run: `npm.cmd run test` from `web-frontend`.
Expected: 0 failures and no unhandled errors.

- [ ] **Step 2: Run strict TypeScript and production build**

Run strict `tsc` for changed helper/API files and `npm.cmd run build`.
Expected: exit code 0 for both.

- [ ] **Step 3: Run detector and diff checks**

Run Impeccable detector on changed UI files and `git diff --check`.
Expected: no new detector findings and no whitespace errors.

- [ ] **Step 4: Commit any test-only adjustments and record verification**

Update the SDD ledger with the verified commit hashes and command results; do not modify unrelated dirty files.
