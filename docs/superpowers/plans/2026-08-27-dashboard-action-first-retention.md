# Dashboard Action-First Retention Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把独立 Web 工作台的 Dashboard 升级为“今日行动台”，让用户进入后能看到一个真实、可执行的下一步，并能继续推进简历、职业规划和投递。

**Architecture:** 保留现有 `loadOverview` 请求边界，先把三个接口的原始记录规范化为可测试的 Dashboard 状态，再由 `OverviewView` 渲染主焦点、进度状态和最多三条继续推进记录。行动只触发现有导航事件，不新增后端 API；“换一件”使用同一候选数组的确定性轮换，避免随机和虚假激励。

**Tech Stack:** Vue 3 `<script setup>`, TypeScript, Vitest, Vite, lucide-vue-next, existing `base.css` design tokens.

## Global Constraints

- 继续复用 `/api/applications`、`/api/draft/list` 和 `/api/career/tasks`，本轮不新增后端端点。
- 所有行动候选内容必须来自 API 返回数据；缺少字段时降级为通用中文提示，不生成事实性结论。
- 使用目标梯度、降低选择成本、即时完成反馈和回访线索；不使用排行榜、强制签到、倒计时、虚假成就或焦虑文案。
- Dashboard 桌面布局保持双列层次，窄屏改为单列；加载、错误和空状态保持稳定尺寸与可恢复入口。
- 新增用户可见文案使用简体中文，按钮必须是可聚焦的原生按钮并配有明确名称。
- 本轮不实现运营监控、支付、推送、外部岗位抓取或新的积分系统。

---

### Task 1: Build A Deterministic Dashboard View Model

**Files:**
- Modify: `web-frontend/src/lib/dashboard.ts`
- Test: `web-frontend/src/tests/dashboard.spec.ts`

**Interfaces:**
- Consumes: raw arrays or `{ items: [] }` envelopes returned by the existing three endpoints.
- Produces: `OverviewState`, `FocusAction`, `ProgressItem`, `ContinuationItem`, `buildOverviewState(input)`, and `selectFocusAction(input, offset)` for `OverviewView`.

- [ ] **Step 1: Write failing model tests**

Add tests that call the pure functions with raw records and assert these exact outcomes:

```ts
import { buildOverviewState, selectFocusAction } from "../lib/dashboard"

it("chooses the earliest incomplete due task before other candidates", () => {
  const state = buildOverviewState({
    applications: [{ id: "app-1", company: "Acme", role_name: "运营", next_action_at: "2099-03-04" }],
    drafts: [{ id: "draft-1", job_title: "运营", resume: { basic: { name: "林", phone: "1", email: "a@b.cn", city: "沪" }, job: { target_role: "运营" } } }],
    tasks: [
      { id: "task-late", title: "准备面试", status: "pending", due_date: "2099-03-12" },
      { id: "task-soon", title: "补充项目成果", status: "pending", due_date: "2099-03-01" },
    ],
  })

  expect(state.focus.kind).toBe("task")
  expect(state.focus.id).toBe("task-soon")
})

it("falls back to starter actions and exposes progress states for empty data", () => {
  const state = buildOverviewState({ applications: [], drafts: [], tasks: [] })

  expect(state.focus.target).toBe("resume")
  expect(state.focusOptions).toHaveLength(3)
  expect(state.progress.map((item) => item.state)).toEqual(["not-started", "not-started", "not-started"])
  expect(state.hasWorkspaceData).toBe(false)
})

it("rotates focus deterministically and puts missing fields behind generic copy", () => {
  const input = { applications: [], drafts: [{ id: "draft-1" }], tasks: [{ id: "task-1", status: "pending" }] }
  const first = selectFocusAction(input, 0)
  const second = selectFocusAction(input, 1)

  expect(first.id).not.toBe(second.id)
  expect(second.title).toContain("行动")
})
```

- [ ] **Step 2: Run the focused tests and confirm they fail**

Run `npm.cmd run test -- --run src/tests/dashboard.spec.ts` from `web-frontend`. Expected: FAIL because the new model types and functions do not exist.

- [ ] **Step 3: Implement the minimal normalized model**

In `dashboard.ts`:

1. Define raw record types with optional fields used by the existing API: tasks use `id`, `title`, `description`, `due_date`, `status`; applications use `id`, `company`, `role_name`, `status`, `next_action_at`, `updated_at`; drafts use `id`, `job_title`, `updated_at`, and optional `resume.basic`/`resume.job`.
2. Keep `loadOverview(request, planId)` and its three parallel requests, then pass `readItems` results to `buildOverviewState`.
3. Sort incomplete tasks by valid `due_date` ascending, missing dates last, then `id`; sort active applications with `next_action_at` using the same rule.
4. Build focus candidates in this order: earliest incomplete task, earliest application follow-up, create-first-resume when no drafts, career-planning starter when drafts exist but no tasks, then review applications when no urgent candidate exists. Deduplicate by `kind`/`id`, cap at three, and use generic labels when optional fields are absent.
5. Derive progress exactly as follows: resume is `not-started` with no drafts, `completed` when every draft has non-empty `resume.basic` fields (`name`, `phone`, `email`, `city`) and `resume.job.target_role`, otherwise `in-progress`; career is `not-started` with no tasks, `completed` when every task is completed, otherwise `in-progress`; applications is `not-started` with no records, `completed` when every record is terminal (`offer`, `rejected`, `closed`), otherwise `in-progress`.
6. Build up to three continuations from incomplete tasks, active applications, and drafts, excluding the selected focus item. Set `hasWorkspaceData` when any source list is non-empty. Never infer company, role, dates, or completion facts that are not in the response.

- [ ] **Step 4: Run the focused tests and confirm they pass**

Run `npm.cmd run test -- --run src/tests/dashboard.spec.ts` from `web-frontend`. Expected: PASS, including existing count aggregation tests.

- [ ] **Step 5: Commit the data model**

```bash
git add web-frontend/src/lib/dashboard.ts web-frontend/src/tests/dashboard.spec.ts
git commit -m "feat(web): derive dashboard action state"
```

### Task 2: Render The Action-First Dashboard

**Files:**
- Modify: `web-frontend/src/views/OverviewView.vue`
- Modify: `web-frontend/src/tests/interaction.spec.ts`

**Interfaces:**
- Consumes: `OverviewState.focus`, `focusOptions`, `progress`, `continuations`, `hasWorkspaceData` from Task 1.
- Produces: navigation events with the existing `resume`, `career`, and `applications` view names; no API contract changes.

- [ ] **Step 1: Write the failing source contract tests**

Extend the Web source-contract suite to require the new structure and interaction names:

```ts
it("renders one primary focus, progress states, and recoverable continuation actions", () => {
  const overview = readFileSync(new URL("../views/OverviewView.vue", import.meta.url), "utf8")
  expect(overview).toContain("overview-focus")
  expect(overview).toContain("focus-action")
  expect(overview).toContain("focusOptions")
  expect(overview).toContain("progress-list")
  expect(overview).toContain("continue-list")
  expect(overview).toContain("换一件")
  expect(overview).toContain('aria-live="polite"')
})
```

- [ ] **Step 2: Run the contract test and confirm it fails**

Run `npm.cmd run test -- --run src/tests/interaction.spec.ts`. Expected: FAIL because the existing view still renders only metric blocks and route buttons.

- [ ] **Step 3: Implement the view with stable states**

Update `OverviewView.vue` to:

1. Keep the existing `refresh`, `loading`, `error`, `ErrorNotice`, and `AsyncButton` flow. Preserve the current 401 message and retry behavior.
2. Add `focusIndex`, a computed `activeFocus` from `overview.focusOptions`, and `rotateFocus()` that advances modulo the option count. Render “换一件” only when there is more than one option.
3. Render a two-column `overview-focus` section. The primary panel must include the exact heading “今天先完成这一件事”, the selected action title/detail, optional due text, and one primary `focus-action` button that emits the action target. Set an `aria-live` status message before emitting so the click has immediate feedback.
4. Render three progress rows for resume, career, and applications using only “未开始 / 进行中 / 已完成”; each row includes a direct navigation button and an icon/state marker.
5. Render the existing counts as a compact secondary snapshot instead of the first viewport’s primary hierarchy.
6. Render `continue-list` with at most three records and direct navigation buttons. When `hasWorkspaceData` is false, render a three-step starter checklist using the same three destinations. Keep all labels in Chinese and avoid rank, streak, countdown, or pressure language.
7. Keep the existing `emit("navigate", ...)` contract and use `:disabled="loading"` on refresh/focus controls while loading.

- [ ] **Step 4: Run the contract tests and confirm they pass**

Run `npm.cmd run test -- --run src/tests/interaction.spec.ts src/tests/dashboard.spec.ts` from `web-frontend`. Expected: PASS.

- [ ] **Step 5: Commit the view**

```bash
git add web-frontend/src/views/OverviewView.vue web-frontend/src/tests/interaction.spec.ts
git commit -m "feat(web): turn dashboard into action workspace"
```

### Task 3: Polish Dashboard Visual Hierarchy And Responsive Behavior

**Files:**
- Modify: `web-frontend/src/styles/base.css`
- Modify: `web-frontend/src/tests/interaction.spec.ts`

**Interfaces:**
- Consumes: the class names emitted by `OverviewView.vue` in Task 2.
- Produces: stable desktop/mobile layout with existing light/dark theme tokens and reduced-motion compatibility.

- [ ] **Step 1: Add failing style contracts**

Extend the existing styles contract with selectors that guarantee the layout boundary:

```ts
expect(styles).toContain(".overview-focus")
expect(styles).toContain(".progress-list")
expect(styles).toContain(".continue-list")
expect(styles).toMatch(/@media \(max-width: 840px\)/)
expect(styles).toContain("min-width: 0")
```

- [ ] **Step 2: Run the style contract and confirm it fails**

Run `npm.cmd run test -- --run src/tests/interaction.spec.ts`. Expected: FAIL for the new selectors.

- [ ] **Step 3: Implement focused styles in `base.css`**

Add styles next to the existing overview rules:

1. Use `.overview-focus { display: grid; grid-template-columns: minmax(0, 1.25fr) minmax(280px, .75fr); gap: 24px; }` with `min-width: 0` on both columns so long Chinese text cannot widen the grid.
2. Give the focus panel a restrained border and accent rule, with a compact eyebrow, `clamp`-free fixed heading scale, clear primary button, and a short feedback line. Keep card radius at the existing `var(--radius)` value.
3. Style progress rows as a vertical list with explicit state colors and no percentages. Keep the right column visually quieter than the primary action.
4. Use a three-column continuation grid that becomes one column under `840px`; the focus grid also becomes one column at that breakpoint. Ensure buttons have `min-height: 44px`, `overflow-wrap: anywhere`, and no horizontal overflow.
5. Add empty checklist, loading skeleton, and `aria-live` feedback spacing without changing existing global motion tokens. Extend the existing reduced-motion block to cover new transforms/transitions.
6. Reuse current light/dark variables and avoid new gradients, ranking visuals, decorative blobs, or oversized hero typography.

- [ ] **Step 4: Run style contracts and build**

Run `npm.cmd run test -- --run src/tests/interaction.spec.ts` and then `npm.cmd run build` from `web-frontend`. Expected: PASS and a successful Vite production build.

- [ ] **Step 5: Commit the visual pass**

```bash
git add web-frontend/src/styles/base.css web-frontend/src/tests/interaction.spec.ts
git commit -m "style(web): polish dashboard action hierarchy"
```

### Task 4: Verify The Integrated Iteration

**Files:**
- Test only: existing Web test/build outputs; no source changes expected.

**Interfaces:**
- Consumes: the three committed Dashboard changes.
- Produces: evidence that the feature passes unit tests, TypeScript checking, Vite build, and the required visual detector.

- [ ] **Step 1: Run the complete Web test suite**

Run `npm.cmd run test` from `web-frontend`. Expected: all tests pass.

- [ ] **Step 2: Run TypeScript and production build checks**

Run `npm.cmd exec tsc -- --noEmit` and `npm.cmd run build` from `web-frontend`. Expected: no type errors and a successful Vite build.

- [ ] **Step 3: Run the Impeccable detector on the changed Dashboard targets**

Run `node C:\Users\16102\.codex\skills\impeccable\scripts\detect.mjs --json web-frontend/src/views/OverviewView.vue web-frontend/src/styles/base.css`. Expected: detector completes; review any actionable findings before claiming completion.

- [ ] **Step 4: Inspect the final diff without touching unrelated work**

Run `git diff --check` and `git status --short`. Confirm only the Dashboard commits contain this iteration’s files and that prior user changes remain intact.

