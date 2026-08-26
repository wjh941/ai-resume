# Web Response Contract Test Coverage Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close the remaining Web list-response regression coverage gap without changing production behavior.

**Architecture:** Extend the existing Vitest domain tests with envelope fixtures for every migrated list adapter and add a source-level CareerView adapter guard. Reuse the real `readItems` helper by mocking only `requestApi`; no production source or backend changes are needed.

**Tech Stack:** Vue 3 + TypeScript source contracts, Vitest, Vite.

## Global Constraints

- No production source changes, API routes, request payloads, mock data, Chinese copy, page structure, or business logic changes.
- Keep direct-array and `{ items: T[] }` behavior covered for all migrated list adapters.
- Use existing Vitest/Vite tooling only; add no dependencies.
- Preserve the existing backend API contract and mock-mode behavior.

---

### Task 1: Complete domain adapter envelope coverage

**Files:**
- Modify: `web-frontend/src/tests/domain-api.spec.ts`

**Interfaces:**
- Tests call the unchanged public adapters: `listApplications`, `listTimeline`, `listCareerTasks`, `listMembershipPackages`, `listOrders`, and `getEvidenceSuggestions`.
- The tests keep the existing `requestApi` mock and real `readItems` helper.

- [ ] **Step 1: Add failing envelope fixtures**

Add tests or extend the direct-array cases so each listed adapter receives an
`{ items: [...] }` payload and asserts the current camelCase result. Add an
envelope fixture for evidence suggestions using the existing snake_case fields.

- [ ] **Step 2: Run the focused domain suite**

Run: `npm.cmd test -- src/tests/domain-api.spec.ts`

Expected: the new tests pass against the current helper-backed adapters; if a
fixture exposes a missing adapter import or mapping, correct only the test
fixture or adapter call needed by the existing contract.

- [ ] **Step 3: Commit the domain coverage**

```bash
git add web-frontend/src/tests/domain-api.spec.ts
git commit -m "test: cover web list response envelopes"
```

### Task 2: Lock the page adapter boundary and verify

**Files:**
- Modify: `web-frontend/src/tests/interaction.spec.ts`
- Modify: `docs/interaction-upgrade-changelog.md`

**Interfaces:**
- The static contract reads `web-frontend/src/views/CareerView.vue` and
  asserts it imports/calls `listCareerTasks` and renders `dueDate`.
- No runtime component behavior changes.

- [ ] **Step 1: Add the failing source contract**

Add a source assertion for the CareerView adapter import, list call, and
camelCase due-date field. Verify it fails only if the view regresses to direct
`.items` access.

- [ ] **Step 2: Run the focused interaction suite**

Run: `npm.cmd test -- src/tests/interaction.spec.ts`

Expected: the source contract passes on the current fixed CareerView.

- [ ] **Step 3: Append the changelog entry**

Record the completed envelope fixtures and CareerView adapter guard as test
coverage only. State explicitly that production routes, payloads, mock data,
Chinese copy, and business logic are unchanged.

- [ ] **Step 4: Run complete verification**

Run: `npm.cmd test`

Expected: all Web test files pass.

Run: `npm.cmd run build`

Expected: Vite exits with code `0`.

Run: `git diff --check`

Expected: no whitespace errors.

- [ ] **Step 5: Commit documentation and tests**

```bash
git add web-frontend/src/tests/interaction.spec.ts docs/interaction-upgrade-changelog.md
git commit -m "docs: record web response contract test coverage"
git status --short
```

Expected: status output is empty.
