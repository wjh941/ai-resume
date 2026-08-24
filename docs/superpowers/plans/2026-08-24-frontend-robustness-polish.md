# Frontend Robustness Polish Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Finish the approved robustness polish for H5 and Web without changing business logic, API contracts, routes, mock data, or Chinese UI copy.

**Architecture:** Keep all behavior at existing call sites and add only presentation primitives: one H5 toast wrapper, centralized CSS contracts, the existing Web `ErrorNotice`, and CSS containment for long lists. Native CSS and current Vue/uni-app patterns are sufficient; no animation or virtualization dependency is introduced.

**Tech Stack:** Vue 3, uni-app H5, Vite 5, Vitest 2, Tailwind-compatible project CSS tokens, native CSS transitions and containment.

## Global Constraints

- Do not add business pages, business modules, API endpoints, request fields, routes, stores, or mock data.
- Keep every existing Chinese UI string unchanged.
- Preserve all finished Web modules and every existing H5 capability.
- Use native CSS transform/transition and browser containment only; add no dependency.
- Preserve mock-mode and `VITE_RESUME_API_URL` backend docking behavior.
- Do not delete unrelated files or revert the existing uncommitted robustness baseline.

---

### Task 1: Unify transient H5 error toasts

**Files:**
- Create: `resume-miniprogram/src/utils/error-feedback.ts`
- Create: `resume-miniprogram/src/tests/error-feedback.spec.ts`
- Modify: `resume-miniprogram/src/pages/applications/index.vue`
- Modify: `resume-miniprogram/src/pages/evidence/index.vue`
- Modify: `resume-miniprogram/src/pages/career-planner/index.vue`
- Modify: `resume-miniprogram/src/pages/template-picker/index.vue`
- Modify: `resume-miniprogram/src/pages/resume-editor/index.vue`
- Modify: `resume-miniprogram/src/pages/privacy/index.vue`
- Modify: `resume-miniprogram/src/pages/drafts/index.vue`

**Interfaces:**
- Produces: `showErrorToast(title: string): void`
- Consumes: the existing global `uni.showToast` API.
- Keeps success and neutral informational toasts at their current call sites.

- [ ] **Step 1: Write the failing utility test**

```ts
import { afterEach, describe, expect, it, vi } from "vitest"
import { showErrorToast } from "../utils/error-feedback"

afterEach(() => vi.unstubAllGlobals())

describe("showErrorToast", () => {
  it("uses the shared transient error presentation", () => {
    const showToast = vi.fn()
    vi.stubGlobal("uni", { showToast })
    showErrorToast("网络请求失败")
    expect(showToast).toHaveBeenCalledWith({
      title: "网络请求失败",
      icon: "none",
      duration: 2600,
      mask: false,
    })
  })
})
```

- [ ] **Step 2: Run the focused test and verify RED**

Run: `cd resume-miniprogram; npm.cmd run test:unit -- src/tests/error-feedback.spec.ts`

Expected: FAIL because `../utils/error-feedback` does not exist.

- [ ] **Step 3: Implement the minimal wrapper**

```ts
export function showErrorToast(title: string): void {
  uni.showToast({ title, icon: "none", duration: 2600, mask: false })
}
```

- [ ] **Step 4: Migrate only error-shaped calls**

Import `showErrorToast` in the listed pages and replace calls shaped like:

```ts
uni.showToast({ title: reason instanceof Error ? reason.message : "提醒保存失败，请稍后重试", icon: "none" })
```

with:

```ts
showErrorToast(reason instanceof Error ? reason.message : "提醒保存失败，请稍后重试")
```

Also migrate invalid-parameter toasts such as `"请填写目标岗位"`. Do not migrate `icon: "success"`, clipboard confirmations, offline-save notices, or neutral preview notices.

- [ ] **Step 5: Run focused and full H5 tests**

Run: `cd resume-miniprogram; npm.cmd run test:unit -- src/tests/error-feedback.spec.ts`

Expected: PASS.

Run: `cd resume-miniprogram; npm.cmd run test:unit -- --reporter=dot`

Expected: all H5 tests PASS.

- [ ] **Step 6: Commit the H5 error-feedback unit**

```powershell
git add resume-miniprogram/src/utils/error-feedback.ts resume-miniprogram/src/tests/error-feedback.spec.ts resume-miniprogram/src/pages/applications/index.vue resume-miniprogram/src/pages/evidence/index.vue resume-miniprogram/src/pages/career-planner/index.vue resume-miniprogram/src/pages/template-picker/index.vue resume-miniprogram/src/pages/resume-editor/index.vue resume-miniprogram/src/pages/privacy/index.vue resume-miniprogram/src/pages/drafts/index.vue
git commit -m "fix(h5): unify transient error feedback"
```

### Task 2: Finish H5 motion, disabled, and long-list contracts

**Files:**
- Modify: `resume-miniprogram/src/tests/interaction.spec.ts`
- Modify: `resume-miniprogram/src/App.vue`
- Modify: `resume-miniprogram/src/components/FormField.vue`
- Modify: `resume-miniprogram/src/pages/account/index.vue`
- Modify: `resume-miniprogram/src/pages/career-assessment/index.vue`
- Modify: `resume-miniprogram/src/pages/career-planner/index.vue`
- Modify: `resume-miniprogram/src/pages/drafts/index.vue`
- Modify: `resume-miniprogram/src/pages/job-collection/index.vue`
- Modify: `resume-miniprogram/src/pages/job-search/index.vue`
- Modify: `resume-miniprogram/src/pages/knowledgebase/index.vue`
- Modify: `resume-miniprogram/src/pages/login/index.vue`
- Modify: `resume-miniprogram/src/pages/membership/index.vue`
- Modify: `resume-miniprogram/src/pages/operator-knowledge/index.vue`
- Modify: `resume-miniprogram/src/pages/orders/index.vue`
- Modify: `resume-miniprogram/src/pages/role-comparison/index.vue`
- Modify: `resume-miniprogram/src/pages/applications/index.vue`
- Modify: `resume-miniprogram/src/pages/evidence/index.vue`

**Interfaces:**
- Produces: global `.ui-error-tip`, `.ui-error-tip--inline`, `.ui-long-list-item`, and disabled/motion token contracts.
- Consumes: existing page templates and centralized `App.vue` variables.

- [ ] **Step 1: Add failing static contracts**

Extend `resume-miniprogram/src/tests/interaction.spec.ts`:

```ts
it("contains off-screen H5 long-list items without changing list data", () => {
  const app = readFileSync(new URL("../App.vue", import.meta.url), "utf8")
  const applications = readFileSync(new URL("../pages/applications/index.vue", import.meta.url), "utf8")
  const evidence = readFileSync(new URL("../pages/evidence/index.vue", import.meta.url), "utf8")
  const jobs = readFileSync(new URL("../pages/job-search/index.vue", import.meta.url), "utf8")
  expect(app).toContain(".ui-long-list-item")
  expect(app).toContain("content-visibility: auto")
  expect(app).toContain("contain-intrinsic-size")
  expect(applications).toContain("ui-long-list-item")
  expect(evidence).toContain("ui-long-list-item")
  expect(jobs).toContain("ui-long-list-item")
})
```

- [ ] **Step 2: Run the focused test and verify RED**

Run: `cd resume-miniprogram; npm.cmd run test:unit -- src/tests/interaction.spec.ts`

Expected: FAIL because `.ui-long-list-item` is absent.

- [ ] **Step 3: Add the global containment primitive**

Add to `resume-miniprogram/src/App.vue`:

```css
.ui-long-list-item {
  content-visibility: auto;
  contain: layout paint style;
  contain-intrinsic-size: auto 220rpx;
}
```

Keep the current non-overshooting easing, `translate3d` entry animation, reduced-motion block, and comprehensive disabled selectors. Change remaining high-frequency page-local `ease` transitions to `var(--ui-motion-ease)` only where found by `rg -n "transition:.*ease" resume-miniprogram/src/pages`.

- [ ] **Step 4: Attach containment to existing list entries**

Add `ui-long-list-item` alongside existing classes:

```vue
<view v-for="item in visibleApplications" :key="item.id" class="card record-card ui-long-list-item">
<view v-for="item in evidence" :key="item.id" class="card evidence-card ui-long-list-item">
<view v-for="item in favorites" :key="item.id" class="favorite-card ui-long-list-item">
<view v-for="source in marketSearchReport?.results" :key="source.url" class="market-source ui-long-list-item">
```

Also attach it to existing job-analysis section, growth-stage, plan-block, and priority-gap result nodes. Do not add wrappers or alter `v-for`, keys, conditions, or data transformations.

- [ ] **Step 5: Run H5 tests and build**

Run: `cd resume-miniprogram; npm.cmd run test:unit -- --reporter=dot`

Run: `cd resume-miniprogram; npm.cmd run build:h5`

Expected: all tests PASS and H5 build exits 0.

- [ ] **Step 6: Commit the H5 rendering unit**

Stage `resume-miniprogram/src/App.vue`, `FormField.vue`, `interaction.spec.ts`, all previously modified H5 error templates, and the four long-list pages. Commit:

```powershell
git commit -m "perf(h5): harden motion and long-list rendering"
```

### Task 3: Finish Web feedback, theme, responsive, and long-list rendering

**Files:**
- Create: `web-frontend/src/components/ErrorNotice.vue` (already present in the worktree baseline)
- Modify: `web-frontend/src/main.ts`
- Modify: `web-frontend/src/App.vue`
- Modify: `web-frontend/src/styles/base.css`
- Modify: `web-frontend/src/tests/interaction.spec.ts`
- Modify: `web-frontend/src/components/LoginPanel.vue`
- Modify: `web-frontend/src/views/AccountView.vue`
- Modify: `web-frontend/src/views/ApplicationsView.vue`
- Modify: `web-frontend/src/views/AssessmentView.vue`
- Modify: `web-frontend/src/views/CareerView.vue`
- Modify: `web-frontend/src/views/ComparisonView.vue`
- Modify: `web-frontend/src/views/EvidenceView.vue`
- Modify: `web-frontend/src/views/InsightsView.vue`
- Modify: `web-frontend/src/views/JobsView.vue`
- Modify: `web-frontend/src/views/MembershipView.vue`
- Modify: `web-frontend/src/views/OverviewView.vue`
- Modify: `web-frontend/src/views/ResumeEditorView.vue`
- Modify: `web-frontend/src/views/ResumeView.vue`

**Interfaces:**
- Consumes: globally registered `ErrorNotice` with `message: string`, `compact?: boolean`, and optional default action slot.
- Produces: transient `html.theme-switching` contract and CSS containment for existing long-list selectors.

- [ ] **Step 1: Add failing Web static contracts**

Extend `web-frontend/src/tests/interaction.spec.ts`:

```ts
it("contains off-screen Web records and disables theme motion when requested", () => {
  const styles = readFileSync(new URL("../styles/base.css", import.meta.url), "utf8")
  expect(styles).toContain("content-visibility: auto")
  expect(styles).toContain("contain-intrinsic-size")
  expect(styles).toContain("html.theme-switching .web-shell *")
  expect(styles).toContain("prefers-reduced-motion: reduce")
})
```

- [ ] **Step 2: Run the focused test and verify RED**

Run: `cd web-frontend; npm.cmd test -- src/tests/interaction.spec.ts`

Expected: FAIL because long-list containment and the descendant theme selector are absent.

- [ ] **Step 3: Complete theme transition coverage**

Keep the initial-render guard and timer cleanup in `App.vue`. Add a theme-window selector in `base.css`:

```css
html.theme-switching .web-shell,
html.theme-switching .web-shell * {
  transition-property: color, background-color, border-color, box-shadow, fill, stroke;
  transition-duration: var(--theme-transition);
  transition-timing-function: var(--motion-ease);
}
```

In the existing reduced-motion media block, disable these theme transitions with `transition: none !important`. Do not persist the class or animate initial theme assignment.

- [ ] **Step 4: Contain existing Web list entries**

Add one selector without template wrappers:

```css
.application-record,
.evidence-list > article,
.record-list > .record-row,
.task-list > .task-row,
.order-list > .order-row {
  content-visibility: auto;
  contain: layout paint style;
  contain-intrinsic-size: auto 82px;
}
```

Retain the existing 1600px, 540px, and 380px rules: 1360px maximum workspace width, 14px small-window topbar padding, 34px narrow icon buttons, 98px maximum user-chip width, and hidden secondary user text below 380px.

- [ ] **Step 5: Run Web tests and build**

Run: `cd web-frontend; npm.cmd test -- --reporter=dot`

Run: `cd web-frontend; npm.cmd run build`

Expected: all tests PASS and Web build exits 0.

- [ ] **Step 6: Commit the Web interaction unit**

Stage all modified files under `web-frontend/src` and commit:

```powershell
git commit -m "perf(web): polish theme and long-list rendering"
```

### Task 4: Changelog, mechanical audit, and final verification

**Files:**
- Modify: `docs/interaction-upgrade-changelog.md`

**Interfaces:**
- Consumes: verified test/build counts from Tasks 1-3.
- Produces: a clean, documented branch with no generated artifacts staged.

- [ ] **Step 1: Append the changelog record**

Record the H5 toast wrapper, H5/Web containment selectors, theme-window coverage, disabled/motion audit, responsive edges, and exact final verification counts. Do not rewrite earlier entries.

- [ ] **Step 2: Run the Impeccable detector once**

Run:

```powershell
node C:\Users\16102\.codex\skills\impeccable\scripts\detect.mjs --json resume-miniprogram/src/App.vue resume-miniprogram/src/pages/applications/index.vue resume-miniprogram/src/pages/evidence/index.vue resume-miniprogram/src/pages/job-search/index.vue web-frontend/src/App.vue web-frontend/src/styles/base.css web-frontend/src/components/ErrorNotice.vue
```

Review findings once. Fix only issues introduced by this iteration; do not start unrelated redesign work.

- [ ] **Step 3: Run fresh complete verification**

Run all four commands:

```powershell
Set-Location resume-miniprogram
npm.cmd run test:unit -- --reporter=dot
npm.cmd run build:h5
Set-Location ..\web-frontend
npm.cmd test -- --reporter=dot
npm.cmd run build
```

Expected: all tests PASS and both builds exit 0.

- [ ] **Step 4: Audit scope and whitespace**

Run:

```powershell
git diff --check
git diff --name-only | Select-String -Pattern '(^|/)(services|stores|api|router|routes)/|package-lock|pnpm-lock|yarn.lock'
```

Expected: `git diff --check` exits 0 and the scope pattern returns no modified files.

- [ ] **Step 5: Commit docs and confirm cleanliness**

```powershell
git add docs/interaction-upgrade-changelog.md
git commit -m "docs: record frontend robustness polish"
git status --short
```

Expected: the commit succeeds and `git status --short` prints nothing.
