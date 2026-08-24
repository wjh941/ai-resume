# Frontend Interaction Upgrade Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a reusable, CSS-only loading and motion foundation to the independent Web frontend and existing Uni-App H5 pages without changing business modules, APIs, page structure, Chinese copy, mock data, or request behavior.

**Architecture:** Each frontend gets a platform-native `LoadingSpinner` and keeps its current CSS token system. The Web app also gets an `AsyncButton`, `AnimatedNumber`, and a tested `useAsyncAction` helper; dynamic views use a keyed Vue transition. H5 keeps native Uni-App button loading where already present, adds the spinner to existing high-frequency loading blocks, and uses global page/button motion classes. Existing request handlers remain the source of business state and always clear pending flags in `finally`.

**Tech Stack:** Vue 3, TypeScript, Vite, Vitest, Uni-App, CSS custom properties, native CSS transitions/keyframes, existing `lucide-vue-next` icons.

## Global Constraints

- `resume-miniprogram` H5: modify existing pages only; do not add experience-evidence, career-assessment, job-comparison, membership, or order business modules.
- `web-frontend`: add interaction primitives only; reserve reusable foundation for future modules without implementing those modules.
- Keep every existing API URL, HTTP method, payload, response shape, page route, Chinese string, and mock data unchanged.
- Do not add animation or UI libraries; use existing CSS architecture and native transforms/transitions.
- Every new pending state must be cleared on resolve, reject, or cancel through `finally`.
- Preserve stable dimensions for buttons, skeleton blocks, metrics, and transition containers to prevent layout jitter.
- Respect `prefers-reduced-motion` with static or opacity-only alternatives.
- Run existing unit tests and production builds for both frontends before claiming completion.

---

### Task 1: Web async state and loading primitives

**Files:**
- Create: `web-frontend/src/composables/useAsyncAction.ts`
- Create: `web-frontend/src/components/LoadingSpinner.vue`
- Create: `web-frontend/src/components/AsyncButton.vue`
- Create: `web-frontend/src/components/AnimatedNumber.vue`
- Create: `web-frontend/src/tests/interaction.spec.ts`

**Interfaces:**
- `useAsyncAction().pending: Ref<boolean>` and `useAsyncAction().run<T>(operation: () => Promise<T>): Promise<T | undefined>`.
- `LoadingSpinner` props: `size?: "sm" | "md" | "lg"`, `label?: string`.
- `AsyncButton` props: `loading?: boolean`, `disabled?: boolean`, `type?: "button" | "submit" | "reset"`; all normal button attributes and slots remain supported.
- `AnimatedNumber` prop: `value: number | string`.

- [ ] **Step 1: Write failing async-state tests**

```ts
import { describe, expect, it } from "vitest"

import { useAsyncAction } from "../composables/useAsyncAction"

describe("useAsyncAction", () => {
  it("clears pending after a successful operation", async () => {
    const action = useAsyncAction()
    const result = await action.run(async () => "saved")

    expect(result).toBe("saved")
    expect(action.pending.value).toBe(false)
  })

  it("clears pending and rethrows after a failed operation", async () => {
    const action = useAsyncAction()
    const failure = Promise.resolve().then(() => action.run(async () => { throw new Error("network") }))

    await expect(failure).rejects.toThrow("network")
    expect(action.pending.value).toBe(false)
  })

  it("ignores a duplicate operation while pending", async () => {
    const action = useAsyncAction()
    let resolve!: (value: string) => void
    const first = action.run(() => new Promise<string>((done) => { resolve = done }))
    const second = await action.run(async () => "duplicate")

    expect(second).toBeUndefined()
    resolve("first")
    await expect(first).resolves.toBe("first")
  })
})
```

- [ ] **Step 2: Run the focused test and verify it fails because the helper does not exist**

Run: `npm.cmd run test -- src/tests/interaction.spec.ts`

Expected: FAIL with a module-not-found error for `../composables/useAsyncAction`.

- [ ] **Step 3: Implement the minimal helper**

```ts
import { ref } from "vue"

export function useAsyncAction() {
  const pending = ref(false)

  async function run<T>(operation: () => Promise<T>): Promise<T | undefined> {
    if (pending.value) return undefined
    pending.value = true
    try {
      return await operation()
    } finally {
      pending.value = false
    }
  }

  return { pending, run }
}
```

- [ ] **Step 4: Run the focused test and verify it passes**

Run: `npm.cmd run test -- src/tests/interaction.spec.ts`

Expected: 3 tests pass.

- [ ] **Step 5: Add CSS-only presentation primitives**

`LoadingSpinner.vue` keeps a fixed inline box for stable button width and renders three spans for the ring. `AsyncButton.vue` always reserves a spinner slot, sets `disabled` to `disabled || loading`, and exposes `aria-busy` while retaining the original slot label. `AnimatedNumber.vue` renders the value with a keyed span so CSS can animate only the changed number.

- [ ] **Step 6: Run Web tests again**

Run: `npm.cmd run test`

Expected: existing tests plus `interaction.spec.ts` pass.

- [ ] **Step 7: Commit the Web primitives**

```bash
git add web-frontend/src/composables/useAsyncAction.ts web-frontend/src/components/LoadingSpinner.vue web-frontend/src/components/AsyncButton.vue web-frontend/src/components/AnimatedNumber.vue web-frontend/src/tests/interaction.spec.ts
git commit -m "feat(web): add interaction loading primitives"
```

### Task 2: Web shell transition and motion tokens

**Files:**
- Modify: `web-frontend/src/App.vue`
- Modify: `web-frontend/src/styles/base.css`

**Interfaces:**
- Consumes: existing `activeView`, `activeComponent`, `dark`, and session state.
- Produces: keyed `view-swap` transition with stable stage dimensions and shared Web motion/loading variables.

- [ ] **Step 1: Add a keyed transition around the existing dynamic view**

```vue
<Transition name="view-swap" mode="out-in">
  <div :key="activeView" class="view-transition-shell">
    <component :is="activeComponent" @navigate="activeView = $event" />
  </div>
</Transition>
```

Keep the existing `workspace-stage` section and all component inputs/events unchanged. Add `LoadingSpinner` only to the transition status overlay if a transition status element is needed; do not change the active view assignment.

- [ ] **Step 2: Add tokenized motion and loading CSS**

Add `--motion-fast`, `--motion-base`, `--motion-ease`, `--progress`, `--spinner-track`, and `--spinner-size-*` to both light and dark root tokens. Add `.view-transition-shell`, `.view-swap-enter-*`, `.view-swap-leave-*`, `.async-button-*`, `.loading-spinner-*`, and `.animated-number` rules using `transform` and `opacity` only for motion.

- [ ] **Step 3: Preserve stable layout and reduced-motion behavior**

Keep `.workspace-stage` min-height and existing skeleton min-heights. Under `prefers-reduced-motion: reduce`, set view transforms and skeleton shimmer to none, keep opacity transitions short or static, and do not use a global `transition: all` rule.

- [ ] **Step 4: Run build and tests**

Run: `npm.cmd run test; npm.cmd run build`

Expected: all tests pass and Vite emits a production bundle.

### Task 3: Web view async controls and feedback

**Files:**
- Modify: `web-frontend/src/components/LoginPanel.vue`
- Modify: `web-frontend/src/components/WebTopbar.vue`
- Modify: `web-frontend/src/views/OverviewView.vue`
- Modify: `web-frontend/src/views/ResumeView.vue`
- Modify: `web-frontend/src/views/CareerView.vue`
- Modify: `web-frontend/src/views/JobsView.vue`
- Modify: `web-frontend/src/views/ApplicationsView.vue`
- Modify: `web-frontend/src/views/InsightsView.vue`
- Modify: `web-frontend/src/views/AccountView.vue`

**Interfaces:**
- Consumes: existing request functions, refs, emits, labels, and response types.
- Produces: button-level spinner/disabled states, stable skeleton blocks, success checkmark styling, and no changed API behavior.

- [ ] **Step 1: Replace only existing async action buttons with `AsyncButton`**

Use existing state names wherever possible: `loading`, `sending`, `saving`, and a narrowly scoped `pendingAction` for account actions/logout. Keep each original Chinese slot label exactly unchanged, for example:

```vue
<AsyncButton class="primary-button compact" type="submit" :loading="saving">
  <Plus :size="17" aria-hidden="true" />{{ saving ? "保存中" : "新增记录" }}
</AsyncButton>
```

- [ ] **Step 2: Route every new pending flag through `finally`**

For account actions and logout, set the action key before the existing request and clear it in `finally`. For existing `loading`/`saving` functions, retain their current `try/catch/finally` structure and only bind the state to `AsyncButton`.

- [ ] **Step 3: Add loading spinner to existing skeleton blocks**

Place a centered `LoadingSpinner` inside the existing overview, list, and result skeleton containers. Keep all existing skeleton spans and min-heights so content does not resize while loading.

- [ ] **Step 4: Add `AnimatedNumber` only to overview metrics**

Replace only the three metric value interpolations with `AnimatedNumber :value="..."`; keep the fallback `"-"`, labels, counts, and data source unchanged.

- [ ] **Step 5: Add success checkmark styling without changing copy**

Use the existing `.notice-success` nodes in Account and any existing success notice nodes. Add a pseudo-element or a reusable class that draws a checkmark with `stroke-dasharray`; do not add or rewrite user-facing text.

- [ ] **Step 6: Run Web tests and build**

Run: `npm.cmd run test; npm.cmd run build`

Expected: all tests and production build pass.

### Task 4: H5 loading component and global interaction foundation

**Files:**
- Create: `resume-miniprogram/src/components/LoadingSpinner.vue`
- Create: `resume-miniprogram/src/utils/async-state.ts`
- Modify: `resume-miniprogram/src/App.vue`
- Create: `resume-miniprogram/src/tests/interaction.spec.ts`

**Interfaces:**
- `LoadingSpinner` props: `size?: "sm" | "md" | "lg"`, `label?: string`.
- `runWithLoading<T>(setLoading: (loading: boolean) => void, operation: () => Promise<T>): Promise<T>`.
- Consumes: existing H5 global variables and native button loading props.
- Produces: Uni-App-compatible block spinner and global page/button motion tokens.

- [ ] **Step 1: Write failing loading-state cleanup tests**

```ts
import { describe, expect, it } from "vitest"

import { runWithLoading } from "../utils/async-state"

describe("runWithLoading", () => {
  it("clears loading after resolve", async () => {
    const states: boolean[] = []
    await expect(runWithLoading((value) => states.push(value), async () => "ok")).resolves.toBe("ok")
    expect(states).toEqual([true, false])
  })

  it("clears loading after rejection", async () => {
    const states: boolean[] = []
    await expect(runWithLoading((value) => states.push(value), async () => { throw new Error("offline") }))
      .rejects.toThrow("offline")
    expect(states).toEqual([true, false])
  })
})
```

- [ ] **Step 2: Run the focused test and verify it fails because the helper does not exist**

Run: `npm.cmd run test:unit -- src/tests/interaction.spec.ts`

Expected: FAIL with a module-not-found error for `../utils/async-state`.

- [ ] **Step 3: Implement the minimal helper and spinner**

```ts
export async function runWithLoading<T>(
  setLoading: (loading: boolean) => void,
  operation: () => Promise<T>,
): Promise<T> {
  setLoading(true)
  try {
    return await operation()
  } finally {
    setLoading(false)
  }
}
```

`LoadingSpinner.vue` uses `view` elements and CSS variables only. Its root has a stable square size, exposes a readable label for H5, and avoids browser-only APIs. Use the same conceptual size names and animation timing as Web.

- [ ] **Step 4: Run the focused H5 test and verify it passes**

Run: `npm.cmd run test:unit -- src/tests/interaction.spec.ts`

Expected: 2 tests pass.

- [ ] **Step 5: Extend `App.vue` global styles**

Add `--ui-motion-slow`, `--ui-spinner-size-*`, `--ui-spinner-track`, and `--ui-motion-reduced`. Add stable `.ui-loading-spinner`, `.ui-page-enter`, `.ui-pressable`, and skeleton settle rules. Apply the page entry animation to the existing `.page` roots only; do not change route definitions.

- [ ] **Step 6: Add reduced-motion and H5 touch feedback fallbacks**

Keep the existing `button:active` behavior, add a restrained overshoot on high-frequency primary buttons, and disable transforms/keyframes under `prefers-reduced-motion: reduce`.

- [ ] **Step 7: Run H5 unit tests**

Run: `npm.cmd run test:unit`

Expected: all existing H5 tests pass.

### Task 5: H5 high-frequency pages and selected advanced interactions

**Files:**
- Modify: `resume-miniprogram/src/pages/login/index.vue`
- Modify: `resume-miniprogram/src/pages/account/index.vue`
- Modify: `resume-miniprogram/src/pages/job-collection/index.vue`
- Modify: `resume-miniprogram/src/pages/career-planner/index.vue`
- Modify: `resume-miniprogram/src/pages/resume-editor/index.vue`
- Modify: `resume-miniprogram/src/pages/applications/index.vue`
- Modify: `resume-miniprogram/src/pages/drafts/index.vue`
- Modify: `resume-miniprogram/src/pages/role-comparison/index.vue`
- Modify: `resume-miniprogram/src/utils/async-state.ts`

**Interfaces:**
- Consumes: existing page refs, API calls, native `:loading` bindings, and route handlers.
- Produces: visible block spinners, stable skeleton/loading transitions, press feedback, elastic switch feedback, and a restrained comparison-card depth/flip-like interaction without changing card content or actions.

- [ ] **Step 1: Add `LoadingSpinner` to existing high-frequency loading blocks**

Keep each page’s existing loading text and skeleton markup. Add the spinner beside or above it, preserving the current `v-if` conditions and API calls.

- [ ] **Step 2: Bind missing async buttons to existing pending refs**

Where an existing async function has a loading/saving ref but its button lacks `:loading` or `:disabled`, add those bindings. Do not introduce new API calls or change labels.

- [ ] **Step 3: Verify loading cleanup in each touched async function**

Wrap touched high-frequency request bodies with `runWithLoading` where a page currently duplicates loading assignment, or keep the existing equivalent `try/finally` when the page has multiple independent flags. In both cases, preserve the existing error and toast behavior and ensure the flag resets on rejection.

- [ ] **Step 4: Add selected H5 motion**

Use the existing job-collection `<switch>` class for a small elastic scale transition. Add a subtle press-depth/flip-like transform to `.comparison-card` on active/focus states rather than changing its content model. Keep the existing comparison reveal animation and disable both under reduced motion.

- [ ] **Step 5: Keep skeleton dimensions fixed**

Give existing career-planner and resume-editor skeleton containers explicit min-heights matching their loaded blocks, and animate opacity/transform only. Do not replace the current skeleton copy or data.

- [ ] **Step 6: Run H5 unit tests and H5 build**

Run: `npm.cmd run test:unit; npm.cmd run build:h5`

Expected: all tests pass and the H5 bundle builds successfully.

### Task 6: Changelog and verification pass

**Files:**
- Create: `docs/interaction-upgrade-changelog.md`

**Interfaces:**
- Documents the exact components/pages changed, selected interactions, skipped interactions, loading cleanup guarantees, and verification commands.

- [ ] **Step 1: Record the Web and H5 scope split**

Document that Web receives reusable interaction primitives while H5 only enhances existing pages and adds no business modules.

- [ ] **Step 2: Record selected and skipped interactions**

List press-bounce, unified spinner, page/block transition, skeleton settle, Web metric transition, success checkmark, H5 switch elasticity, and comparison-card depth/flip-like feedback. Explicitly list particle burst, liquid slider, hamburger morph, swipe-away deletion, and bottom sheet as skipped.

- [ ] **Step 3: Record loading/error guarantees**

State that buttons disable while pending, all touched async handlers clear state in `finally`, and existing errors/API behavior are preserved.

- [ ] **Step 4: Run final verification**

Run:

```bash
cd web-frontend
npm.cmd run test
npm.cmd run build
cd ..\resume-miniprogram
npm.cmd run test:unit
npm.cmd run build:h5
cd ..
node C:\Users\16102\.codex\skills\impeccable\scripts\detect.mjs --json web-frontend/src
git diff --check
git status --short
```

Expected: every command exits successfully, the detector returns no blocking findings, and the status lists only the intended implementation and documentation files.

- [ ] **Step 5: Commit the changelog and final implementation**

```bash
git add web-frontend resume-miniprogram/src docs/interaction-upgrade-changelog.md
git commit -m "feat: upgrade web and h5 interactions"
```
