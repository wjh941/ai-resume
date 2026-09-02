# SPA Navigation Leave Guard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prevent SPA sidebar and internal view navigation from unmounting dirty application forms without confirmation.

**Architecture:** Add a tiny Vue injection context that stores the active view's synchronous `canLeave` guard. `App.vue` owns navigation decisions and the latest blocked destination; `ApplicationsView.vue` registers its existing dirty-state check and emits a resolution event after discard so the parent can continue the pending navigation.

**Tech Stack:** Vue 3 Composition API, TypeScript, Vitest, existing `AsyncButton` and workspace navigation components.

## Global Constraints

- No router, event bus, backend endpoint, local storage, or new dependency.
- Preserve `WebSidebar` events, `aria-current`, drawer closing, and existing child `navigate` events.
- Ignore repeated navigation to the active view; clean views navigate immediately.
- Dirty application navigation keeps the current view mounted, records only the latest target, and reuses the existing inline confirmation.
- `ApplicationsView` unregisters its guard on unmount; no guard may leak into later views.

---

### Task 1: Navigation Guard Context

**Files:**
- Create: `web-frontend/src/lib/navigation-guard.ts`
- Create: `web-frontend/src/tests/navigation-guard.spec.ts`

**Interfaces:**

```ts
export type NavigationGuard = () => boolean

export interface NavigationGuardContext {
  register: (guard: NavigationGuard) => () => void
  canNavigate: () => boolean
}

export const NAVIGATION_GUARD_KEY: InjectionKey<NavigationGuardContext>
export function createNavigationGuardContext(): NavigationGuardContext
```

- [ ] **Step 1: Write failing unit tests**

Test that no registered guard allows navigation, a guard returning `false` blocks it, a guard returning `true` allows it, unregister restores the clean default, and registering a replacement makes only the latest guard active.

- [ ] **Step 2: Run RED**

From `web-frontend`, run `npm.cmd run test -- --run src/tests/navigation-guard.spec.ts`. It must fail because the module is missing.

- [ ] **Step 3: Implement the minimal context**

Store one nullable guard in a closure. `register` replaces the active guard and returns an idempotent unregister function that clears only its own guard. `canNavigate` returns `activeGuard ? activeGuard() : true`.

- [ ] **Step 4: Run GREEN**

Run the same focused command and confirm all context tests pass.

- [ ] **Step 5: Commit**

Commit with `git commit -m "feat(web): add SPA navigation guard context"`.

### Task 2: Coordinate Dirty Application Navigation

**Files:**
- Modify: `web-frontend/src/App.vue`
- Modify: `web-frontend/src/views/ApplicationsView.vue`
- Modify: `web-frontend/src/tests/interaction.spec.ts`

**Interfaces:**
- Consumes `NAVIGATION_GUARD_KEY` and `createNavigationGuardContext` from Task 1.
- `ApplicationsView` emits `navigation-ready` after `discardChanges()`.
- `App.vue` keeps `navigateTo(view: WorkspaceView)` and `resumePendingNavigation()` private handlers.

- [ ] **Step 1: Write failing source-contract tests**

Extend `interaction.spec.ts` with assertions that `App.vue` provides the guard context, routes both sidebar and dynamic-view navigation through `navigateTo`, stores a pending target, and listens for `navigation-ready`. Require `ApplicationsView.vue` to inject the context, register/unregister a guard, expose `canLeaveForNavigation`, and emit `navigation-ready` from discard. Require the existing confirmation markup to remain present.

- [ ] **Step 2: Run RED**

Run `npm.cmd run test -- --run src/tests/interaction.spec.ts`. The new contracts must fail before production edits.

- [ ] **Step 3: Implement parent navigation coordination**

In `App.vue`, create/provide the context, add `pendingNavigation = ref<WorkspaceView | null>(null)`, and route both `<WebSidebar @navigate>` and dynamic-view `@navigate` through `navigateTo`. The handler ignores the active view, calls `navigationContext.canNavigate()`, records a blocked target when false, and assigns `activeView` only when allowed. `resumePendingNavigation()` consumes the latest target once.

- [ ] **Step 4: Register the application guard**

In `ApplicationsView.vue`, inject the context optionally, register `canLeaveForNavigation` on mount, and unregister it on unmount alongside existing listeners. The guard returns `true` when clean; when dirty it sets `showLeaveConfirmation` and returns `false`. `discardChanges()` keeps its current reset behavior and emits `navigation-ready` after clearing state.

- [ ] **Step 5: Run focused GREEN tests**

Run `npm.cmd run test -- --run src/tests/navigation-guard.spec.ts src/tests/interaction.spec.ts src/tests/keyboard-shortcuts.spec.ts` and confirm all pass.

- [ ] **Step 6: Commit**

Commit with `git commit -m "feat(web): protect SPA navigation from dirty applications"`.

### Task 3: Full Verification

**Files:**
- No source changes expected.

- [ ] **Step 1: Run complete Web tests**

Run `npm.cmd run test -- --run` from `web-frontend`; record the passing file/test counts.

- [ ] **Step 2: Run production build**

Run `npm.cmd run build` and confirm Vite exits with code 0.

- [ ] **Step 3: Run quality checks**

Run `git diff --check <iteration-base>..HEAD` and `node "C:\Users\16102\.codex\skills\impeccable\scripts\detect.mjs" --json web-frontend/src/App.vue web-frontend/src/views/ApplicationsView.vue`; resolve any new findings.
