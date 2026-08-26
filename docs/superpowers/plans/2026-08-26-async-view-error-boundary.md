# Async View Error Boundary Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a bounded async-view chunk retry and visible error boundary to the existing Web workbench.

**Architecture:** Add `AsyncViewError.vue` as a presentation-only wrapper around
the globally registered `ErrorNotice`. Configure the existing `asyncView`
factory in `App.vue` with `errorComponent` and a two-retry `onError` callback;
all view loaders, keys, events, and transitions remain the same.

**Tech Stack:** Vue 3 `defineAsyncComponent`, Vitest, Vite, native CSS.

## Global Constraints

- No new business pages, API routes, request payloads, mock data, Chinese copy changes, or H5 changes.
- Retry only dynamic-import failures; do not alter page-level API loading/error handling.
- Reuse existing `ErrorNotice` semantics and CSS; add no dependency.
- Verify focused/full Web and H5 tests, both builds, detector, and diff checks.

---

### Task 1: Add failing error-boundary contracts

**Files:**
- Modify: `web-frontend/src/tests/interaction.spec.ts`

**Interfaces:**
- Static source contracts read `App.vue` and `components/AsyncViewError.vue`.

- [ ] **Step 1: Add failing assertions**

Assert App.vue imports `AsyncViewError`, configures `errorComponent`, includes
`onError`, retries while `attempts <= 2`, and calls `fail(error)`. Assert the
component wraps `<ErrorNotice ... role="alert">` through its shared component.

- [ ] **Step 2: Run the focused test and confirm failure**

Run `npm.cmd test -- src/tests/interaction.spec.ts` from `web-frontend`.
Expected: the new assertions fail because the error component and options do
not yet exist.

### Task 2: Implement bounded async-view failure UI

**Files:**
- Create: `web-frontend/src/components/AsyncViewError.vue`
- Modify: `web-frontend/src/App.vue`

**Interfaces:**
- `AsyncViewError` is a presentation-only component with no API calls or
  emitted business events.
- `asyncView` continues to return a `Component` for the existing view map.

- [ ] **Step 1: Add the shared error component**

Render `<ErrorNotice message="页面加载失败，请刷新后重试" compact />` and keep
the component free of request or navigation logic.

- [ ] **Step 2: Configure retry and error rendering**

Import `AsyncViewError` and add `errorComponent: AsyncViewError` plus
`onError(error, retry, fail, attempts) { if (attempts <= 2) retry(); else fail(error) }`
to the existing async component options. Leave all loaders and template events
unchanged.

- [ ] **Step 3: Run focused tests and build**

Run the focused Web interaction test and `npm.cmd run build`; expect all tests
green and the existing view chunks still emitted.

- [ ] **Step 4: Commit implementation**

`git add web-frontend/src/App.vue web-frontend/src/components/AsyncViewError.vue web-frontend/src/tests/interaction.spec.ts && git commit -m "fix: show web view chunk load errors"`

### Task 3: Document and verify

**Files:**
- Modify: `docs/interaction-upgrade-changelog.md`

**Interfaces:**
- Documentation records only async-view failure handling; all business/API
  behavior remains unchanged.

- [ ] **Step 1: Append changelog entry**

Record the bounded retries, shared ErrorNotice fallback, and unchanged H5/API
scope.

- [ ] **Step 2: Run complete verification**

Run Web `npm.cmd test` and `npm.cmd run build`; H5 `npm.cmd run test:unit` and
`npm.cmd run build:h5`; run the Impeccable detector once over `App.vue`,
`AsyncViewError.vue`, and `base.css`; finish with `git diff --check` and
`git status --short`.

- [ ] **Step 3: Commit documentation**

`git add docs/interaction-upgrade-changelog.md && git commit -m "docs: record async view error boundary"`
