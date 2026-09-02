# Application Form Leave Guard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prevent accidental loss of unsaved application, timeline, and reminder input in the web application tracker.

**Architecture:** Add a pure snapshot comparison helper for the three form layers, then wire it into `ApplicationsView.vue` with the existing pending-action guard, an inline confirmation region, and a conditional `beforeunload` listener. Keep all persistence remote-only and preserve current API payloads.

**Tech Stack:** Vue 3 Composition API, TypeScript, Vitest, existing `AsyncButton` and shared CSS tokens.

## Global Constraints

- No new dependency, backend endpoint, or local-storage draft.
- Cover company, role, city, status, source, dates, notes, contacts, attachment, draft id, timeline fields, and reminder time.
- Preserve existing `pendingKey`/`loading` request locks and `resolveApplicationsCloseAction` keyboard semantics.
- Confirmation UI must use `role="alert"`, `aria-live="polite"`, existing button components with at least 44px height, and responsive wrapping.
- Register `beforeunload` only while dirty and always remove it on unmount.

---

### Task 1: Form Snapshot Dirty-State Helper

**Files:**
- Create: `web-frontend/src/lib/application-form-state.ts`
- Test: `web-frontend/src/tests/application-form-state.spec.ts`

**Interfaces:**
- Produces `ApplicationFormSnapshot`, `createApplicationFormSnapshot`, and `isApplicationFormDirty` for `ApplicationsView.vue`.
- `ApplicationFormSnapshot` must contain plain string values for the main form, timeline form, and reminder time so Vue refs are never retained by the baseline.

- [ ] **Step 1: Write the failing tests**

Add tests that assert an identical snapshot is clean, changing a main field is dirty, changing a timeline field is dirty, changing `reminderAt` is dirty, and a later mutation of the source objects does not mutate an already-created baseline.

- [ ] **Step 2: Run the focused test and verify RED**

Run `npm.cmd run test -- --run src/tests/application-form-state.spec.ts` from `web-frontend`. It must fail because the helper module does not exist.

- [ ] **Step 3: Implement the minimal helper**

Export typed plain-object inputs and implement `createApplicationFormSnapshot` with object spreads for each layer. Implement `isApplicationFormDirty(current, baseline)` using stable JSON serialization of the fixed property order; return `false` when snapshots are equal.

- [ ] **Step 4: Run the focused test and verify GREEN**

Run the same command and confirm all helper tests pass with no warnings.

- [ ] **Step 5: Commit**

Run `git add -- web-frontend/src/lib/application-form-state.ts web-frontend/src/tests/application-form-state.spec.ts` then `git commit -m "feat(web): add application form dirty state helper"`.

### Task 2: Protect Application Tracker Edits

**Files:**
- Modify: `web-frontend/src/views/ApplicationsView.vue`
- Modify: `web-frontend/src/styles/base.css`
- Modify: `web-frontend/src/tests/interaction.spec.ts`
- Modify: `web-frontend/src/tests/keyboard-shortcuts.spec.ts` only if a new pure shortcut assertion is needed

**Interfaces:**
- Consumes the Task 1 snapshot helper.
- Keeps the current `cancelEditing(): void`, `startEdit(item)`, `submit()`, `addEvent(item)`, `setReminder(item)`, and `handleShortcut(event)` entry points.

- [ ] **Step 1: Write failing source-contract tests**

Extend `interaction.spec.ts` with one test that reads `ApplicationsView.vue` and requires the helper import, `isDirty`, conditional `beforeunload` add/remove calls, `showLeaveConfirmation`, `continueEditing`, `discardChanges`, and an inline `role="alert"` confirmation. Require `base.css` to contain an `.application-leave-confirmation` rule and a mobile wrapping rule.

- [ ] **Step 2: Run the focused tests and verify RED**

Run `npm.cmd run test -- --run src/tests/interaction.spec.ts` from `web-frontend`. The new assertions must fail against the current view and stylesheet.

- [ ] **Step 3: Wire baseline and dirty state**

Import the helper. Keep a `formBaseline` ref initialized from the empty main form and a `followupBaseline` ref initialized from empty timeline/reminder values. Expose `isDirty` as a computed comparison of the current three layers. Update baselines when starting an edit, opening a timeline, after successful save/add-event/save-reminder, and after explicit discard. Ensure reset operations clear the confirmation state. A main-form save must preserve dirty follow-up values instead of silently resetting them.

- [ ] **Step 4: Add guarded cancellation and browser protection**

Change `cancelEditing` to keep the current form when dirty and set `showLeaveConfirmation`; retain the existing `runPendingGuardedAction` behavior for pending requests. Add `continueEditing` and `discardChanges` actions. Register `handleBeforeUnload` through a `watch(isDirty, ...)` and remove both keyboard and unload listeners in `onBeforeUnmount`.

- [ ] **Step 5: Render the confirmation and style it**

Place the inline confirmation immediately below the application form actions. Use `role="alert"`, `aria-live="polite"`, concise Chinese copy, and `AsyncButton` actions for continue/discard. Add `.application-leave-confirmation` styles using existing tokens, with a minimum 44px action height; at the mobile breakpoint make its action group wrap without overflow. Block `remove(item)` while any form layer is dirty, showing the same inline confirmation; on a clean successful delete, clear follow-up refs/baseline along with `expandedId`. Snapshot serialization must use an explicit field order so equivalent objects with reordered keys compare cleanly.

- [ ] **Step 6: Run focused tests and verify GREEN**

Run `npm.cmd run test -- --run src/tests/application-form-state.spec.ts src/tests/interaction.spec.ts src/tests/keyboard-shortcuts.spec.ts` from `web-frontend` and confirm all pass.

- [ ] **Step 7: Commit**

Run `git add -- web-frontend/src/views/ApplicationsView.vue web-frontend/src/styles/base.css web-frontend/src/tests/interaction.spec.ts web-frontend/src/tests/keyboard-shortcuts.spec.ts` then `git commit -m "feat(web): protect unsaved application edits"`.

### Task 3: Full Verification

**Files:**
- No source changes expected.

- [ ] **Step 1: Run the complete web test suite**

Run `npm.cmd run test -- --run` from `web-frontend` and record the complete passing count.

- [ ] **Step 2: Run the production build**

Run `npm.cmd run build` from `web-frontend` and confirm Vite exits with code 0.

- [ ] **Step 3: Run diff and visual mechanical checks**

Run `git diff --check 8e5a676..HEAD` and `node "C:\Users\16102\.codex\skills\impeccable\scripts\detect.mjs" --json web-frontend/src/views/ApplicationsView.vue web-frontend/src/styles/base.css`; resolve any new findings before completion.

- [ ] **Step 4: Commit verification notes only if needed**

Do not create a source commit for clean verification. If a test or detector requires a fix, return to Task 2 and commit the smallest correction with a focused message.
