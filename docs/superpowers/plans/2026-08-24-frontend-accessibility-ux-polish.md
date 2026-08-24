# Frontend Accessibility and UX Polish Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Improve accessibility, rapid-repeat protection, long-text readability, overlay dismissal, and viewport-safe tooltip behavior in both existing frontends without changing business behavior.

**Architecture:** Keep H5 and Web runtime code separate while applying the same interaction contracts. Reuse existing pending refs and buttons, add handler-entry guards, and introduce one tiny threshold helper plus one `ExpandableText` component per frontend; no global directive, dependency, modal framework, route, or API change.

**Tech Stack:** Vue 3.5, TypeScript, UniApp H5, Vite, Vitest, Tailwind-compatible existing CSS architecture, native CSS line clamp and ARIA attributes.

## Global Constraints

- `resume-miniprogram` H5 gets no new business page, route, capability, API, data model, or store.
- `web-frontend` keeps every delivered business module and API flow intact; no placeholder replacement.
- Keep original Chinese UI text and mock data unchanged. New `展开` and `收起` control labels are allowed by the approved design.
- Use existing CSS/native platform behavior and add no third-party animation, tooltip, modal, or debounce dependency.
- Preserve existing loading cleanup on success, failure, abort, and timeout.
- All frontend unit tests and production builds must pass.
- Append the iteration to `docs/interaction-upgrade-changelog.md`.
- Keep the Git worktree clean and do not delete unrelated files.

---

### Task 1: H5 Accessibility and Overlay Semantics

**Files:**
- Modify: `resume-miniprogram/src/components/FormField.vue`
- Modify: `resume-miniprogram/src/components/OnboardingTour.vue`
- Modify: `resume-miniprogram/src/pages/job-search/index.vue`
- Modify: `resume-miniprogram/src/pages/applications/index.vue`
- Modify: `resume-miniprogram/src/tests/interaction.spec.ts`

**Interfaces:**
- Consumes: existing `FormField` props, `OnboardingTour` `complete` event, and current page action handlers.
- Produces: accessible input/error relationships, keyboard-operable non-button actions, and reliable mask/content event separation.

- [ ] **Step 1: Add failing H5 accessibility contract tests**

Append assertions to `resume-miniprogram/src/tests/interaction.spec.ts`:

```ts
it("exposes H5 form, action, and overlay accessibility semantics", () => {
  const field = readFileSync(new URL("../components/FormField.vue", import.meta.url), "utf8")
  const onboarding = readFileSync(new URL("../components/OnboardingTour.vue", import.meta.url), "utf8")
  const jobs = readFileSync(new URL("../pages/job-search/index.vue", import.meta.url), "utf8")
  const applications = readFileSync(new URL("../pages/applications/index.vue", import.meta.url), "utf8")

  expect(field).toContain(':aria-label="label"')
  expect(field).toContain(':aria-invalid="Boolean(error)"')
  expect(field).toContain(':aria-describedby="error ? errorId : undefined"')
  expect(onboarding).toContain('@tap="closeFromMask"')
  expect(onboarding).toContain("@tap.stop")
  expect(jobs).toContain('role="button"')
  expect(jobs).toContain('tabindex="0"')
  expect(jobs).toContain(':aria-expanded="isAnalysisSectionOpen(section.order)"')
  expect(applications).toContain(':aria-label="`删除 ${item.company} 的 ${item.roleName} 投递记录`"')
})
```

- [ ] **Step 2: Run the focused test and verify RED**

Run:

```powershell
Set-Location resume-miniprogram
npm.cmd run test:unit -- src/tests/interaction.spec.ts --reporter=dot
```

Expected: FAIL because the new ARIA and mask-event contracts are absent.

- [ ] **Step 3: Implement accessible H5 form and overlay behavior**

In `FormField.vue`, use Vue 3.5's built-in ID generator and connect the input to its error without changing visible copy:

```ts
import { useId } from "vue"

const fieldId = useId()
const errorId = `${fieldId}-error`
```

```vue
<input
  :id="fieldId"
  :aria-label="label"
  :aria-invalid="Boolean(error)"
  :aria-describedby="error ? errorId : undefined"
  ...
/>
<text v-if="error" :id="errorId" class="ui-error-tip ui-error-tip--inline" role="alert">{{ error }}</text>
```

In `OnboardingTour.vue`, keep the existing completion event and separate mask taps from dialog taps:

```ts
function closeFromMask(): void {
  emit("complete")
}
```

```vue
<view v-if="visible" class="onboarding-mask" @tap="closeFromMask">
  <view class="onboarding-dialog" role="dialog" aria-modal="true" aria-label="新手引导" @tap.stop>
```

Add explicit `aria-label` values to the skip, next/complete, and destination buttons. In `job-search`, mark the decorative search glyph hidden, label the search input and contextual role-removal buttons, and give clickable market/analysis rows `role="button"`, `tabindex="0"`, Enter/Space handlers, and `aria-expanded` where applicable. Add contextual labels to application edit/timeline/delete row actions.

- [ ] **Step 4: Run the focused H5 test and verify GREEN**

Run:

```powershell
Set-Location resume-miniprogram
npm.cmd run test:unit -- src/tests/interaction.spec.ts --reporter=dot
```

Expected: PASS.

- [ ] **Step 5: Commit Task 1**

```powershell
git add resume-miniprogram/src/components/FormField.vue resume-miniprogram/src/components/OnboardingTour.vue resume-miniprogram/src/pages/job-search/index.vue resume-miniprogram/src/pages/applications/index.vue resume-miniprogram/src/tests/interaction.spec.ts
git commit -m "fix(h5): improve accessible interaction semantics"
```

### Task 2: H5 Rapid-Repeat Request Guards

**Files:**
- Modify: `resume-miniprogram/src/pages/applications/index.vue`
- Modify: `resume-miniprogram/src/pages/career-assessment/index.vue`
- Modify: `resume-miniprogram/src/pages/job-search/index.vue`
- Modify: `resume-miniprogram/src/pages/membership/index.vue`
- Modify: `resume-miniprogram/src/tests/interaction.spec.ts`

**Interfaces:**
- Consumes: existing `saving`, `submitting`, `loading`, `marketSearchLoading`, `reviewLoading`, `pdfLoading`, `adviceLoading`, and `purchasing` refs.
- Produces: synchronous handler-entry rejection of duplicate taps while retaining every original API call and `finally` cleanup.

- [ ] **Step 1: Add failing H5 duplicate-action assertions**

Add to the pending-control test in `resume-miniprogram/src/tests/interaction.spec.ts`:

```ts
const membership = readFileSync(new URL("../pages/membership/index.vue", import.meta.url), "utf8")
expect(applications).toContain("if (saving.value) return")
expect(assessment).toContain("if (submitting.value) return")
expect(jobSearch).toContain("if (loading.value) return")
expect(jobSearch).toContain("if (marketSearchLoading.value || !activeRoleName.value) return")
expect(jobSearch).toContain("if (reviewLoading.value || pdfLoading.value) return")
expect(jobSearch).toContain("if (adviceLoading.value) return")
expect(membership).toContain("if (purchasing.value) return")
```

- [ ] **Step 2: Run the focused test and verify RED**

Run:

```powershell
Set-Location resume-miniprogram
npm.cmd run test:unit -- src/tests/interaction.spec.ts --reporter=dot
```

Expected: FAIL on at least the applications, assessment, job-search, and membership guards.

- [ ] **Step 3: Add minimal synchronous guards**

Add the appropriate first-line guard before validation or pending assignment:

```ts
async function save() {
  if (saving.value) return
  // existing validation and request flow
}
```

Apply the same pattern to career-assessment `submit`, job-search `loadJobAnalyses`, `loadMarketSearch`, `reviewResume`, `chooseResumePdf`, and `requestCareerAdvice`, plus membership `beginDemoCheckout` and `completeCheckout`. Cross-action guards must include the paired pending state, for example:

```ts
if (reviewLoading.value || pdfLoading.value) return
```

Do not add debounce timers and do not move or rewrite API calls.

- [ ] **Step 4: Run focused and complete H5 tests**

Run:

```powershell
Set-Location resume-miniprogram
npm.cmd run test:unit -- src/tests/interaction.spec.ts --reporter=dot
npm.cmd run test:unit -- --reporter=dot
```

Expected: both commands PASS.

- [ ] **Step 5: Commit Task 2**

```powershell
git add resume-miniprogram/src/pages/applications/index.vue resume-miniprogram/src/pages/career-assessment/index.vue resume-miniprogram/src/pages/job-search/index.vue resume-miniprogram/src/pages/membership/index.vue resume-miniprogram/src/tests/interaction.spec.ts
git commit -m "fix(h5): block rapid duplicate actions"
```

### Task 3: H5 Long-Text Expansion

**Files:**
- Create: `resume-miniprogram/src/utils/expandable-text.ts`
- Create: `resume-miniprogram/src/components/ExpandableText.vue`
- Create: `resume-miniprogram/src/tests/expandable-text.spec.ts`
- Modify: `resume-miniprogram/src/components/ResumePreview.vue`
- Modify: `resume-miniprogram/src/pages/applications/index.vue`
- Modify: `resume-miniprogram/src/pages/job-collection/index.vue`
- Modify: `resume-miniprogram/src/pages/job-search/index.vue`
- Modify: `resume-miniprogram/src/tests/interaction.spec.ts`

**Interfaces:**
- Produces: `isExpandableText(text: string, expandAt: number): boolean` and `ExpandableText` props `{ text: string; lines?: 1 | 4; expandAt?: number; label?: string }`.
- Consumes: original display strings only; it emits no business event and mutates no domain data.

- [ ] **Step 1: Write failing threshold tests**

Create `resume-miniprogram/src/tests/expandable-text.spec.ts`:

```ts
import { describe, expect, it } from "vitest"
import { isExpandableText } from "../utils/expandable-text"

describe("isExpandableText", () => {
  it("uses the configured threshold after trimming", () => {
    expect(isExpandableText(" 数据分析师 ", 18)).toBe(false)
    expect(isExpandableText("高级数据分析与商业策略解决方案负责人", 18)).toBe(true)
    expect(isExpandableText("x".repeat(96), 96)).toBe(false)
    expect(isExpandableText("x".repeat(97), 96)).toBe(true)
  })
})
```

Also add static assertions to `interaction.spec.ts` that `ExpandableText.vue` contains `aria-expanded`, `-webkit-line-clamp`, `展开`, and `收起`.

- [ ] **Step 2: Run the new tests and verify RED**

Run:

```powershell
Set-Location resume-miniprogram
npm.cmd run test:unit -- src/tests/expandable-text.spec.ts src/tests/interaction.spec.ts --reporter=dot
```

Expected: FAIL because the helper and component do not exist.

- [ ] **Step 3: Implement the pure helper and H5 component**

Create `utils/expandable-text.ts`:

```ts
export function isExpandableText(text: string, expandAt: number): boolean {
  return text.trim().length > expandAt
}
```

Implement `ExpandableText.vue` with a local `expanded` ref, computed `canExpand`, stable content ID, `aria-controls`, and `aria-expanded`. The collapsed text uses:

```vue
<script setup lang="ts">
import { computed, ref, useId } from "vue"
import { isExpandableText } from "../utils/expandable-text"

const props = withDefaults(defineProps<{
  text: string
  lines?: 1 | 4
  expandAt?: number
  label?: string
}>(), { lines: 4, expandAt: 96, label: "内容" })
const expanded = ref(false)
const contentId = useId()
const canExpand = computed(() => isExpandableText(props.text, props.expandAt))
const toggleLabel = computed(() => `${expanded.value ? "收起" : "展开"}${props.label}`)
</script>

<template>
  <view class="expandable-text">
    <text
      :id="contentId"
      class="expandable-copy"
      :class="{ 'is-collapsed': canExpand && !expanded }"
      :style="{ '--expandable-lines': String(lines) }"
    >{{ text }}</text>
    <button
      v-if="canExpand"
      size="mini"
      class="expandable-toggle"
      :aria-controls="contentId"
      :aria-expanded="expanded"
      :aria-label="toggleLabel"
      @click="expanded = !expanded"
    >{{ expanded ? "收起" : "展开" }}</button>
  </view>
</template>
```

The component CSS includes:

```css
.expandable-copy.is-collapsed {
  display: -webkit-box;
  overflow: hidden;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: var(--expandable-lines);
  overflow-wrap: anywhere;
}
```

The toggle is a native button and appears only when `isExpandableText(props.text, props.expandAt)` is true.

- [ ] **Step 4: Apply H5 long-text rules to existing content**

Use `:lines="1" :expand-at="18"` for application role/company, saved favorite role, current job role, and resume company/position identity text. Use `:lines="4" :expand-at="96"` for self-evaluation, course detail, employment description, and project description in `ResumePreview.vue`.

Do not wrap an `ExpandableText` inside another button. Existing role-tab buttons retain their current text and get CSS overflow protection only when needed.

- [ ] **Step 5: Run H5 tests and build**

Run:

```powershell
Set-Location resume-miniprogram
npm.cmd run test:unit -- src/tests/expandable-text.spec.ts src/tests/interaction.spec.ts --reporter=dot
npm.cmd run test:unit -- --reporter=dot
npm.cmd run build:h5
```

Expected: tests PASS and H5 build completes.

- [ ] **Step 6: Commit Task 3**

```powershell
git add resume-miniprogram/src/utils/expandable-text.ts resume-miniprogram/src/components/ExpandableText.vue resume-miniprogram/src/tests/expandable-text.spec.ts resume-miniprogram/src/tests/interaction.spec.ts resume-miniprogram/src/components/ResumePreview.vue resume-miniprogram/src/pages/applications/index.vue resume-miniprogram/src/pages/job-collection/index.vue resume-miniprogram/src/pages/job-search/index.vue
git commit -m "feat(h5): add accessible long-text expansion"
```

### Task 4: Web Accessibility, Tooltip, and Rapid-Repeat Guards

**Files:**
- Modify: `web-frontend/src/App.vue`
- Modify: `web-frontend/src/components/LoginPanel.vue`
- Modify: `web-frontend/src/components/WebTopbar.vue`
- Modify: `web-frontend/src/views/ApplicationsView.vue`
- Modify: `web-frontend/src/views/CareerView.vue`
- Modify: `web-frontend/src/views/EvidenceView.vue`
- Modify: `web-frontend/src/views/InsightsView.vue`
- Modify: `web-frontend/src/views/JobsView.vue`
- Modify: `web-frontend/src/views/ResumeView.vue`
- Modify: `web-frontend/src/tests/interaction.spec.ts`

**Interfaces:**
- Consumes: current loading refs, existing `ErrorNotice`, native labels, and native `title` behavior.
- Produces: handler-entry duplicate protection, contextual action names, error relationships, and short viewport-managed native tooltips.

- [ ] **Step 1: Add failing Web contracts**

Extend `web-frontend/src/tests/interaction.spec.ts`:

```ts
it("guards rapid Web actions and exposes accessible context", () => {
  const app = readFileSync(new URL("../App.vue", import.meta.url), "utf8")
  const login = readFileSync(new URL("../components/LoginPanel.vue", import.meta.url), "utf8")
  const topbar = readFileSync(new URL("../components/WebTopbar.vue", import.meta.url), "utf8")
  const career = readFileSync(new URL("../views/CareerView.vue", import.meta.url), "utf8")
  const evidence = readFileSync(new URL("../views/EvidenceView.vue", import.meta.url), "utf8")
  const insights = readFileSync(new URL("../views/InsightsView.vue", import.meta.url), "utf8")
  const jobs = readFileSync(new URL("../views/JobsView.vue", import.meta.url), "utf8")

  expect(app).toContain("if (logoutLoading.value) return")
  expect(login).toContain("if (loading.value || sending.value) return")
  expect(career).toContain("if (saving.value) return")
  expect(evidence).toContain("if (readinessLoading.value) return")
  expect(insights).toContain("if (loading.value) return")
  expect(jobs).toContain("if (loading.value) return")
  expect(jobs).toContain("if (!result.value || saving.value) return")
  expect(login).toContain("aria-describedby")
  expect(login).toContain("aria-invalid")
  expect(topbar).toContain(":title=")
  expect(topbar).toContain(":aria-label=")
  expect(topbar).toContain(":aria-pressed=\"dark\"")
})
```

- [ ] **Step 2: Run the focused Web test and verify RED**

Run:

```powershell
Set-Location web-frontend
npm.cmd test -- src/tests/interaction.spec.ts --reporter=dot
```

Expected: FAIL on the missing handler guards and form relationships.

- [ ] **Step 3: Implement Web duplicate guards**

Add synchronous pending checks to App logout, both LoginPanel request paths, Career add-task, Evidence readiness, Insights query, and Jobs query/favorite. Cross-lock login actions:

```ts
async function sendCode() {
  if (loading.value || sending.value) return
  // existing validation and request
}

async function submit() {
  if (loading.value || sending.value) return
  // existing request
}
```

Pair those guards with existing button disabled/loading props. Do not add a delay or change request payloads.

- [ ] **Step 4: Implement Web accessible naming and form error relationships**

Give login, jobs, and applications forms conditional `aria-describedby` values and stable IDs on their existing `ErrorNotice` nodes. Use the existing constraints to mark only locally invalid fields:

```vue
<!-- LoginPanel examples -->
<input v-model.trim="phone" :aria-invalid="Boolean(error && !/^1\d{10}$/.test(phone))" ... />
<input v-model.trim="code" :aria-invalid="Boolean(error && code.length !== 6)" ... />

<!-- JobsView -->
<input v-model.trim="roleName" :aria-invalid="Boolean(error && !roleName.trim())" ... />

<!-- ApplicationsView -->
<input v-model.trim="form.roleName" :aria-invalid="Boolean(error && !form.roleName.trim())" ... />
```

Use the equivalent existing length constraints for account and password. Request-level failures with valid values leave every field valid and remain attached to the form. Add contextual `aria-label`/native `title` to row edit/copy/delete controls in Applications and Resume. Keep WebTopbar's short matching `title` and `aria-label` values for theme and logout icon buttons, and add `:aria-pressed="dark"` to the theme toggle; do not add a custom tooltip element or CSS pseudo-tooltip.

All visible `<label>` wrappers stay in source order. Do not add positive `tabindex` values.

- [ ] **Step 5: Run Web focused and complete tests**

Run:

```powershell
Set-Location web-frontend
npm.cmd test -- src/tests/interaction.spec.ts --reporter=dot
npm.cmd test -- --reporter=dot
```

Expected: both commands PASS.

- [ ] **Step 6: Commit Task 4**

```powershell
git add web-frontend/src/App.vue web-frontend/src/components/LoginPanel.vue web-frontend/src/components/WebTopbar.vue web-frontend/src/views/ApplicationsView.vue web-frontend/src/views/CareerView.vue web-frontend/src/views/EvidenceView.vue web-frontend/src/views/InsightsView.vue web-frontend/src/views/JobsView.vue web-frontend/src/views/ResumeView.vue web-frontend/src/tests/interaction.spec.ts
git commit -m "fix(web): improve accessible action handling"
```

### Task 5: Web Long-Text Expansion

**Files:**
- Create: `web-frontend/src/lib/expandable-text.ts`
- Create: `web-frontend/src/components/ExpandableText.vue`
- Create: `web-frontend/src/tests/expandable-text.spec.ts`
- Modify: `web-frontend/src/styles/base.css`
- Modify: `web-frontend/src/views/ApplicationsView.vue`
- Modify: `web-frontend/src/views/EvidenceView.vue`
- Modify: `web-frontend/src/views/JobsView.vue`
- Modify: `web-frontend/src/views/ResumeView.vue`
- Modify: `web-frontend/src/tests/interaction.spec.ts`

**Interfaces:**
- Produces: `isExpandableText(text: string, expandAt: number): boolean` and the same `ExpandableText` prop contract as H5.
- Consumes: existing role, company, draft title, evidence action, and job-summary strings only.

- [ ] **Step 1: Write failing Web threshold and component-contract tests**

Create `web-frontend/src/tests/expandable-text.spec.ts`:

```ts
import { describe, expect, it } from "vitest"
import { isExpandableText } from "../lib/expandable-text"

describe("isExpandableText", () => {
  it("uses the configured threshold after trimming", () => {
    expect(isExpandableText(" 数据分析师 ", 18)).toBe(false)
    expect(isExpandableText("高级数据分析与商业策略解决方案负责人", 18)).toBe(true)
    expect(isExpandableText("x".repeat(96), 96)).toBe(false)
    expect(isExpandableText("x".repeat(97), 96)).toBe(true)
  })
})
```

Extend `interaction.spec.ts`:

```ts
it("uses the accessible Web long-text contract", () => {
  const component = readFileSync(new URL("../components/ExpandableText.vue", import.meta.url), "utf8")
  const styles = readFileSync(new URL("../styles/base.css", import.meta.url), "utf8")
  expect(component).toContain(":aria-expanded=\"expanded\"")
  expect(component).toContain("展开")
  expect(component).toContain("收起")
  expect(styles).toContain("-webkit-line-clamp")
  expect(styles).toContain("overflow-wrap: anywhere")
})
```

- [ ] **Step 2: Run new Web tests and verify RED**

Run:

```powershell
Set-Location web-frontend
npm.cmd test -- src/tests/expandable-text.spec.ts src/tests/interaction.spec.ts --reporter=dot
```

Expected: FAIL because the helper and component do not exist.

- [ ] **Step 3: Implement the helper and Web component**

Create `web-frontend/src/lib/expandable-text.ts`:

```ts
export function isExpandableText(text: string, expandAt: number): boolean {
  return text.trim().length > expandAt
}
```

Implement `web-frontend/src/components/ExpandableText.vue`:

```vue
<script setup lang="ts">
import { computed, ref, useId } from "vue"
import { isExpandableText } from "../lib/expandable-text"

const props = withDefaults(defineProps<{
  text: string
  lines?: 1 | 4
  expandAt?: number
  label?: string
}>(), { lines: 4, expandAt: 96, label: "内容" })
const expanded = ref(false)
const contentId = useId()
const canExpand = computed(() => isExpandableText(props.text, props.expandAt))
const toggleLabel = computed(() => `${expanded.value ? "收起" : "展开"}${props.label}`)
</script>

<template>
  <span class="expandable-text">
    <span
      :id="contentId"
      class="expandable-copy"
      :class="{ 'is-collapsed': canExpand && !expanded }"
      :style="{ '--expandable-lines': String(lines) }"
    >{{ text }}</span>
    <button
      v-if="canExpand"
      class="expandable-toggle"
      type="button"
      :aria-controls="contentId"
      :aria-expanded="expanded"
      :aria-label="toggleLabel"
      @click="expanded = !expanded"
    >{{ expanded ? "收起" : "展开" }}</button>
  </span>
</template>
```

Put reusable visual rules in `base.css`:

```css
.expandable-copy.is-collapsed {
  display: -webkit-box;
  overflow: hidden;
  overflow-wrap: anywhere;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: var(--expandable-lines);
}
```

Use the existing focus-visible and disabled tokens; do not add a tooltip library.

- [ ] **Step 4: Apply Web long-text behavior**

Use one-line/18-character treatment for application role/company, job result role, and resume draft title. Use four-line/96-character treatment for job report summary and evidence action text. Keep edit textareas untruncated because users must be able to edit the full value.

- [ ] **Step 5: Run Web tests and production build**

Run:

```powershell
Set-Location web-frontend
npm.cmd test -- src/tests/expandable-text.spec.ts src/tests/interaction.spec.ts --reporter=dot
npm.cmd test -- --reporter=dot
npm.cmd run build
```

Expected: tests PASS and the production build completes.

- [ ] **Step 6: Commit Task 5**

```powershell
git add web-frontend/src/lib/expandable-text.ts web-frontend/src/components/ExpandableText.vue web-frontend/src/tests/expandable-text.spec.ts web-frontend/src/tests/interaction.spec.ts web-frontend/src/styles/base.css web-frontend/src/views/ApplicationsView.vue web-frontend/src/views/EvidenceView.vue web-frontend/src/views/JobsView.vue web-frontend/src/views/ResumeView.vue
git commit -m "feat(web): add accessible long-text expansion"
```

### Task 6: Changelog, UI Audit, Full Verification, and Scope Audit

**Files:**
- Modify: `docs/interaction-upgrade-changelog.md`

**Interfaces:**
- Consumes: completed H5 and Web changes and final command results.
- Produces: an auditable iteration record and a clean verified branch.

- [ ] **Step 1: Append the iteration record**

Add a `2026-08-24 accessibility and UX edge-case pass` section that records:

- H5 accessible labels/form errors, duplicate-action guards, long-text locations, and onboarding mask behavior.
- Web form/action semantics, duplicate-action guards, long-text locations, and native viewport-managed tooltip choice.
- Confirmation that Web had no custom modal/drawer mask to replace.
- Final test and build totals from the commands below.
- Confirmation that routes, APIs, services, stores, mock data, Chinese business content, and lockfiles did not change.

- [ ] **Step 2: Run the Impeccable detector once**

Run exactly once after all UI edits:

```powershell
node C:\Users\16102\.codex\skills\impeccable\scripts\detect.mjs --json resume-miniprogram/src/components/FormField.vue resume-miniprogram/src/components/OnboardingTour.vue resume-miniprogram/src/components/ExpandableText.vue resume-miniprogram/src/pages/job-search/index.vue resume-miniprogram/src/pages/applications/index.vue web-frontend/src/components/LoginPanel.vue web-frontend/src/components/WebTopbar.vue web-frontend/src/components/ExpandableText.vue web-frontend/src/styles/base.css web-frontend/src/views/ApplicationsView.vue web-frontend/src/views/JobsView.vue
```

Expected: no findings related to this iteration. Fix any introduced finding before final verification, but do not rerun the detector.

- [ ] **Step 3: Run all final verification commands**

Run:

```powershell
Set-Location resume-miniprogram
npm.cmd run test:unit -- --reporter=dot
npm.cmd run build:h5

Set-Location ..\web-frontend
npm.cmd test -- --reporter=dot
npm.cmd run build

Set-Location ..
git diff --check
git status --short
```

Expected: both suites and builds pass, `git diff --check` prints nothing, and status lists only the uncommitted changelog before its commit.

- [ ] **Step 4: Audit scope from the approved baseline**

Run:

```powershell
git diff --name-only 0e0d463 | Select-String -Pattern '(^|/)(api|services|stores|router|routes|mocks?|fixtures)(/|$)|(^|/)(package-lock.json|pnpm-lock.yaml|yarn.lock)$'
```

Expected: no output. Review `git diff --name-only 0e0d463` and confirm all remaining files belong to this spec, its plan, tests, UI components, views, or changelog.

- [ ] **Step 5: Commit documentation and confirm clean state**

```powershell
git add docs/interaction-upgrade-changelog.md
git commit -m "docs: record accessibility ux polish"
git status --short
```

Expected: commit succeeds and final status is empty.
