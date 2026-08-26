# Long-list Responsive Polish Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reduce scroll-time layout work for existing long lists while preserving all business behavior and responsive layouts.

**Architecture:** Reuse the existing H5 `ui-long-list-item` class and add one
CSS containment rule to the existing Web list-surface selectors. Template
changes are limited to the H5 draft row class; no data or runtime logic moves.

**Tech Stack:** Vue 3, uni-app H5, native CSS containment, Vitest, Vite.

## Global Constraints

- No new pages, modules, API endpoints, request payloads, mock data, Chinese copy, or business logic.
- Use native CSS `content-visibility`/`contain` only; add no dependencies.
- Preserve incremental list windows, table horizontal scrolling, responsive breakpoints, accessibility, and reduced-motion behavior.
- Run H5/Web unit tests, H5/Web builds, and `git diff --check`.

---

### Task 1: Cover long-list containment contracts

**Files:**
- Modify: `resume-miniprogram/src/tests/interaction.spec.ts`
- Modify: `web-frontend/src/tests/interaction.spec.ts`

**Interfaces:**
- Tests read existing source files as static contracts, matching the current
  project testing style; no Vue Test Utils or dependency is introduced.

- [ ] **Step 1: Add failing source assertions**

Assert the H5 drafts template uses `ui-long-list-item`, and the Web base CSS
declares the list-surface containment selector for the existing list classes.

- [ ] **Step 2: Run focused tests and confirm failure**

Run `npm.cmd test -- src/tests/interaction.spec.ts` from each frontend.
Expected: the new assertions fail before the template/CSS contract exists.

- [ ] **Step 3: Implement the minimal template/CSS contract**

Add `ui-long-list-item` to the existing H5 draft row and add the Web list
surface selector with native containment and intrinsic size reservation.

- [ ] **Step 4: Run focused tests and confirm pass**

Run the same focused commands. Expected: all focused tests pass.

- [ ] **Step 5: Commit**

`git add resume-miniprogram/src/pages/drafts/index.vue resume-miniprogram/src/tests/interaction.spec.ts web-frontend/src/styles/base.css web-frontend/src/tests/interaction.spec.ts && git commit -m "perf: isolate long list rendering surfaces"`

### Task 2: Document and verify

**Files:**
- Modify: `docs/interaction-upgrade-changelog.md`

**Interfaces:**
- Documentation records only the containment polish; all existing module and
  API contracts remain unchanged.

- [ ] **Step 1: Append the changelog entry**

Record the H5 draft-row containment and Web list-surface isolation, explicitly
noting that list windows, table scrolling, routes, APIs, and business logic
remain unchanged.

- [ ] **Step 2: Run complete verification**

Run H5 `npm.cmd run test:unit` and `npm.cmd run build:h5`; run Web `npm.cmd test`
and `npm.cmd run build`; finish with `git diff --check` and `git status --short`.

- [ ] **Step 3: Commit documentation**

`git add docs/interaction-upgrade-changelog.md && git commit -m "docs: record long list rendering polish"`
