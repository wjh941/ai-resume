# Web Resilience And Recovery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task with verification checkpoints.

**Goal:** Prevent avoidable Web work loss and dead-end states through immediate deletion logout, session-scoped recovery, retryable account loading, bounded API requests, and truthful status copy.

**Architecture:** Reuse the existing Vue app session state, `AsyncButton`, Fetch wrapper, and browser `sessionStorage`. Add one small storage helper for feature snapshots. Account deletion communicates upward through an existing component event boundary so `App` remains the single owner of session cleanup.

**Tech Stack:** Vue 3, TypeScript, Vitest, native Fetch/AbortController/sessionStorage, lucide-vue-next.

## Global Constraints

- No new npm dependencies.
- No backend API changes.
- Preserve unrelated user changes in the dirty worktree.
- Keep recovery data scoped by authenticated user id and limited to small transient form state.
- All production behavior changes require a failing test before implementation.

---

### Task 1: Add account deletion session closeout

**Files:**
- Modify: `web-frontend/src/views/AccountView.vue`
- Modify: `web-frontend/src/App.vue`
- Test: `web-frontend/src/tests/retention-hardening.spec.ts`

**Interfaces:**
- `AccountView` emits `deleted` after `POST /api/account/deletion-request` succeeds.
- `App` handles `deleted` by clearing the local session and returning to the login surface with a completion notice.

- [ ] **Step 1: Write the failing test**

Add assertions that `AccountView.vue` emits `deleted` after the deletion request and that `App.vue` handles the event by clearing the session and rendering a deletion notice.

- [ ] **Step 2: Run the focused test to verify it fails**

Run: `npm.cmd exec vitest -- src/tests/retention-hardening.spec.ts`
Expected: FAIL because the event and App handler do not exist.

- [ ] **Step 3: Implement the minimal event path**

Add `deleted` to the AccountView emit type, call `emit("deleted")` after the successful request, and add an App handler that calls `clearSession()`, sets `session.value = null`, and sets a login notice prop. Keep the existing session-expired notice behavior distinct.

- [ ] **Step 4: Run the focused test to verify it passes**

Run: `npm.cmd exec vitest -- src/tests/retention-hardening.spec.ts`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add web-frontend/src/views/AccountView.vue web-frontend/src/App.vue web-frontend/src/tests/retention-hardening.spec.ts
git commit -m "fix(web): close session after account deletion"
```

### Task 2: Add user-scoped session recovery helpers

**Files:**
- Create: `web-frontend/src/lib/workspace-recovery.ts`
- Modify: `web-frontend/src/views/AssessmentView.vue`
- Modify: `web-frontend/src/views/ComparisonView.vue`
- Test: `web-frontend/src/tests/workspace-recovery.spec.ts`

**Interfaces:**
- `readWorkspaceSnapshot<T>(storage, userId, feature): T | null`
- `writeWorkspaceSnapshot<T>(storage, userId, feature, value): void`
- `clearWorkspaceSnapshot(storage, userId, feature): void`

- [ ] **Step 1: Write the failing tests**

Cover round-trip storage, malformed-value rejection, and user isolation. Add source assertions that assessment answers and comparison selections use the helper.

- [ ] **Step 2: Run the focused test to verify it fails**

Run: `npm.cmd exec vitest -- src/tests/workspace-recovery.spec.ts`
Expected: FAIL because the helper module does not exist.

- [ ] **Step 3: Implement the helper**

Use `sessionStorage`-compatible `Storage`, a fixed key prefix, JSON serialization, and `try/catch` so unavailable storage or malformed values degrade to `null`/no-op.

- [ ] **Step 4: Wire assessment recovery**

Read the authenticated user id from `readSession()` on setup, restore `answers` if valid, watch answer changes to write a small snapshot, and clear it after a successful submit.

- [ ] **Step 5: Wire comparison recovery**

Read and validate the string-array selection snapshot, write on selection changes, and clear it after a successful comparison result.

- [ ] **Step 6: Run focused tests to verify they pass**

Run: `npm.cmd exec vitest -- src/tests/workspace-recovery.spec.ts src/tests/assessment-workflow.spec.ts src/tests/comparison-workflow.spec.ts`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add web-frontend/src/lib/workspace-recovery.ts web-frontend/src/views/AssessmentView.vue web-frontend/src/views/ComparisonView.vue web-frontend/src/tests/workspace-recovery.spec.ts
git commit -m "feat(web): recover transient workspace inputs"
```

### Task 3: Make account loading retryable and API calls bounded

**Files:**
- Modify: `web-frontend/src/views/AccountView.vue`
- Modify: `web-frontend/src/lib/api.ts`
- Modify: `web-frontend/src/tests/api.spec.ts`
- Modify: `web-frontend/src/tests/retention-hardening.spec.ts`

**Interfaces:**
- `requestApi` and `downloadApi` keep their current signatures and reject with an abort error when the default timeout elapses.

- [ ] **Step 1: Write failing tests**

Add an API test proving a never-settling fetch receives an abort signal and rejects after the configured timeout using fake timers. Add a source assertion that AccountView renders a retry action calling `refresh`.

- [ ] **Step 2: Run focused tests to verify they fail**

Run: `npm.cmd exec vitest -- src/tests/api.spec.ts src/tests/retention-hardening.spec.ts`
Expected: FAIL because no timeout or account retry action exists.

- [ ] **Step 3: Implement timeout handling**

Create an internal `withTimeoutSignal` helper using `AbortController`, a 15-second default, and cleanup of the timer/listeners. Compose with a caller signal when present. Use it in both Fetch calls and preserve existing 401/error handling.

- [ ] **Step 4: Implement account retry UI**

Import `RefreshCw`, add a heading action that calls `refresh`, and make its loading state reflect `loading`.

- [ ] **Step 5: Run focused tests to verify they pass**

Run: `npm.cmd exec vitest -- src/tests/api.spec.ts src/tests/retention-hardening.spec.ts`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add web-frontend/src/lib/api.ts web-frontend/src/views/AccountView.vue web-frontend/src/tests/api.spec.ts web-frontend/src/tests/retention-hardening.spec.ts
git commit -m "fix(web): bound requests and retry account loading"
```

### Task 4: Correct topbar status and run full verification

**Files:**
- Modify: `web-frontend/src/components/WebTopbar.vue`
- Modify: `web-frontend/src/tests/interaction.spec.ts`

- [ ] **Step 1: Write the failing test**

Change the static copy assertion to require `工作区已就绪` and reject the old live-connection claim.

- [ ] **Step 2: Run the focused test to verify it fails**

Run: `npm.cmd exec vitest -- src/tests/interaction.spec.ts`
Expected: FAIL because the old copy remains.

- [ ] **Step 3: Implement the copy change**

Replace the status text with `工作区已就绪` without introducing fake connectivity state.

- [ ] **Step 4: Run the full verification suite**

Run: `npm.cmd run test` and `npm.cmd run build` from `web-frontend`.
Expected: 0 test failures and build exit code 0.

- [ ] **Step 5: Run frontend detector and diff checks**

Run: `node C:\Users\16102\.codex\skills\impeccable\scripts\detect.mjs --json web-frontend/src/App.vue web-frontend/src/components/WebTopbar.vue web-frontend/src/components/LoginPanel.vue web-frontend/src/lib/api.ts web-frontend/src/lib/workspace-recovery.ts web-frontend/src/views/AccountView.vue web-frontend/src/views/AssessmentView.vue web-frontend/src/views/ComparisonView.vue`, then `git diff --check`.
Expected: no new detector findings for changed files and no whitespace errors.

- [ ] **Step 6: Commit**

```bash
git add web-frontend/src/components/WebTopbar.vue web-frontend/src/tests/interaction.spec.ts
git commit -m "fix(web): clarify workspace readiness status"
```
