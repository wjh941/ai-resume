# Web View Code-Splitting Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Load existing Web business views on demand and reduce the initial JavaScript payload without changing business behavior.

**Architecture:** Keep `App.vue` as the authenticated shell and replace eager
view imports with a typed map of Vue async components. Each loader uses a
dynamic import and the existing `LoadingSpinner`; the keyed out-in transition
and event bindings remain untouched.

**Tech Stack:** Vue 3 `defineAsyncComponent`, Vite dynamic imports, Vitest,
native CSS.

## Global Constraints

- No new pages, capabilities, dependencies, API routes, request payloads, mock data, Chinese copy, or business-logic changes.
- Preserve `WorkspaceView`, `editingDraftId`, emitted events, transition keys, loading shell height, and reduced-motion behavior.
- H5 source and build behavior remains unchanged.
- Verify focused tests, full H5/Web suites, both builds, entry size, detector, and `git diff --check`.

---

### Task 1: Add async-view source contract

**Files:**
- Modify: `web-frontend/src/tests/interaction.spec.ts`

**Interfaces:**
- The contract reads `web-frontend/src/App.vue` and asserts the shared
  loading component, `defineAsyncComponent`, dynamic imports, and unchanged
  transition/event boundary.

- [ ] **Step 1: Add failing assertions**

Assert that App.vue imports `defineAsyncComponent` and `LoadingSpinner`, defines
an async component loader, includes dynamic imports for each existing view, and
retains `mode="out-in"` and the existing `@navigate`/`@open-draft` bindings.

- [ ] **Step 2: Run the focused test and confirm failure**

Run `npm.cmd test -- src/tests/interaction.spec.ts` from `web-frontend`.
Expected: the new async-view assertions fail against the eager imports.

### Task 2: Implement view-level code splitting

**Files:**
- Modify: `web-frontend/src/App.vue`

**Interfaces:**
- `activeComponent` continues to return the component selected by the same
  `WorkspaceView` key; the template emits and props remain unchanged.

- [ ] **Step 1: Replace eager view imports**

Import `Component`, `computed`, and `defineAsyncComponent` from Vue, import the
existing `LoadingSpinner`, and define a small `asyncView` helper with
`loadingComponent: LoadingSpinner`, `delay: 120`, and `suspensible: false`.
Create the existing view map with `() => import("./views/<View>.vue")` loaders,
using `OverviewView`, `ResumeView`, `CareerView`, `JobsView`, `ApplicationsView`,
`EvidenceView`, `MembershipView`, `AssessmentView`, `ComparisonView`,
`InsightsView`, `AccountView`, and `ResumeEditorView`, then keep the current
computed lookup and template structure.

- [ ] **Step 2: Run the focused test and confirm pass**

Run `npm.cmd test -- src/tests/interaction.spec.ts` from `web-frontend`.
Expected: all interaction tests pass, including transition/event assertions.

- [ ] **Step 3: Build and record bundle split**

Run `npm.cmd run build` from `web-frontend`; verify the output includes multiple
view chunks and the entry JS asset is smaller than 192.66 kB.

- [ ] **Step 4: Commit implementation**

`git add web-frontend/src/App.vue web-frontend/src/tests/interaction.spec.ts && git commit -m "perf: split web views into async chunks"`

### Task 3: Document and verify

**Files:**
- Modify: `docs/interaction-upgrade-changelog.md`

**Interfaces:**
- Documentation records payload/perceived-loading improvements only; all
  existing business modules and API contracts remain intact.

- [ ] **Step 1: Append changelog entry**

Record the async Web view loading, shared spinner reuse, preserved transition,
and unchanged H5/business/API scope.

- [ ] **Step 2: Run complete verification**

Run Web `npm.cmd test` and `npm.cmd run build`; H5 `npm.cmd run test:unit` and
`npm.cmd run build:h5`; run Impeccable detector once over `web-frontend/src/App.vue`
and `web-frontend/src/styles/base.css`; finish with `git diff --check` and
`git status --short`.

- [ ] **Step 3: Commit documentation**

`git add docs/interaction-upgrade-changelog.md && git commit -m "docs: record web view code splitting"`
