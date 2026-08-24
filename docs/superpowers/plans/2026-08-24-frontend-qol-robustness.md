# Frontend Quality-of-Life and Form Robustness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Improve existing H5 and Web form feedback, local draft resilience, empty states, long-list rendering, desktop shortcuts, mobile modal focus restoration, and wide-record layout without changing business APIs or adding modules.

**Architecture:** Keep H5 and Web source ownership separate while applying the same interaction contract. Use small framework-free debounce/checkpoint helpers, existing validators and components, bounded `slice`-based progressive rendering, native keyboard/focus APIs, and CSS grid/overflow fixes; preserve all source arrays, manual remote-save flows, request payloads, and routes.

**Tech Stack:** Vue 3, UniApp H5, Pinia, TypeScript, Vitest, Tailwind-compatible existing CSS architecture, native `localStorage`, native `IntersectionObserver`, native keyboard/focus events.

## Global Constraints

- Implementation baseline is `b0dbe20`; behavioral baseline before design commits is `18afb5a`.
- Follow `docs/superpowers/specs/2026-08-24-frontend-qol-robustness-design.md`.
- No new H5 or Web business page, route, capability, API call shape, request field, mock record, backend pagination, or backend source change.
- Manual remote draft save remains the only operation that calls the draft-save API.
- Existing Chinese UI strings remain byte-for-byte unchanged; only additive helper/status copy is allowed.
- H5 questions remain optional; Web assessment completeness rules remain unchanged.
- Use native APIs and existing dependencies only; do not add form, table, keyboard, or virtual-list libraries.
- Preserve mock mode and backend docking through existing API tests and a changed-path audit.
- Every production behavior starts with a failing test and ends with a focused green test before committing.

## Execution Preflight

Before Task 1, verify `git status --short` is empty, read the execution skills required by the selected handoff mode, and run Impeccable context exactly once:

```powershell
node C:\Users\16102\.codex\skills\impeccable\scripts\context.mjs --target resume-miniprogram/src/pages/resume-form/index.vue
```

Read `C:\Users\16102\.codex\skills\impeccable\reference\harden.md` during execution analysis and `C:\Users\16102\.codex\skills\impeccable\reference\craft-floor.md` immediately before the first UI edit. Do not rerun context.

---

### Task 1: H5 Debounced Local Checkpoint and Resume Field Validation

**Files:**
- Create: `resume-miniprogram/src/utils/debounced-task.ts`
- Create: `resume-miniprogram/src/tests/debounced-task.spec.ts`
- Modify: `resume-miniprogram/src/pages/resume-form/index.vue`
- Modify: `resume-miniprogram/src/tests/validators.spec.ts`
- Modify: `resume-miniprogram/src/tests/interaction.spec.ts`

**Interfaces:**
- Produces `createDebouncedTask(action: () => void, delayMs: number): { schedule(): void; flush(): void; cancel(): void; isPending(): boolean }`.
- Consumes existing `validateResume`, `toValidationErrorMap`, `FormField`, `useResumeStore().checkpoint()`, and manual `saveDraft` flow.
- Produces page-local `localSaveState: "idle" | "saving" | "saved" | "error"`; no caller outside `resume-form` consumes that state.

- [ ] **Step 1: Add failing fake-timer tests for debounce, flush, and cancellation**

Create `resume-miniprogram/src/tests/debounced-task.spec.ts`:

```ts
import { afterEach, describe, expect, it, vi } from "vitest"

import { createDebouncedTask } from "../utils/debounced-task"

afterEach(() => vi.useRealTimers())

describe("createDebouncedTask", () => {
  it("coalesces rapid schedules and runs once after 800ms", () => {
    vi.useFakeTimers()
    const action = vi.fn()
    const task = createDebouncedTask(action, 800)

    task.schedule()
    vi.advanceTimersByTime(500)
    task.schedule()
    vi.advanceTimersByTime(799)
    expect(action).not.toHaveBeenCalled()
    vi.advanceTimersByTime(1)
    expect(action).toHaveBeenCalledTimes(1)
    expect(task.isPending()).toBe(false)
  })

  it("flushes the latest pending action exactly once", () => {
    vi.useFakeTimers()
    const action = vi.fn()
    const task = createDebouncedTask(action, 800)
    task.schedule()
    task.flush()
    vi.runAllTimers()
    expect(action).toHaveBeenCalledTimes(1)
  })

  it("cancels without running", () => {
    vi.useFakeTimers()
    const action = vi.fn()
    const task = createDebouncedTask(action, 800)
    task.schedule()
    task.cancel()
    vi.runAllTimers()
    expect(action).not.toHaveBeenCalled()
  })
})
```

- [ ] **Step 2: Run the new test and verify RED**

Run:

```powershell
cd resume-miniprogram
npm.cmd run test:unit -- src/tests/debounced-task.spec.ts --reporter=dot
```

Expected: FAIL because `../utils/debounced-task` does not exist.

- [ ] **Step 3: Implement the minimal framework-free scheduler**

Create `resume-miniprogram/src/utils/debounced-task.ts`:

```ts
export type DebouncedTask = {
  schedule(): void
  flush(): void
  cancel(): void
  isPending(): boolean
}

export function createDebouncedTask(action: () => void, delayMs: number): DebouncedTask {
  let timer: ReturnType<typeof setTimeout> | null = null

  const cancel = () => {
    if (timer === null) return
    clearTimeout(timer)
    timer = null
  }

  const run = () => {
    timer = null
    action()
  }

  return {
    schedule() {
      cancel()
      timer = setTimeout(run, delayMs)
    },
    flush() {
      if (timer === null) return
      cancel()
      action()
    },
    cancel,
    isPending: () => timer !== null,
  }
}
```

- [ ] **Step 4: Run the debounce tests and verify GREEN**

Run the Step 2 command. Expected: 3 tests pass.

- [ ] **Step 5: Extend failing resume validation and interaction contracts**

In `resume-miniprogram/src/tests/validators.spec.ts`, add a test that asserts the existing required fields map to all four keys:

```ts
it("maps all required resume fields to inline errors", () => {
  const errors = toValidationErrorMap(validateResume(createEmptyResume()))
  expect(Object.keys(errors)).toEqual(expect.arrayContaining([
    "basic.name", "basic.phone", "basic.email", "job.targetRole",
  ]))
})
```

In `resume-miniprogram/src/tests/interaction.spec.ts`, add a static contract that expects:

```ts
it("debounces H5 local checkpoints and maps resume field errors", () => {
  const resumeForm = readFileSync(new URL("../pages/resume-form/index.vue", import.meta.url), "utf8")
  expect(resumeForm).toContain("createDebouncedTask")
  expect(resumeForm).toContain("const localSaveState")
  expect(resumeForm).toContain("checkpointPaused")
  expect(resumeForm).toContain("localCheckpoint.flush()")
  expect(resumeForm).toContain(':error="fieldErrors[\'basic.name\']"')
  expect(resumeForm).toContain(':error="fieldErrors[\'basic.phone\']"')
  expect(resumeForm).toContain(':error="fieldErrors[\'basic.email\']"')
  expect(resumeForm).toContain(':error="fieldErrors[\'job.targetRole\']"')
  expect(resumeForm).not.toContain("if (errors.length) return\n  if (errors.length)")
})
```

- [ ] **Step 6: Run focused H5 tests and verify RED on missing page wiring**

Run:

```powershell
npm.cmd run test:unit -- src/tests/validators.spec.ts src/tests/interaction.spec.ts --reporter=dot
```

Expected: validator assertions pass; interaction contract fails because debounce/status/error props are not wired.

- [ ] **Step 7: Wire the 800ms local checkpoint and field errors into `resume-form`**

In `resume-miniprogram/src/pages/resume-form/index.vue`:

```ts
import { onHide } from "@dcloudio/uni-app"
import { computed, nextTick, onBeforeUnmount, ref, watch } from "vue"
import { createDebouncedTask } from "../../utils/debounced-task"

const localSaveState = ref<"idle" | "saving" | "saved" | "error">("idle")
const validationActive = ref(false)
let checkpointPaused = false
function persistLocalCheckpoint(): void {
  try {
    store.checkpoint()
    localSaveState.value = "saved"
  } catch {
    localSaveState.value = "error"
  }
}
const localCheckpoint = createDebouncedTask(persistLocalCheckpoint, 800)

watch(() => store.draft, () => {
  if (checkpointPaused) return
  localSaveState.value = "saving"
  localCheckpoint.schedule()
}, { deep: true })

watch(resume, () => {
  if (validationActive.value) fieldErrors.value = toValidationErrorMap(validateResume(resume.value))
}, { deep: true })

const flushLocalCheckpoint = () => localCheckpoint.flush()
onHide(flushLocalCheckpoint)
onBeforeUnmount(flushLocalCheckpoint)
```

At the beginning of manual `save()`:

```ts
localCheckpoint.flush()
validationActive.value = true
const errors = validateResume(resume.value)
fieldErrors.value = toValidationErrorMap(errors)
if (errors.length) return
```

Delete the duplicate unreachable `if (errors.length)` branch. Pass each mapped error into its corresponding `FormField`. Add one compact `aria-live="polite"` status line using additive copy:

```vue
<text class="local-save-status" aria-live="polite">
  {{ localSaveState === "saving" ? "正在保存到本机" : localSaveState === "saved" ? "已保存到本机" : localSaveState === "error" ? "本机自动保存失败，请手动保存" : "" }}
</text>
```

Keep existing button and toast strings unchanged.

In the successful remote-save branch, pause the watcher around the existing returned-ID assignment, then replace the direct post-request checkpoint:

```ts
checkpointPaused = true
try {
  store.draft.id = saved.id
  await nextTick()
} finally {
  checkpointPaused = false
}
localCheckpoint.cancel()
persistLocalCheckpoint()
```

In the failed remote-save branch, replace the direct local fallback checkpoint with only the final two lines above. This keeps the existing local fallback but prevents the remote response mutation from leaving a second delayed write behind.

- [ ] **Step 8: Run focused and full H5 tests**

Run:

```powershell
npm.cmd run test:unit -- src/tests/debounced-task.spec.ts src/tests/validators.spec.ts src/tests/interaction.spec.ts --reporter=dot
npm.cmd run test:unit -- --reporter=dot
```

Expected: focused tests and the complete H5 suite pass.

- [ ] **Step 9: Commit Task 1**

From repository root:

```powershell
git add resume-miniprogram/src/utils/debounced-task.ts resume-miniprogram/src/tests/debounced-task.spec.ts resume-miniprogram/src/tests/validators.spec.ts resume-miniprogram/src/tests/interaction.spec.ts resume-miniprogram/src/pages/resume-form/index.vue
git commit -m "feat(h5): improve local draft form resilience"
```

---

### Task 2: H5 Search/Assessment Feedback and Modal Focus Restoration

**Files:**
- Create: `resume-miniprogram/src/utils/focus-restore.ts`
- Create: `resume-miniprogram/src/tests/focus-restore.spec.ts`
- Modify: `resume-miniprogram/src/pages/job-search/index.vue`
- Modify: `resume-miniprogram/src/pages/career-assessment/index.vue`
- Modify: `resume-miniprogram/src/pages/resume-editor/index.vue`
- Modify: `resume-miniprogram/src/tests/interaction.spec.ts`

**Interfaces:**
- Produces `captureFocusRestore(documentLike?: DocumentLike): () => void`; it never imports DOM globals at module evaluation time.
- Job search produces page-local `roleFieldError` separate from existing API `error`.
- Career assessment produces page-local `stepHint`; it never blocks `goNext()` or `submit()`.

- [ ] **Step 1: Write failing focus-restoration tests**

Create `resume-miniprogram/src/tests/focus-restore.spec.ts`:

```ts
import { describe, expect, it, vi } from "vitest"

import { captureFocusRestore } from "../utils/focus-restore"

describe("captureFocusRestore", () => {
  it("is a no-op without an H5 document", () => {
    expect(() => captureFocusRestore(undefined)()).not.toThrow()
  })

  it("restores a still-connected focusable element", () => {
    const focus = vi.fn()
    const restore = captureFocusRestore({ activeElement: { isConnected: true, focus } })
    restore()
    expect(focus).toHaveBeenCalledTimes(1)
  })

  it("does not focus a removed element", () => {
    const focus = vi.fn()
    const restore = captureFocusRestore({ activeElement: { isConnected: false, focus } })
    restore()
    expect(focus).not.toHaveBeenCalled()
  })
})
```

- [ ] **Step 2: Run the focus test and verify RED**

Run:

```powershell
cd resume-miniprogram
npm.cmd run test:unit -- src/tests/focus-restore.spec.ts --reporter=dot
```

Expected: FAIL because `focus-restore.ts` does not exist.

- [ ] **Step 3: Implement the guarded focus helper**

Create `resume-miniprogram/src/utils/focus-restore.ts`:

```ts
type Focusable = { isConnected?: boolean; focus?: () => void }
type DocumentLike = { activeElement?: Focusable | null }

export function captureFocusRestore(documentLike?: DocumentLike): () => void {
  const active = documentLike?.activeElement
  return () => {
    if (!active || active.isConnected === false) return
    active.focus?.()
  }
}
```

Pass `typeof document === "undefined" ? undefined : document` from H5 callers so MiniProgram builds never evaluate an unguarded DOM access.

- [ ] **Step 4: Run focus tests and verify GREEN**

Run the Step 2 command. Expected: 3 tests pass.

- [ ] **Step 5: Add failing interaction contracts for form feedback and focus**

Extend `resume-miniprogram/src/tests/interaction.spec.ts` with assertions for:

```ts
it("separates H5 field feedback and restores focus after native modals", () => {
  const jobSearch = readFileSync(new URL("../pages/job-search/index.vue", import.meta.url), "utf8")
  const assessment = readFileSync(new URL("../pages/career-assessment/index.vue", import.meta.url), "utf8")
  const editor = readFileSync(new URL("../pages/resume-editor/index.vue", import.meta.url), "utf8")
  expect(jobSearch).toContain('const roleFieldError = ref("")')
  expect(jobSearch).toContain(':aria-invalid="Boolean(roleFieldError)"')
  expect(jobSearch).toContain('id="job-role-error"')
  expect(assessment).toContain('const stepHint = ref("")')
  expect(assessment).toContain('aria-live="polite"')
  expect(editor).toContain("captureFocusRestore")
  expect(editor).toContain("complete: restoreFocus")
})
```

Run `npm.cmd run test:unit -- src/tests/interaction.spec.ts --reporter=dot` and verify RED.

- [ ] **Step 6: Separate field validation from API errors in H5 job search**

In `resume-miniprogram/src/pages/job-search/index.vue`:

- Add `roleFieldError`.
- Move the existing empty-role string `请输入岗位名称，或从下方联想岗位中选择。` from global `error` to `roleFieldError` without changing the string.
- Clear stale global `error` when this empty-input validation branch runs; later network failures continue to populate only global `error`.
- In the existing `watch(roleName, ...)`, clear `roleFieldError` when `value.trim()` is non-empty before refreshing suggestions.
- Add `aria-invalid`, `aria-describedby="job-role-error"`, and an inline `ui-error-tip` under the input.
- Keep API failures in the existing global `error` surface.

- [ ] **Step 7: Add non-blocking H5 assessment guidance**

In `resume-miniprogram/src/pages/career-assessment/index.vue`:

```ts
const stepHint = ref("")

function answer(key: string, value: number) {
  store.answer(key, value)
  stepHint.value = ""
}

function currentStepHasAnswer(): boolean {
  return currentQuestions.value.some((question) => Number.isInteger(store.answers[question.key]))
}

function goNext() {
  stepHint.value = currentStepHasAnswer() ? "" : "本步骤尚未作答，可继续并稍后补充"
  if (currentStep.value < steps.length - 1) currentStep.value += 1
  else void submit()
}
```

Render the hint near the button row with `class="ui-error-tip" aria-live="polite"`. Do not return early and do not change `submitAssessment` arguments.

- [ ] **Step 8: Restore H5 input focus after existing resume modals**

In both `applyImportPreview()` and `restoreVersion()` in `resume-miniprogram/src/pages/resume-editor/index.vue`:

```ts
const restoreFocus = captureFocusRestore(
  typeof document === "undefined" ? undefined : document,
)
uni.showModal({
  // existing title/content/success stay unchanged
  complete: restoreFocus,
})
```

Do not change confirm/cancel behavior or asynchronous restore logic.

- [ ] **Step 9: Run focused and full H5 tests, then build**

```powershell
npm.cmd run test:unit -- src/tests/focus-restore.spec.ts src/tests/interaction.spec.ts --reporter=dot
npm.cmd run test:unit -- --reporter=dot
npm.cmd run build:h5
```

Expected: all tests pass and the H5 compiler reports `DONE Build complete`.

- [ ] **Step 10: Commit Task 2**

From repository root:

```powershell
git add resume-miniprogram/src/utils/focus-restore.ts resume-miniprogram/src/tests/focus-restore.spec.ts resume-miniprogram/src/tests/interaction.spec.ts resume-miniprogram/src/pages/job-search/index.vue resume-miniprogram/src/pages/career-assessment/index.vue resume-miniprogram/src/pages/resume-editor/index.vue
git commit -m "fix(h5): clarify form feedback and modal focus"
```

---

### Task 3: H5 Progressive Lists and Additive Empty States

**Files:**
- Create: `resume-miniprogram/src/composables/useIncrementalList.ts`
- Create: `resume-miniprogram/src/tests/incremental-list.spec.ts`
- Modify: `resume-miniprogram/src/pages/drafts/index.vue`
- Modify: `resume-miniprogram/src/pages/applications/index.vue`
- Modify: `resume-miniprogram/src/pages/evidence/index.vue`
- Modify: `resume-miniprogram/src/pages/job-collection/index.vue`
- Modify: `resume-miniprogram/src/pages/job-search/index.vue`
- Modify: `resume-miniprogram/src/App.vue`
- Modify: `resume-miniprogram/src/tests/interaction.spec.ts`

**Interfaces:**
- Produces `useIncrementalList<T>(source: Readonly<Ref<readonly T[]>>, initial?: number, step?: number)` returning `visibleItems`, `hasMore`, `showMore()`, and `reset()`.
- Default H5 threshold is 20/20.
- Consumes existing source refs/computed refs; page edit/delete/filter logic continues to use original arrays.

- [ ] **Step 1: Write failing incremental-list tests**

Create `resume-miniprogram/src/tests/incremental-list.spec.ts`:

```ts
import { ref } from "vue"
import { describe, expect, it } from "vitest"

import { useIncrementalList } from "../composables/useIncrementalList"

describe("useIncrementalList for H5", () => {
  it("renders 20 records and advances by 20 without exceeding length", () => {
    const source = ref(Array.from({ length: 45 }, (_, index) => index))
    const list = useIncrementalList(source)
    expect(list.visibleItems.value).toHaveLength(20)
    list.showMore()
    expect(list.visibleItems.value).toHaveLength(40)
    list.showMore()
    expect(list.visibleItems.value).toHaveLength(45)
    expect(list.hasMore.value).toBe(false)
  })

  it("resets after a refresh or filter change", () => {
    const source = ref(Array.from({ length: 60 }, (_, index) => index))
    const list = useIncrementalList(source)
    list.showMore()
    list.reset()
    expect(list.visibleItems.value).toHaveLength(20)
  })
})
```

- [ ] **Step 2: Run the new test and verify RED**

```powershell
cd resume-miniprogram
npm.cmd run test:unit -- src/tests/incremental-list.spec.ts --reporter=dot
```

Expected: FAIL because the composable does not exist.

- [ ] **Step 3: Implement the H5 composable**

Create `resume-miniprogram/src/composables/useIncrementalList.ts`:

```ts
import { computed, ref, type Ref } from "vue"

export function useIncrementalList<T>(
  source: Readonly<Ref<readonly T[]>>,
  initial = 20,
  step = 20,
) {
  const limit = ref(initial)
  const visibleItems = computed(() => source.value.slice(0, limit.value))
  const hasMore = computed(() => limit.value < source.value.length)
  const showMore = () => { limit.value = Math.min(limit.value + step, source.value.length) }
  const reset = () => { limit.value = initial }
  return { visibleItems, hasMore, showMore, reset }
}
```

- [ ] **Step 4: Run incremental-list tests and verify GREEN**

Run the Step 2 command. Expected: 2 tests pass.

- [ ] **Step 5: Add failing H5 page contracts**

Extend `resume-miniprogram/src/tests/interaction.spec.ts` to require:

```ts
it("bounds H5 long lists and adds additive empty states", () => {
  const app = readFileSync(new URL("../App.vue", import.meta.url), "utf8")
  const drafts = readFileSync(new URL("../pages/drafts/index.vue", import.meta.url), "utf8")
  const applications = readFileSync(new URL("../pages/applications/index.vue", import.meta.url), "utf8")
  const evidence = readFileSync(new URL("../pages/evidence/index.vue", import.meta.url), "utf8")
  const collection = readFileSync(new URL("../pages/job-collection/index.vue", import.meta.url), "utf8")
  const jobSearch = readFileSync(new URL("../pages/job-search/index.vue", import.meta.url), "utf8")
  expect(drafts).toContain("useIncrementalList")
  expect(applications).toContain("useIncrementalList")
  expect(evidence).toContain("useIncrementalList")
  expect(collection).toContain("useIncrementalList")
  expect(drafts).toContain('@scrolltolower="showMore"')
  expect(applications).toContain('@scrolltolower="showMore"')
  expect(drafts).toContain("progressive-scroll-page")
  expect(app).toContain("contain-intrinsic-size: auto 180rpx")
  expect(app).toContain(".progressive-scroll-page")
  expect(jobSearch).toContain("job-empty-state")
  expect(drafts).toContain("本机填写中的内容也会自动保留。")
  expect(drafts).toContain('/pages/resume-form/index')
  expect(applications).toContain("可先查询岗位，再回到这里记录进度。")
  expect(applications).toContain('/pages/job-search/index')
  expect(jobSearch).toContain("暂未找到匹配岗位，可换一个更具体的岗位名称。")
})
```

Run `npm.cmd run test:unit -- src/tests/interaction.spec.ts --reporter=dot` and verify RED.

- [ ] **Step 6: Wire progressive rendering into H5 long lists**

For drafts, evidence, and job collection, pass `drafts`, `evidence`, and `favorites` respectively to `useIncrementalList`. Replace only the template `v-for` source with `renderedItems`, add `progressive-scroll-page` and `@scrolltolower="showMore"` to the existing `scroll-view`, and call `resetVisibleItems()` immediately after assigning a successful refreshed source array.

For applications, pass existing `visibleApplications` to the composable, render `renderedItems`, call `resetVisibleItems()` after a successful load, and reset the rendered window whenever either filter changes:

```ts
watch([selectedStatus, interviewDate], () => resetVisibleItems())
```

Keep edit/delete/status operations pointed at the original application records.

Use the exact shared names in every page:

```ts
// drafts/index.vue
const {
  visibleItems: renderedItems,
  hasMore,
  showMore,
  reset: resetVisibleItems,
} = useIncrementalList(drafts)

// applications/index.vue
const {
  visibleItems: renderedItems,
  hasMore,
  showMore,
  reset: resetVisibleItems,
} = useIncrementalList(visibleApplications)

// evidence/index.vue
const {
  visibleItems: renderedItems,
  hasMore,
  showMore,
  reset: resetVisibleItems,
} = useIncrementalList(evidence)

// job-collection/index.vue
const {
  visibleItems: renderedItems,
  hasMore,
  showMore,
  reset: resetVisibleItems,
} = useIncrementalList(favorites)
```

Render a small loading-more hint only while `hasMore` is true; do not alter list records or API query parameters.

Use this template shape after each rendered list so the same `scrolltolower` event can reveal the next chunk:

```vue
<text v-if="hasMore" class="progressive-list-hint">继续下滑显示更多</text>
```

- [ ] **Step 7: Add empty-state helper lines and existing actions without rewriting text**

- `drafts/index.vue`: retain `No resume drafts yet` and `Your saved resume history will appear here.`; add `本机填写中的内容也会自动保留。` and a `前往填写简历` button that navigates to `/pages/resume-form/index`.
- `applications/index.vue`: retain `还没有投递计划。确认岗位与公司后，在上方手动保存第一条记录。`; add a CSS-only document illustration, `可先查询岗位，再回到这里记录进度。`, and a `查询岗位` button that navigates to `/pages/job-search/index`.
- `job-search/index.vue`: under the condition below, render `job-empty-state` with `暂未找到匹配岗位，可换一个更具体的岗位名称。` and preserve all existing search strings:

```vue
<view
  v-if="consultation.stage === 'role-entry' && roleName.trim() && !suggestionLoading && !visibleSuggestions.length && !jobConsultations.length"
  class="job-empty-state"
>
  <text class="job-empty-icon" aria-hidden="true">⌕</text>
  <text>暂未找到匹配岗位，可换一个更具体的岗位名称。</text>
</view>
```

Use direct handlers for the two existing routes:

```ts
// drafts/index.vue
const openResumeForm = () => uni.navigateTo({ url: "/pages/resume-form/index" })

// applications/index.vue
const openJobSearch = () => uni.navigateTo({ url: "/pages/job-search/index" })
```

For the applications empty state, reuse the drafts page's three-line document motif as local CSS-only markup; do not import an image:

```vue
<view class="empty-illustration" aria-hidden="true"><view /><view /><view /></view>
```

Keep illustration dimensions fixed so the helper/action does not shift when text wraps. Add these scoped styles to the pages that use them; duplicate only the small illustration rule across the two scoped style blocks:

```css
.empty-illustration {
  display: flex;
  flex-direction: column;
  gap: 8rpx;
  width: 116rpx;
  margin: 0 auto 20rpx;
  padding: 20rpx;
  background: #eef6ff;
  border: 1rpx solid #d4e8ff;
  border-radius: 18rpx;
}
.empty-illustration view { height: 9rpx; background: #9fc8f7; border-radius: 999rpx; }
.empty-illustration view:nth-child(2) { width: 76%; }
.empty-illustration view:nth-child(3) { width: 54%; }
.empty-helper { display: block; margin-top: 10rpx; color: #86909c; font-size: 23rpx; }
.empty-action { margin: 20rpx auto 0; color: #fff; background: #1677ff; font-size: 24rpx; }
.job-empty-state { display: flex; align-items: center; gap: 12rpx; margin-top: 14rpx; color: #64748b; font-size: 23rpx; line-height: 1.55; }
.job-empty-icon { flex: 0 0 38rpx; font-size: 32rpx; text-align: center; }
```

Use existing `empty-illustration`, `empty-state`, primary button, and `ui-error-tip` patterns. Do not add a route or asset.

- [ ] **Step 8: Make H5 progressive scroll bounded and tune containment**

In `resume-miniprogram/src/App.vue`, add the bounded scroll/hint classes and change the existing long-list containment estimate:

```css
.progressive-scroll-page {
  height: 100vh;
  box-sizing: border-box;
}
.progressive-list-hint {
  display: block;
  padding: 24rpx 0 12rpx;
  color: #86909c;
  font-size: 22rpx;
  text-align: center;
}
.ui-long-list-item {
  content-visibility: auto;
  contain: layout paint style;
  contain-intrinsic-size: auto 180rpx;
}
```

This is an estimate, not a data threshold; the 20/20 composable owns the progressive threshold.

- [ ] **Step 9: Run focused/full H5 tests and build**

```powershell
npm.cmd run test:unit -- src/tests/incremental-list.spec.ts src/tests/interaction.spec.ts --reporter=dot
npm.cmd run test:unit -- --reporter=dot
npm.cmd run build:h5
```

- [ ] **Step 10: Commit Task 3**

From repository root:

```powershell
git add resume-miniprogram/src/composables/useIncrementalList.ts resume-miniprogram/src/tests/incremental-list.spec.ts resume-miniprogram/src/tests/interaction.spec.ts resume-miniprogram/src/pages/drafts/index.vue resume-miniprogram/src/pages/applications/index.vue resume-miniprogram/src/pages/evidence/index.vue resume-miniprogram/src/pages/job-collection/index.vue resume-miniprogram/src/pages/job-search/index.vue resume-miniprogram/src/App.vue
git commit -m "perf(h5): bound long-list rendering"
```

---

### Task 4: Web Draft Checkpoint, Debounce, and Resume Validation

**Files:**
- Create: `web-frontend/src/lib/debounced-task.ts`
- Create: `web-frontend/src/lib/draft-checkpoint.ts`
- Create: `web-frontend/src/lib/resume-validation.ts`
- Create: `web-frontend/src/tests/debounced-task.spec.ts`
- Create: `web-frontend/src/tests/draft-checkpoint.spec.ts`
- Create: `web-frontend/src/tests/resume-validation.spec.ts`
- Modify: `web-frontend/src/views/ResumeEditorView.vue`
- Modify: `web-frontend/src/styles/base.css`
- Modify: `web-frontend/src/tests/interaction.spec.ts`

**Interfaces:**
- Produces package-local `createDebouncedTask(action: () => void, delayMs: number): { schedule(): void; flush(): void; cancel(): void; isPending(): boolean }`.
- `readDraftCheckpoint(storage, draftId, serverUpdatedAt): DraftRecord | null`.
- `writeDraftCheckpoint(storage, draft, savedAt?): void` and `clearDraftCheckpoint(storage, draftId): void`.
- `validateDraft(draft: DraftRecord): Record<string, string>` returns keys `jobTitle`, `basic.name`, `basic.phone`, `basic.email`, and `job.targetRole`.

- [ ] **Step 1: Write failing Web helper tests**

Create `web-frontend/src/tests/debounced-task.spec.ts`:

```ts
import { afterEach, describe, expect, it, vi } from "vitest"
import { createDebouncedTask } from "../lib/debounced-task"

afterEach(() => vi.useRealTimers())

describe("createDebouncedTask for Web", () => {
  it("coalesces rapid schedules into one 800ms action", () => {
    vi.useFakeTimers()
    const action = vi.fn()
    const task = createDebouncedTask(action, 800)
    task.schedule()
    vi.advanceTimersByTime(500)
    task.schedule()
    vi.advanceTimersByTime(799)
    expect(action).not.toHaveBeenCalled()
    vi.advanceTimersByTime(1)
    expect(action).toHaveBeenCalledTimes(1)
  })

  it("flushes once and cancels the timer", () => {
    vi.useFakeTimers()
    const action = vi.fn()
    const task = createDebouncedTask(action, 800)
    task.schedule()
    task.flush()
    vi.runAllTimers()
    expect(action).toHaveBeenCalledTimes(1)
    expect(task.isPending()).toBe(false)
  })

  it("cancels without running", () => {
    vi.useFakeTimers()
    const action = vi.fn()
    const task = createDebouncedTask(action, 800)
    task.schedule()
    task.cancel()
    vi.runAllTimers()
    expect(action).not.toHaveBeenCalled()
    expect(task.isPending()).toBe(false)
  })
})
```

Create `web-frontend/src/tests/draft-checkpoint.spec.ts` with an in-memory store:

```ts
import { beforeEach, describe, expect, it } from "vitest"
import {
  checkpointKey,
  clearDraftCheckpoint,
  readDraftCheckpoint,
  writeDraftCheckpoint,
} from "../lib/draft-checkpoint"
import type { DraftRecord } from "../lib/drafts"

const values = new Map<string, string>()
const storage = {
  getItem: (key: string) => values.get(key) ?? null,
  setItem: (key: string, value: string) => { values.set(key, value) },
  removeItem: (key: string) => { values.delete(key) },
}
const draft = { id: "d-1", updatedAt: "2026-08-24T10:00:00Z" } as DraftRecord

beforeEach(() => values.clear())

it("restores only a newer matching checkpoint", () => {
  writeDraftCheckpoint(storage, draft, Date.parse("2026-08-24T09:00:00Z"))
  expect(readDraftCheckpoint(storage, "d-1", "2026-08-24T10:00:00Z")).toBeNull()

  writeDraftCheckpoint(storage, draft, Date.parse("2026-08-24T11:00:00Z"))
  expect(readDraftCheckpoint(storage, "d-1", "2026-08-24T10:00:00Z")).toMatchObject({ id: "d-1" })
})

it("ignores mismatched and malformed checkpoint data", () => {
  storage.setItem(checkpointKey("d-1"), JSON.stringify({
    version: 1,
    draftId: "other",
    savedAt: Date.parse("2026-08-24T11:00:00Z"),
    draft,
  }))
  expect(readDraftCheckpoint(storage, "d-1", "2026-08-24T10:00:00Z")).toBeNull()

  storage.setItem(checkpointKey("d-1"), "not-json")
  expect(readDraftCheckpoint(storage, "d-1", "2026-08-24T10:00:00Z")).toBeNull()

  storage.setItem(checkpointKey("d-1"), JSON.stringify({
    version: 1,
    draftId: "d-1",
    savedAt: Date.parse("2026-08-24T11:00:00Z"),
    draft: { id: "d-1" },
  }))
  expect(readDraftCheckpoint(storage, "d-1", "2026-08-24T10:00:00Z")).toBeNull()
})

it("clears a saved checkpoint after remote save", () => {
  writeDraftCheckpoint(storage, draft)
  clearDraftCheckpoint(storage, "d-1")
  expect(storage.getItem(checkpointKey("d-1"))).toBeNull()
})
```

Create `web-frontend/src/tests/resume-validation.spec.ts`:

```ts
import { describe, expect, it } from "vitest"
import { validateDraft } from "../lib/resume-validation"
import type { DraftRecord } from "../lib/drafts"

const validDraft = (): DraftRecord => ({
  id: "d-1",
  jobTitle: "数据工程师简历",
  templateId: "business",
  resume: {
    version: 1,
    basic: { name: "张三", phone: "13800138000", email: "zhang@example.com", city: "上海" },
    job: { targetRole: "数据工程师", expectedSalary: "", employmentType: "" },
    education: [], employment: [], projects: [],
    skills: { skills: [], certificates: [] }, selfEvaluation: "",
    sectionVisibility: { basic: true, job: true, education: true, employment: true, projects: true, skills: true, selfEvaluation: true },
  },
  jobIntelligence: null,
  createdAt: "2026-08-24T09:00:00Z",
  updatedAt: "2026-08-24T10:00:00Z",
})

describe("validateDraft", () => {
  it("returns no errors for a valid draft", () => {
    expect(validateDraft(validDraft())).toEqual({})
  })

  it("returns every aligned required-field key", () => {
    const draft = validDraft()
    draft.jobTitle = ""
    draft.resume.basic = { name: "", phone: "123", email: "bad", city: "" }
    draft.resume.job.targetRole = ""
    expect(Object.keys(validateDraft(draft))).toEqual(expect.arrayContaining([
      "jobTitle", "basic.name", "basic.phone", "basic.email", "job.targetRole",
    ]))
  })
})
```

- [ ] **Step 2: Run helper tests and verify RED**

```powershell
cd web-frontend
npm.cmd test -- src/tests/debounced-task.spec.ts src/tests/draft-checkpoint.spec.ts src/tests/resume-validation.spec.ts --reporter=dot
```

Expected: FAIL because all three helper modules are missing.

- [ ] **Step 3: Implement the Web debounce helper**

Create `web-frontend/src/lib/debounced-task.ts`:

```ts
export type DebouncedTask = {
  schedule(): void
  flush(): void
  cancel(): void
  isPending(): boolean
}

export function createDebouncedTask(action: () => void, delayMs: number): DebouncedTask {
  let timer: ReturnType<typeof setTimeout> | null = null
  const cancel = () => {
    if (timer === null) return
    clearTimeout(timer)
    timer = null
  }
  const run = () => { timer = null; action() }
  return {
    schedule() { cancel(); timer = setTimeout(run, delayMs) },
    flush() { if (timer !== null) { cancel(); action() } },
    cancel,
    isPending: () => timer !== null,
  }
}
```

- [ ] **Step 4: Implement the versioned Web checkpoint helper**

Create `web-frontend/src/lib/draft-checkpoint.ts`:

```ts
import type { DraftRecord } from "./drafts"

export type StorageLike = Pick<Storage, "getItem" | "setItem" | "removeItem">
type Envelope = { version: 1; draftId: string; savedAt: number; draft: DraftRecord }

export const checkpointKey = (draftId: string) => `resume_web_checkpoint:${draftId}`

export function writeDraftCheckpoint(storage: StorageLike, draft: DraftRecord, savedAt = Date.now()): void {
  const envelope: Envelope = { version: 1, draftId: draft.id, savedAt, draft }
  storage.setItem(checkpointKey(draft.id), JSON.stringify(envelope))
}

export function readDraftCheckpoint(
  storage: StorageLike,
  draftId: string,
  serverUpdatedAt: string,
): DraftRecord | null {
  try {
    const raw = storage.getItem(checkpointKey(draftId))
    if (!raw) return null
    const parsed = JSON.parse(raw) as Partial<Envelope>
    const serverTime = Date.parse(serverUpdatedAt)
    if (parsed.version !== 1 || parsed.draftId !== draftId || !Number.isFinite(parsed.savedAt)) return null
    if (Number.isFinite(serverTime) && parsed.savedAt! <= serverTime) return null
    if (!parsed.draft || parsed.draft.id !== draftId) return null
    if (!parsed.draft.resume?.basic || !parsed.draft.resume?.job) return null
    return parsed.draft
  } catch {
    return null
  }
}

export function clearDraftCheckpoint(storage: StorageLike, draftId: string): void {
  storage.removeItem(checkpointKey(draftId))
}
```

- [ ] **Step 5: Implement aligned Web draft validation**

Create `web-frontend/src/lib/resume-validation.ts` with the same phone/email regex as H5 and additive messages:

```ts
import type { DraftRecord } from "./drafts"

const PHONE_PATTERN = /^1\d{10}$/
const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

export function validateDraft(draft: DraftRecord): Record<string, string> {
  const errors: Record<string, string> = {}
  if (!draft.jobTitle.trim()) errors.jobTitle = "请填写草稿名称"
  if (!draft.resume.basic.name.trim()) errors["basic.name"] = "请填写姓名"
  if (!PHONE_PATTERN.test(draft.resume.basic.phone.trim())) errors["basic.phone"] = "请输入有效的手机号码"
  if (!EMAIL_PATTERN.test(draft.resume.basic.email.trim())) errors["basic.email"] = "请输入有效的邮箱地址"
  if (!draft.resume.job.targetRole.trim()) errors["job.targetRole"] = "请填写期望岗位"
  return errors
}
```

- [ ] **Step 6: Run helper tests and verify GREEN**

Run the Step 2 command. Expected: all new helper tests pass.

- [ ] **Step 7: Add a failing ResumeEditor interaction contract**

In `web-frontend/src/tests/interaction.spec.ts`, assert:

```ts
it("wires local checkpoint and inline validation into the resume editor", () => {
  const editor = readFileSync(new URL("../views/ResumeEditorView.vue", import.meta.url), "utf8")
  expect(editor).toContain("readDraftCheckpoint")
  expect(editor).toContain("writeDraftCheckpoint")
  expect(editor).toContain("createDebouncedTask")
  expect(editor).toContain("validateDraft")
  expect(editor).toContain("local-save-status")
  expect(editor).toContain("localCheckpoint.flush()")
  expect(editor).toContain("clearDraftCheckpoint")
  expect(editor).toContain("checkpointPaused")
  expect(editor).toContain('aria-live="polite"')
})
```

Run the interaction test and verify RED.

- [ ] **Step 8: Wire checkpoint hydration, autosave, and inline validation**

In `web-frontend/src/views/ResumeEditorView.vue`:

- Add `fieldErrors`, `validationActive`, `localSaveState`, and `hydrated` refs.
- Add a non-reactive `checkpointPaused` flag used only around server hydration/save replacement.
- Build an 800ms `localCheckpoint` scheduler that calls `writeDraftCheckpoint(window.localStorage, draft.value)` inside `try/catch` and sets saved/error status.
- Import `nextTick`; in `load()`, read the server draft, replace it with `readDraftCheckpoint(...) || serverDraft`, then `await nextTick()` before setting `hydrated = true` so initial hydration never schedules an autosave.
- Deep-watch `draft`; when hydrated and not `checkpointPaused`, set status to saving and schedule. In the same callback, when validation is active and the draft exists, replace `fieldErrors` with `validateDraft(currentDraft)` so corrected fields clear immediately.
- On unmount, flush the pending checkpoint.
- At manual save start, flush the checkpoint, clear stale API `error`, activate validation, compute errors, and return before the existing API call when errors exist.
- On successful API save, cancel the pending local task, set `checkpointPaused = true`, assign the returned server draft, and `await nextTick()`. Clear the checkpoint in a nested storage-only `try/catch`, setting only `localSaveState = "error"` if storage fails; reset `checkpointPaused = false` in that nested `finally`. Then retain the existing `emit("saved", saved)` and do not alter the payload mapper. A local-storage exception must not enter the existing remote-save `catch` or replace its API error state.
- Add field-level `small.form-error`, `aria-invalid`, and `aria-describedby` for the five validated inputs.
- Add a compact `local-save-status` live region; do not change existing headings/button/error strings.

Use the additive live-region labels `正在保存到本机`, `已保存到本机`, and `本机自动保存失败，请手动保存` for saving, saved, and error states respectively.

Extend the existing `.form-error` rule in `base.css` rather than adding a duplicate, then add `.local-save-status`:

```css
.form-error { display: block; margin-top: 6px; color: var(--danger); font-size: 12px; line-height: 1.45; }
.local-save-status { min-height: 18px; color: var(--muted); font-size: 12px; }
```

- [ ] **Step 9: Run focused/full Web tests and build**

```powershell
npm.cmd test -- src/tests/debounced-task.spec.ts src/tests/draft-checkpoint.spec.ts src/tests/resume-validation.spec.ts src/tests/interaction.spec.ts --reporter=dot
npm.cmd test -- --reporter=dot
npm.cmd run build
```

- [ ] **Step 10: Commit Task 4**

From repository root:

```powershell
git add web-frontend/src/lib/debounced-task.ts web-frontend/src/lib/draft-checkpoint.ts web-frontend/src/lib/resume-validation.ts web-frontend/src/tests/debounced-task.spec.ts web-frontend/src/tests/draft-checkpoint.spec.ts web-frontend/src/tests/resume-validation.spec.ts web-frontend/src/tests/interaction.spec.ts web-frontend/src/views/ResumeEditorView.vue web-frontend/src/styles/base.css
git commit -m "feat(web): add resilient local draft checkpoint"
```

---

### Task 5: Web Shortcuts and Inline Search/Assessment Feedback

**Files:**
- Create: `web-frontend/src/lib/keyboard-shortcuts.ts`
- Create: `web-frontend/src/tests/keyboard-shortcuts.spec.ts`
- Modify: `web-frontend/src/views/ResumeEditorView.vue`
- Modify: `web-frontend/src/views/ApplicationsView.vue`
- Modify: `web-frontend/src/views/JobsView.vue`
- Modify: `web-frontend/src/views/AssessmentView.vue`
- Modify: `web-frontend/src/components/AssessmentQuestionCard.vue`
- Modify: `web-frontend/src/styles/base.css`
- Modify: `web-frontend/src/tests/interaction.spec.ts`

**Interfaces:**
- Produces `resolveWorkspaceShortcut(event): "save" | "back" | "close" | null`.
- Resume editor consumes `save` and `back`; Applications consumes `close`.
- Jobs produces page-local `roleFieldError`; AssessmentQuestionCard consumes new `invalid?: boolean` prop.

- [ ] **Step 1: Write failing shortcut resolution tests**

Create `web-frontend/src/tests/keyboard-shortcuts.spec.ts`:

```ts
import { describe, expect, it } from "vitest"
import { resolveWorkspaceShortcut } from "../lib/keyboard-shortcuts"

const key = (overrides: Partial<KeyboardEvent>) => ({
  key: "", ctrlKey: false, metaKey: false, altKey: false, isComposing: false,
  ...overrides,
}) as KeyboardEvent

describe("resolveWorkspaceShortcut", () => {
  it("maps save, back, and close commands", () => {
    expect(resolveWorkspaceShortcut(key({ key: "s", ctrlKey: true }))).toBe("save")
    expect(resolveWorkspaceShortcut(key({ key: "S", metaKey: true }))).toBe("save")
    expect(resolveWorkspaceShortcut(key({ key: "ArrowLeft", altKey: true }))).toBe("back")
    expect(resolveWorkspaceShortcut(key({ key: "Escape" }))).toBe("close")
  })

  it("ignores IME composition and unrelated keys", () => {
    expect(resolveWorkspaceShortcut(key({ key: "s", ctrlKey: true, isComposing: true }))).toBeNull()
    expect(resolveWorkspaceShortcut(key({ key: "s" }))).toBeNull()
  })
})
```

- [ ] **Step 2: Run shortcut tests and verify RED**

```powershell
cd web-frontend
npm.cmd test -- src/tests/keyboard-shortcuts.spec.ts --reporter=dot
```

Expected: FAIL because the helper does not exist.

- [ ] **Step 3: Implement the shortcut resolver**

Create `web-frontend/src/lib/keyboard-shortcuts.ts`:

```ts
export type WorkspaceShortcut = "save" | "back" | "close"

export function resolveWorkspaceShortcut(event: KeyboardEvent): WorkspaceShortcut | null {
  if (event.isComposing) return null
  if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "s") return "save"
  if (event.altKey && event.key === "ArrowLeft") return "back"
  if (event.key === "Escape") return "close"
  return null
}
```

- [ ] **Step 4: Run shortcut tests and verify GREEN**

Run the Step 2 command. Expected: 2 tests pass.

- [ ] **Step 5: Add failing component contracts**

Extend `web-frontend/src/tests/interaction.spec.ts`:

```ts
it("wires scoped shortcuts and inline business-form feedback", () => {
  const editor = readFileSync(new URL("../views/ResumeEditorView.vue", import.meta.url), "utf8")
  const applications = readFileSync(new URL("../views/ApplicationsView.vue", import.meta.url), "utf8")
  const jobs = readFileSync(new URL("../views/JobsView.vue", import.meta.url), "utf8")
  const assessment = readFileSync(new URL("../views/AssessmentView.vue", import.meta.url), "utf8")
  const questionCard = readFileSync(new URL("../components/AssessmentQuestionCard.vue", import.meta.url), "utf8")

  expect(editor).toContain("resolveWorkspaceShortcut")
  expect(editor).toContain('window.addEventListener("keydown"')
  expect(editor).toContain('window.removeEventListener("keydown"')
  expect(applications).toContain("resolveWorkspaceShortcut")
  expect(jobs).toContain('const roleFieldError = ref("")')
  expect(jobs).toContain('id="jobs-role-error"')
  expect(assessment).toContain(':invalid="validationActive && !Number.isInteger(answers[question.key])"')
  expect(questionCard).toContain(':aria-invalid="invalid || undefined"')
})
```

Run the interaction test and verify RED.

- [ ] **Step 6: Register scoped shortcuts with existing guards**

In `ResumeEditorView.vue`, register one `keydown` handler on mount and remove it on unmount:

```ts
function handleShortcut(event: KeyboardEvent): void {
  const shortcut = resolveWorkspaceShortcut(event)
  if (shortcut === "save") {
    event.preventDefault()
    if (!saving.value) void save()
  } else if (shortcut === "back") {
    event.preventDefault()
    if (!saving.value) emit("cancel")
  }
}
```

In `ApplicationsView.vue`, Escape calls `resetForm()` when editing; otherwise it sets `expandedId = null` when a timeline is open. Do nothing when neither state exists or an async action is pending. Native `window.confirm` remains unchanged.

- [ ] **Step 7: Add field-specific Web job query feedback**

In `JobsView.vue`, keep the existing empty-role string exactly, but assign it to `roleFieldError` and clear stale global `error` in that validation branch. Add `watch(roleName, (value) => { if (value.trim()) roleFieldError.value = "" })`, `aria-invalid`, `aria-describedby="jobs-role-error"`, and an inline `form-error`. Keep later network failures in `error`/`ErrorNotice`.

- [ ] **Step 8: Surface unanswered Web assessment questions without changing completeness logic**

In `AssessmentView.vue`:

- Add `validationActive`.
- Keep `isAssessmentComplete` and the existing error string.
- Change submit button disabled state from `!complete` to `saving`, so clicking an incomplete form reaches the existing guarded `submit()` and surfaces feedback without sending an API request.
- Set `validationActive = true` when incomplete submit is attempted.
- Pass `invalid` to every unanswered `AssessmentQuestionCard` only after activation.
- Watch `complete`; when it becomes true, clear `validationActive` and clear global `error` only when it exactly equals the existing `请完成全部题目后提交` validation string. Never clear an API error from this watcher.

In `AssessmentQuestionCard.vue`, assign props and add a deterministic described-by ID derived from the existing question key:

```ts
import { computed } from "vue"

const props = defineProps<{
  question: AssessmentQuestion
  modelValue: number | undefined
  disabled: boolean
  invalid?: boolean
}>()
const hintId = computed(() => `assessment-question-${props.question.key}-error`)
```

On the existing root `<article>`, add `:class="{ 'is-invalid': invalid }"`, `:aria-invalid="invalid || undefined"`, and `:aria-describedby="invalid ? hintId : undefined"`. Render `<small v-if="invalid" :id="hintId" class="question-error">请选择一个符合程度</small>` after the scale hints.

In `base.css`, add only native CSS feedback:

```css
.assessment-question.is-invalid {
  border-color: color-mix(in srgb, var(--danger) 60%, var(--line));
  box-shadow: inset 3px 0 0 var(--danger);
}
.question-error {
  color: var(--danger);
  font-size: 12px;
  line-height: 1.45;
}
```

- [ ] **Step 9: Run focused/full Web tests and build**

```powershell
npm.cmd test -- src/tests/keyboard-shortcuts.spec.ts src/tests/assessment-workflow.spec.ts src/tests/interaction.spec.ts --reporter=dot
npm.cmd test -- --reporter=dot
npm.cmd run build
```

- [ ] **Step 10: Commit Task 5**

From repository root:

```powershell
git add web-frontend/src/lib/keyboard-shortcuts.ts web-frontend/src/tests/keyboard-shortcuts.spec.ts web-frontend/src/tests/interaction.spec.ts web-frontend/src/views/ResumeEditorView.vue web-frontend/src/views/ApplicationsView.vue web-frontend/src/views/JobsView.vue web-frontend/src/views/AssessmentView.vue web-frontend/src/components/AssessmentQuestionCard.vue web-frontend/src/styles/base.css
git commit -m "feat(web): add keyboard and inline form guidance"
```

---

### Task 6: Web Progressive Lists, Empty States, and Stable Wide Records

**Files:**
- Create: `web-frontend/src/composables/useIncrementalList.ts`
- Create: `web-frontend/src/components/ProgressiveListSentinel.vue`
- Create: `web-frontend/src/tests/incremental-list.spec.ts`
- Modify: `web-frontend/src/views/ResumeView.vue`
- Modify: `web-frontend/src/views/ApplicationsView.vue`
- Modify: `web-frontend/src/views/EvidenceView.vue`
- Modify: `web-frontend/src/views/MembershipView.vue`
- Modify: `web-frontend/src/views/JobsView.vue`
- Modify: `web-frontend/src/styles/base.css`
- Modify: `web-frontend/src/tests/interaction.spec.ts`

**Interfaces:**
- Produces `useIncrementalList<T>(source: Readonly<Ref<readonly T[]>>, initial?: number, step?: number)` returning `visibleItems`, `hasMore`, `showMore()`, and `reset()` with Web defaults 40/40.
- `ProgressiveListSentinel` consumes `hasMore: boolean` and emits `more`; its button remains a manual fallback when `IntersectionObserver` is unavailable.
- Source arrays remain authoritative for mutations and API results.

- [ ] **Step 1: Write failing Web incremental-list tests**

Create `web-frontend/src/tests/incremental-list.spec.ts`:

```ts
import { ref } from "vue"
import { describe, expect, it } from "vitest"

import { useIncrementalList } from "../composables/useIncrementalList"

describe("useIncrementalList for Web", () => {
  it("renders 40 records and advances by 40 without exceeding length", () => {
    const source = ref(Array.from({ length: 95 }, (_, index) => index))
    const list = useIncrementalList(source)
    expect(list.visibleItems.value).toHaveLength(40)
    list.showMore()
    expect(list.visibleItems.value).toHaveLength(80)
    list.showMore()
    expect(list.visibleItems.value).toHaveLength(95)
    expect(list.hasMore.value).toBe(false)
  })

  it("resets after a refresh or filter change", () => {
    const source = ref(Array.from({ length: 95 }, (_, index) => index))
    const list = useIncrementalList(source)
    list.showMore()
    list.reset()
    expect(list.visibleItems.value).toHaveLength(40)
  })
})
```

- [ ] **Step 2: Run the test and verify RED**

```powershell
cd web-frontend
npm.cmd test -- src/tests/incremental-list.spec.ts --reporter=dot
```

Expected: FAIL because the Web composable does not exist.

- [ ] **Step 3: Implement the Web composable**

Create `web-frontend/src/composables/useIncrementalList.ts`:

```ts
import { computed, ref, type Ref } from "vue"

export function useIncrementalList<T>(
  source: Readonly<Ref<readonly T[]>>,
  initial = 40,
  step = 40,
) {
  const limit = ref(initial)
  const visibleItems = computed(() => source.value.slice(0, limit.value))
  const hasMore = computed(() => limit.value < source.value.length)
  const showMore = () => { limit.value = Math.min(limit.value + step, source.value.length) }
  const reset = () => { limit.value = initial }
  return { visibleItems, hasMore, showMore, reset }
}
```

- [ ] **Step 4: Implement the progressive sentinel contract-first**

Add static assertions to `interaction.spec.ts` requiring `IntersectionObserver`, `watch(target`, `observer.disconnect()`, `type="button"`, and `emit("more")`; run the interaction test and verify RED.

Create `ProgressiveListSentinel.vue` with:

```vue
<script setup lang="ts">
import { onBeforeUnmount, ref, watch } from "vue"
defineProps<{ hasMore: boolean }>()
const emit = defineEmits<{ more: [] }>()
const target = ref<HTMLButtonElement | null>(null)
let observer: IntersectionObserver | null = null

function disconnect(): void {
  observer?.disconnect()
  observer = null
}

watch(target, (element) => {
  disconnect()
  if (!("IntersectionObserver" in window) || !element) return
  observer = new IntersectionObserver(([entry]) => {
    if (entry?.isIntersecting) emit("more")
  }, { rootMargin: "240px 0px" })
  observer.observe(element)
}, { flush: "post" })

onBeforeUnmount(disconnect)
</script>

<template>
  <button v-if="hasMore" ref="target" type="button" class="progressive-list-sentinel" @click="emit('more')">显示更多</button>
</template>
```

- [ ] **Step 5: Wire Web progressive rendering**

Use `useIncrementalList` and `ProgressiveListSentinel` in:

- `ResumeView`: drafts.
- `ApplicationsView`: filtered application records; reset on refresh/filter.
- `EvidenceView`: evidence records.
- `MembershipView`: order records.

Render only `visibleItems` while every edit/delete/payment/status operation continues to use the original item object. Reset on each successful refresh and relevant filter change.

Use these exact local bindings:

```ts
// ResumeView.vue
const {
  visibleItems: renderedDrafts,
  hasMore: hasMoreDrafts,
  showMore: showMoreDrafts,
  reset: resetVisibleDrafts,
} = useIncrementalList(drafts)

// ApplicationsView.vue
const {
  visibleItems: renderedApplications,
  hasMore: hasMoreApplications,
  showMore: showMoreApplications,
  reset: resetVisibleApplications,
} = useIncrementalList(items)

// EvidenceView.vue
const {
  visibleItems: renderedEvidence,
  hasMore: hasMoreEvidence,
  showMore: showMoreEvidence,
  reset: resetVisibleEvidence,
} = useIncrementalList(items)

// MembershipView.vue
const {
  visibleItems: renderedOrders,
  hasMore: hasMoreOrders,
  showMore: showMoreOrders,
  reset: resetVisibleOrders,
} = useIncrementalList(orders)
```

Call `resetVisibleItems()` immediately after assigning each refreshed source array. In `ApplicationsView`, the existing status change already calls `refresh()`, so that successful refresh is the single filter-reset path. Place this immediately after each rendered list:

```vue
<!-- ResumeView example; use the matching page-specific names above elsewhere. -->
<ProgressiveListSentinel :has-more="hasMoreDrafts" @more="showMoreDrafts" />
```

- [ ] **Step 6: Add additive Web empty-state refinements**

- `ResumeView`: keep both existing strings and add `本机编辑内容会自动保留，手动保存后同步到服务端。`; wrap the existing `FilePenLine` icon with the shared icon surface below.
- `ApplicationsView`: keep both existing strings and add `可直接使用上方表单新增第一条记录。`; wrap the existing `Building2` icon with the shared icon surface below.
- `JobsView`: keep the existing initial heading and description, add `输入具体岗位名称后开始整理能力要求。`, and wrap the existing `BriefcaseBusiness` icon with the same surface.

Use this exact wrapper in all three views, retaining each existing Lucide icon inside it:

```vue
<span class="empty-board-icon" aria-hidden="true"><FilePenLine :size="24" aria-hidden="true" /></span>
```

Add one shared fixed-size style:

```css
.empty-board-icon {
  display: grid;
  flex: 0 0 44px;
  width: 44px;
  height: 44px;
  place-items: center;
  color: var(--forest);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: var(--surface-muted);
}
```

Do not add a create-resume API, route, or new business action.

- [ ] **Step 7: Stabilize the five-column record grid and horizontal scroll**

In `base.css`:

```css
.application-table {
  overflow-x: auto;
  overscroll-behavior-x: contain;
  scrollbar-gutter: stable;
  -webkit-overflow-scrolling: touch;
}
.application-row {
  min-width: 980px;
  grid-template-columns: 40px minmax(220px, 1fr) 128px 170px minmax(250px, auto);
}
.application-record { contain-intrinsic-size: auto 124px; }
.evidence-list > article { contain-intrinsic-size: auto 132px; }
.record-list > .record-row { contain-intrinsic-size: auto 82px; }
.order-list > .order-row { contain-intrinsic-size: auto 72px; }
```

Inside the existing responsive breakpoint, restore `min-width: 0`, `overflow-x: visible`, and the current stacked tracks. Do not add resize JavaScript.

Use this exact addition inside `@media (max-width: 840px)` while retaining the existing stacked behavior:

```css
.application-table {
  overflow-x: visible;
  scrollbar-gutter: auto;
}
.application-row {
  min-width: 0;
  grid-template-columns: 40px minmax(0, 1fr) auto;
}
.application-row small {
  grid-column: 2 / -1;
  text-align: left;
}
.application-row .record-actions {
  grid-column: 2 / -1;
  justify-content: flex-start;
}
```

- [ ] **Step 8: Complete static contracts and run RED/GREEN**

In `interaction.spec.ts`, add this complete contract:

```ts
it("bounds large Web lists and stabilizes the wide application grid", () => {
  const resume = readFileSync(new URL("../views/ResumeView.vue", import.meta.url), "utf8")
  const applications = readFileSync(new URL("../views/ApplicationsView.vue", import.meta.url), "utf8")
  const evidence = readFileSync(new URL("../views/EvidenceView.vue", import.meta.url), "utf8")
  const membership = readFileSync(new URL("../views/MembershipView.vue", import.meta.url), "utf8")
  const jobs = readFileSync(new URL("../views/JobsView.vue", import.meta.url), "utf8")
  const sentinel = readFileSync(new URL("../components/ProgressiveListSentinel.vue", import.meta.url), "utf8")
  const styles = readFileSync(new URL("../styles/base.css", import.meta.url), "utf8")

  for (const source of [resume, applications, evidence, membership]) {
    expect(source).toContain("useIncrementalList")
    expect(source).toContain("ProgressiveListSentinel")
  }
  expect(sentinel).toContain("IntersectionObserver")
  expect(sentinel).toContain("watch(target")
  expect(sentinel).toContain("observer?.disconnect()")
  expect(sentinel).toContain('type="button"')
  expect(sentinel).toContain("emit('more')")
  expect(styles).toContain("overflow-x: auto")
  expect(styles).toContain("grid-template-columns: 40px minmax(220px, 1fr) 128px 170px minmax(250px, auto)")
  expect(resume).toContain("本机编辑内容会自动保留，手动保存后同步到服务端。")
  expect(applications).toContain("可直接使用上方表单新增第一条记录。")
  expect(jobs).toContain("输入具体岗位名称后开始整理能力要求。")
})
```

Run once before page/CSS edits for RED and again afterward for GREEN.

- [ ] **Step 9: Run full Web tests and production build**

```powershell
npm.cmd test -- src/tests/incremental-list.spec.ts src/tests/interaction.spec.ts --reporter=dot
npm.cmd test -- --reporter=dot
npm.cmd run build
```

- [ ] **Step 10: Commit Task 6**

From repository root:

```powershell
git add web-frontend/src/composables/useIncrementalList.ts web-frontend/src/components/ProgressiveListSentinel.vue web-frontend/src/tests/incremental-list.spec.ts web-frontend/src/tests/interaction.spec.ts web-frontend/src/views/ResumeView.vue web-frontend/src/views/ApplicationsView.vue web-frontend/src/views/EvidenceView.vue web-frontend/src/views/MembershipView.vue web-frontend/src/views/JobsView.vue web-frontend/src/styles/base.css
git commit -m "perf(web): stabilize large record surfaces"
```

---

### Task 7: Changelog, UI Audit, Full Verification, and Scope Audit

**Files:**
- Modify: `docs/interaction-upgrade-changelog.md`

**Interfaces:**
- Consumes all completed H5/Web changes.
- Produces final evidence only; no production behavior is added in this task.

- [ ] **Step 1: Run the Impeccable detector exactly once after UI edits are complete**

Run one command with every changed UI target:

```powershell
node C:\Users\16102\.codex\skills\impeccable\scripts\detect.mjs --json resume-miniprogram/src/pages/resume-form/index.vue resume-miniprogram/src/pages/job-search/index.vue resume-miniprogram/src/pages/career-assessment/index.vue resume-miniprogram/src/pages/drafts/index.vue resume-miniprogram/src/pages/applications/index.vue resume-miniprogram/src/pages/evidence/index.vue resume-miniprogram/src/pages/job-collection/index.vue web-frontend/src/views/ResumeEditorView.vue web-frontend/src/views/JobsView.vue web-frontend/src/views/AssessmentView.vue web-frontend/src/views/ApplicationsView.vue web-frontend/src/views/ResumeView.vue web-frontend/src/views/EvidenceView.vue web-frontend/src/views/MembershipView.vue web-frontend/src/components/ProgressiveListSentinel.vue web-frontend/src/styles/base.css
```

Expected: `[]`. If findings exist, fix the complete batch once and do not rerun the detector.

- [ ] **Step 2: Run both complete frontend suites and production builds fresh**

From `resume-miniprogram`:

```powershell
npm.cmd run test:unit -- --reporter=dot
npm.cmd run build:h5
```

From `web-frontend`:

```powershell
npm.cmd test -- --reporter=dot
npm.cmd run build
```

Capture the exact file/test counts and successful build summaries for Step 5. The complete suites must include the existing H5 `*-api.spec.ts`/`phase*-services.spec.ts` contracts and Web `api.spec.ts`/`domain-api.spec.ts` contracts; these are the mock-mode and backend-docking evidence.

- [ ] **Step 3: Verify formatting and frontend-only scope**

From repository root:

```powershell
git diff --check b0dbe20..HEAD
git diff --check
git status --short
git diff --name-only b0dbe20..HEAD
```

Inspect the changed-path output. It must contain no file under:

```text
resume-backend/
**/services/
**/api/
**/router/
**/mocks/
**/fixtures/
```

It must contain no `package-lock.json`, `pnpm-lock.yaml`, or `yarn.lock`. Existing frontend API tests in the full suites must be green, proving mock/backend request mapping remains intact.

- [ ] **Step 4: Review requirements against the diff**

Confirm explicitly:

```text
[ ] No existing Chinese string was replaced.
[ ] No remote autosave request was added.
[ ] H5 assessment navigation is still non-blocking.
[ ] Web assessment still blocks incomplete submission before the API.
[ ] Progressive lists eventually expose every source record.
[ ] Manual buttons and keyboard shortcuts share pending guards.
[ ] Native modal/confirm business callbacks are unchanged.
[ ] Application rows define all five columns and remain usable at narrow widths.
```

- [ ] **Step 5: Append the dated changelog entry with verified evidence**

Add `## 2026-08-24 quality-of-life and form robustness` to `docs/interaction-upgrade-changelog.md` and record:

- H5/Web validation surfaces.
- 800ms local checkpoint debounce and explicit no-remote-autosave rule.
- Exact additive empty-state strings and the existing-only navigation policy.
- H5 20/20 and Web 40/40 progressive thresholds.
- `Ctrl/Cmd+S`, `Alt+ArrowLeft`, and scoped Escape behavior.
- H5 focus restoration and Web five-column record layout.
- The exact test file/test counts and build results captured in Step 2.
- The changed-path/mock/backend-docking audit result from Steps 2-4.

- [ ] **Step 6: Commit documentation and any verification-only fixes**

From repository root:

```powershell
git add docs/interaction-upgrade-changelog.md
git commit -m "docs: record frontend qol robustness"
```

- [ ] **Step 7: Confirm clean final state**

```powershell
git diff --check b0dbe20..HEAD
git status --short
git log --oneline -10
```

Expected: empty status output and the seven iteration commits at the top of the branch.
