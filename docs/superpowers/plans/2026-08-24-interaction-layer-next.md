# Front-end Interaction Layer Next Iteration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task with checkpoints.

**Goal:** Upgrade loading, transition, and selective micro-interaction feedback in both frontends while preserving all H5 business behavior and all delivered Web business modules/API contracts.

**Architecture:** Keep each app's existing native Vue/CSS primitives and normalize their semantic token names at the application root. Web continues using `AsyncButton`, `LoadingSpinner`, `useAsyncAction`, and the keyed `App` transition; H5 continues using `LoadingSpinner`, `runWithLoading`, and page-scoped transition classes. New code is limited to interaction helpers, CSS, and existing view wiring.

**Tech Stack:** Vue 3, uni-app Vue 3, TypeScript, native CSS transitions/keyframes, Vitest, Vite/uni build.

## Global Constraints

- `resume-miniprogram` receives no new pages, modules, API endpoints, mock data, copy, or business capabilities.
- Existing Web experience-evidence, career-assessment, role-comparison, membership, and order modules stay fully intact; no adapter, payload, route, or business workflow changes.
- Use native CSS transform/opacity/background transitions only; do not add animation dependencies.
- Every async action clears pending state in `finally`, including rejection and abort; pending controls disable duplicate clicks.
- Keep Chinese UI text and mock data unchanged; centralize motion/loading tokens and preserve reduced-motion behavior.

---

### Task 1: Lock the shared interaction contract with focused tests

**Files:**
- Modify: `web-frontend/src/tests/interaction.spec.ts`
- Modify: `resume-miniprogram/src/tests/interaction.spec.ts`
- Modify: `resume-miniprogram/src/utils/async-state.ts`
- Create: `web-frontend/src/lib/interaction-state.ts`
- Create: `web-frontend/src/tests/interaction-state.spec.ts`

**Interfaces:**
- `runWithLoading(setLoading, operation)` continues returning the operation result or rethrowing the original error.
- `interaction-state.ts` exports pure `pendingLabel(loading: boolean, idle: string, active: string): string` and `canStartInteraction(loading: boolean): boolean` helpers for Web controls that cannot mount component tests.

- [ ] **Step 1: Write failing tests**

```ts
it("rejects a duplicate interaction while loading", () => {
  expect(canStartInteraction(true)).toBe(false)
  expect(pendingLabel(true, "保存", "保存中")).toBe("保存中")
})
```

Add an H5 test where an abort-shaped error rejects and `runWithLoading` records `[true, false]`.

- [ ] **Step 2: Run focused tests and confirm failure**

Run `npm.cmd run test -- src/tests/interaction-state.spec.ts` in `web-frontend`.
Expected: FAIL because the Web helper does not exist yet.

- [ ] **Step 3: Implement the minimal helpers and preserve H5 semantics**

Implement the two Web pure helpers. Keep `runWithLoading`'s `finally` cleanup and only add a comment if needed to clarify abort/rejection preservation; do not swallow errors.

- [ ] **Step 4: Run focused tests**

Run `npm.cmd run test -- src/tests/interaction-state.spec.ts src/tests/interaction.spec.ts` in `web-frontend` and `npm.cmd run test:unit -- src/tests/interaction.spec.ts` in `resume-miniprogram`.
Expected: all focused tests pass.

- [ ] **Step 5: Commit**

```bash
git add web-frontend/src/lib/interaction-state.ts web-frontend/src/tests/interaction-state.spec.ts web-frontend/src/tests/interaction.spec.ts resume-miniprogram/src/utils/async-state.ts resume-miniprogram/src/tests/interaction.spec.ts
git commit -m "test: lock interaction pending cleanup contract"
```

### Task 2: Strengthen Web shared loading and transition feedback

**Files:**
- Modify: `web-frontend/src/components/AsyncButton.vue`
- Modify: `web-frontend/src/App.vue`
- Modify: `web-frontend/src/styles/base.css`
- Modify: `web-frontend/src/tests/interaction.spec.ts`
- Create: `web-frontend/src/components/FutureCapabilityShell.vue`

**Interfaces:**
- `AsyncButton` keeps the existing `loading`, `disabled`, and `type` props and continues forwarding attributes/events.
- `FutureCapabilityShell` is a neutral presentational component with props `{ title: string; description: string }` and no API calls; it is optional infrastructure for future Web-only capabilities and must not replace delivered modules.

- [ ] **Step 1: Add the failing contract test**

Extend interaction tests to assert the pure loading helper behavior used by `AsyncButton` and add a static contract check that the future shell has no request imports.

- [ ] **Step 2: Implement the Web shared layer**

Add centralized variables for ripple duration, press scale, transition distance, and loading block minimum height. Keep spinner geometry stable. Add a restrained pseudo-element ripple only to `.primary-button`/explicit primary actions, preserve the existing press transform, and ensure disabled/loading buttons do not animate or accept clicks.

Keep the keyed `Transition name="view-swap" mode="out-in"` in `App.vue`; add `aria-live="polite"` only to non-blocking status surfaces and keep `.view-transition-shell` min-height stable. Do not change active view keys or business events.

Implement `FutureCapabilityShell.vue` as a slot-friendly visual shell only; do not mount it over evidence, assessment, comparison, membership, order, or any existing functional view.

- [ ] **Step 3: Verify Web interaction behavior**

Run `npm.cmd run test -- src/tests/interaction.spec.ts src/tests/interaction-state.spec.ts` and `npm.cmd run build` in `web-frontend`.
Expected: PASS with unchanged API adapter tests.

- [ ] **Step 4: Commit**

```bash
git add web-frontend/src/components/AsyncButton.vue web-frontend/src/components/FutureCapabilityShell.vue web-frontend/src/App.vue web-frontend/src/styles/base.css web-frontend/src/tests/interaction.spec.ts
git commit -m "feat(web): strengthen shared interaction feedback"
```

### Task 3: Apply selective Web interactions to delivered views

**Files:**
- Modify: `web-frontend/src/views/OverviewView.vue`
- Modify: `web-frontend/src/views/ResumeView.vue`
- Modify: `web-frontend/src/views/ResumeEditorView.vue`
- Modify: `web-frontend/src/views/CareerView.vue`
- Modify: `web-frontend/src/views/JobsView.vue`
- Modify: `web-frontend/src/views/ApplicationsView.vue`
- Modify: `web-frontend/src/views/EvidenceView.vue`
- Modify: `web-frontend/src/views/MembershipView.vue`
- Modify: `web-frontend/src/views/AssessmentView.vue`
- Modify: `web-frontend/src/views/ComparisonView.vue`
- Modify: `web-frontend/src/views/InsightsView.vue`
- Modify: `web-frontend/src/views/AccountView.vue`
- Modify: `web-frontend/src/components/WebSidebar.vue`
- Modify: `web-frontend/src/components/WebTopbar.vue`
- Modify: `web-frontend/src/styles/base.css`

**Interfaces:**
- Existing API adapter calls, request bodies, emitted navigation events, and business data remain byte-for-byte compatible unless a template-only loading/ARIA attribute is required.
- Existing `AsyncButton` pending props remain the only source of button disabled/loading state.

- [ ] **Step 1: Audit high-frequency controls**

List every async trigger and mode/filter switch in the files above. For each, verify `:loading` or `useAsyncAction` cleanup, retry/error rendering, and stable skeleton presence before editing. Do not add animation to read-only text or every list item.

- [ ] **Step 2: Apply interaction classes by scenario**

Use primary ripple/press treatment on submit/save/query/pay actions, elastic active-state treatment on mode/filter switches, and a small success check only on existing success notices. Keep row hover/press transform limited to actionable rows. Do not add particle burst, card flip, swipe-away, or bottom-sheet behavior.

- [ ] **Step 3: Verify delivered business workflows remain intact**

Run the existing Web suite and build. Inspect `git diff -- web-frontend/src/lib web-frontend/src/views` to ensure no API adapter or business payload changes occurred.

- [ ] **Step 4: Commit**

```bash
git add web-frontend/src/views web-frontend/src/components/WebSidebar.vue web-frontend/src/components/WebTopbar.vue web-frontend/src/styles/base.css
git commit -m "feat(web): apply selective interaction feedback"
```

### Task 4: Audit H5 existing pages without changing business scope

**Files:**
- Modify: `resume-miniprogram/src/App.vue`
- Modify: existing H5 page files only where an async handler lacks `finally` cleanup or a loading block lacks `LoadingSpinner` (no new page files)
- Modify: `resume-miniprogram/src/utils/async-state.ts`
- Modify: `resume-miniprogram/src/tests/interaction.spec.ts`

**Interfaces:**
- Existing service/store calls, page routes, page component structure, and Chinese copy remain unchanged.
- `LoadingSpinner` remains the only shared H5 spinner component; `runWithLoading` remains the wrapper for pending cleanup.

- [ ] **Step 1: Add regression tests for abort/rejection cleanup**

Extend `resume-miniprogram/src/tests/interaction.spec.ts` with an abort-shaped rejection and assert the loading sequence always ends in `false`.

- [ ] **Step 2: Normalize H5 root tokens and transitions**

Add semantic aliases for motion/loading variables alongside existing `--ui-*` variables so current selectors keep working. Keep `.page` enter animation, skeleton opacity/transform transitions, button press, and reduced-motion behavior native CSS-only. Do not change page routes or add a global navigation guard.

- [ ] **Step 3: Fix only verified loading gaps**

For each existing page found by the audit, wrap the current request in `runWithLoading` or add the existing `LoadingSpinner` to its current loading block. Ensure button `:loading` and `:disabled` are both driven by the existing pending ref. Preserve catches and displayed Chinese error text.

- [ ] **Step 4: Run H5 focused tests/build**

Run `npm.cmd run test:unit -- src/tests/interaction.spec.ts` and `npm.cmd run build:h5` in `resume-miniprogram`.
Expected: PASS; no new H5 page/module paths.

- [ ] **Step 5: Commit**

```bash
git add resume-miniprogram/src/App.vue resume-miniprogram/src/utils/async-state.ts resume-miniprogram/src/tests/interaction.spec.ts resume-miniprogram/src/pages
git commit -m "fix(h5): harden existing loading and transitions"
```

### Task 5: Changelog and full regression verification

**Files:**
- Modify: `docs/interaction-upgrade-changelog.md`
- Test: `web-frontend/src/tests/*.spec.ts`
- Test: `resume-miniprogram/src/tests/*.spec.ts`

- [ ] **Step 1: Update the changelog**

Record exact Web components/views and H5 existing pages changed, interaction choices, loading cleanup behavior, and deliberately skipped interaction types. State that delivered Web business modules/API logic were preserved and H5 received no new business files.

- [ ] **Step 2: Run all verification commands**

Run:

```bash
cd web-frontend; npm.cmd run test; npm.cmd run build
cd ../resume-miniprogram; npm.cmd run test:unit; npm.cmd run build:h5
cd ..; git diff --check; git status --short
```

Expected: all tests/builds pass, no diff-check errors, and only intentional commits/files are present.

- [ ] **Step 3: Run the UI detector**

Run `node C:\Users\16102\.codex\skills\impeccable\scripts\detect.mjs --json web-frontend/src/App.vue web-frontend/src/components web-frontend/src/views web-frontend/src/styles/base.css` once after UI edits. Verify any finding before final handoff.

- [ ] **Step 4: Commit documentation**

```bash
git add docs/interaction-upgrade-changelog.md
git commit -m "docs: record interaction layer next iteration"
```
