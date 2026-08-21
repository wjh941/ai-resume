# 独立 Web 求职工作台视觉与交互升级 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修复独立 Web 工作概览的草稿列表解析错误，并以不改变业务接口的方式升级工作台的视觉层级、状态反馈和响应式体验。

**Architecture:** 在 `src/lib/dashboard.ts` 的数据边界适配既有草稿数组响应，保留其他 `{ items }` API 合同；在 `src/lib/api.ts` 暴露带 HTTP 状态的错误类型，由概览页面显示精确中文提示。所有视觉调整集中在现有 `src/styles/base.css` 与现有壳层组件，避免增加设计依赖或重构视图结构。

**Tech Stack:** Vue 3、TypeScript、Vite、Vitest、CSS 自定义属性、Lucide Vue。

## Global Constraints

- 仅修改 `web-frontend` 与本计划相关文档；H5、FastAPI API、数据库和既有业务流程不变。
- 所有新增用户可见文本使用简体中文，保留 JWT、API 等技术专有名词。
- 不新增 npm 依赖、图像资产或远程字体。
- 圆角不超过 8px；使用可扫描的工作台布局，避免大量浮动卡片和装饰性渐变。
- 支持浅色、深色、窄屏与 `prefers-reduced-motion`。

---

### Task 1: 为概览数据适配和错误状态建立回归测试

**Files:**
- Modify: `web-frontend/src/tests/dashboard.spec.ts`
- Modify: `web-frontend/src/tests/api.spec.ts`

**Interfaces:**
- Consumes: `loadOverview(request, planId)` 与 `requestApi(path, init)`。
- Produces: 草稿数组响应可被概览计数；HTTP 401 错误保留状态码供视图区分提示。

- [ ] **Step 1: 写出草稿数组响应的失败测试**

```ts
it("counts drafts when the existing draft API returns an array", async () => {
  const request = vi.fn()
    .mockResolvedValueOnce({ items: [] })
    .mockResolvedValueOnce([{ id: "draft-1" }, { id: "draft-2" }])
    .mockResolvedValueOnce({ items: [] })

  await expect(loadOverview(request)).resolves.toMatchObject({ draftCount: 2 })
})
```

- [ ] **Step 2: 运行失败测试，确认当前实现错误读取 `drafts.items`**

Run: `npm.cmd run test -- src/tests/dashboard.spec.ts`

Expected: FAIL，`drafts.items` 为 `undefined`。

- [ ] **Step 3: 写出 HTTP 状态错误的失败测试**

```ts
it("preserves a 401 status for a failed API request", async () => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(
    new Response(JSON.stringify({ detail: "登录已过期" }), { status: 401 }),
  ))

  await expect(requestApi("/api/applications")).rejects.toMatchObject({ status: 401 })
})
```

- [ ] **Step 4: 运行 API 失败测试，确认当前普通 `Error` 没有 `status`**

Run: `npm.cmd run test -- src/tests/api.spec.ts`

Expected: FAIL，断言对象没有 `status: 401`。

- [ ] **Step 5: 提交测试基线**

```bash
git add web-frontend/src/tests/dashboard.spec.ts web-frontend/src/tests/api.spec.ts
git commit -m "test(web): cover overview response boundaries"
```

### Task 2: 最小化修复概览读取与登录失效提示

**Files:**
- Modify: `web-frontend/src/lib/dashboard.ts`
- Modify: `web-frontend/src/lib/api.ts`
- Modify: `web-frontend/src/views/OverviewView.vue`
- Test: `web-frontend/src/tests/dashboard.spec.ts`
- Test: `web-frontend/src/tests/api.spec.ts`

**Interfaces:**
- Consumes: 后端的 `/api/applications`、`/api/draft/list`、`/api/career/tasks?plan_id=` 响应。
- Produces: `loadOverview()` 返回 `{ applicationCount, draftCount, openTaskCount }`；`ApiRequestError` 具有 `status: number`。

- [ ] **Step 1: 在 `dashboard.ts` 将草稿列表声明为数组并计算其长度**

```ts
type DraftListResponse = Array<{ id: string }>

const [applications, drafts, tasks] = await Promise.all([
  request<ItemsResponse>("/api/applications"),
  request<DraftListResponse>("/api/draft/list"),
  request<ItemsResponse>(`/api/career/tasks?plan_id=${encodeURIComponent(planId)}`),
])

return { applicationCount: applications.items.length, draftCount: drafts.length, openTaskCount: tasks.items.filter((task) => task.status !== "completed").length }
```

- [ ] **Step 2: 在 `api.ts` 添加可导出的状态错误类型，并在非成功响应时抛出它**

```ts
export class ApiRequestError extends Error {
  constructor(message: string, readonly status: number) {
    super(message)
    this.name = "ApiRequestError"
  }
}

if (!response.ok || body.code !== "ok") {
  throw new ApiRequestError(readMessage(body), response.status)
}
```

- [ ] **Step 3: 在概览页面仅对 401 显示“登录已过期，请退出后重新登录”，其他错误显示读取失败提示**

```ts
} catch (reason) {
  error.value = reason instanceof ApiRequestError && reason.status === 401
    ? "登录已过期，请退出后重新登录"
    : "暂时无法读取工作概览，请稍后重试"
}
```

- [ ] **Step 4: 运行两份聚焦测试，确认变绿**

Run: `npm.cmd run test -- src/tests/dashboard.spec.ts src/tests/api.spec.ts`

Expected: PASS，草稿数组被正确计数，401 错误包含状态码。

- [ ] **Step 5: 提交最小行为修复**

```bash
git add web-frontend/src/lib/dashboard.ts web-frontend/src/lib/api.ts web-frontend/src/views/OverviewView.vue web-frontend/src/tests/dashboard.spec.ts web-frontend/src/tests/api.spec.ts
git commit -m "fix(web): handle overview draft responses"
```

### Task 3: 强化工作台视觉层级和交互反馈

**Files:**
- Modify: `web-frontend/src/styles/base.css`
- Modify: `web-frontend/src/components/WebSidebar.vue`
- Modify: `web-frontend/src/components/WebTopbar.vue`
- Modify: `web-frontend/src/views/OverviewView.vue`

**Interfaces:**
- Consumes: 现有 CSS 语义令牌、壳层组件的 `activeView` 与 `dark` 属性、概览的 `loading` 和 `error` 状态。
- Produces: 统一的浅色/深色语义颜色、显式主操作层级、键盘可见焦点、减少动态效果模式。

- [ ] **Step 1: 在 `base.css` 将颜色和阴影归并为语义令牌**

```css
:root {
  --canvas: #f6f5f0;
  --surface: #fffefa;
  --surface-raised: #ffffff;
  --ink: #17231d;
  --muted: #627066;
  --brand: #17483a;
  --accent: #e96b4a;
  --progress: #16866a;
  --insight: #287394;
  --line: #d9ddd5;
  --radius: 8px;
}
```

- [ ] **Step 2: 调整壳层与概览的版式，而不改变现有页面入口**

```css
.web-sidebar { background: var(--brand); }
.navigation-item.is-active { color: var(--brand); background: var(--surface-raised); }
.overview-strip { gap: 1px; background: var(--line); }
.metric-block { min-height: 176px; background: var(--surface-raised); }
.action-route { border-color: var(--line); }
```

- [ ] **Step 3: 为主要交互添加短促且可关闭的状态变化**

```css
@media (prefers-reduced-motion: no-preference) {
  .navigation-item, .primary-button, .route-actions button, .record-row {
    transition: transform 160ms ease, background-color 160ms ease, border-color 160ms ease, color 160ms ease;
  }
  .route-actions button:hover { transform: translateY(-2px); }
}
```

- [ ] **Step 4: 保持所有图标按钮、导航与表单的可见键盘焦点和不低于现有对比度的辅助文本**

```css
button:focus-visible, input:focus-visible, select:focus-visible {
  outline: 3px solid color-mix(in srgb, var(--insight) 60%, transparent);
  outline-offset: 3px;
}
```

- [ ] **Step 5: 提交视觉升级**

```bash
git add web-frontend/src/styles/base.css web-frontend/src/components/WebSidebar.vue web-frontend/src/components/WebTopbar.vue web-frontend/src/views/OverviewView.vue
git commit -m "style(web): elevate workbench hierarchy"
```

### Task 4: 完整验证与交付检查

**Files:**
- Verify: `web-frontend/src/lib/dashboard.ts`
- Verify: `web-frontend/src/lib/api.ts`
- Verify: `web-frontend/src/views/OverviewView.vue`
- Verify: `web-frontend/src/styles/base.css`

**Interfaces:**
- Consumes: 本地 Web 开发服务 `http://127.0.0.1:5174/` 与现有 FastAPI 后端 `http://127.0.0.1:8000/`。
- Produces: 通过的单元测试、生产构建和一次机械设计检查。

- [ ] **Step 1: 运行独立 Web 的完整单元测试**

Run: `npm.cmd run test`

Expected: PASS，所有测试文件通过。

- [ ] **Step 2: 运行生产构建**

Run: `npm.cmd run build`

Expected: PASS，Vite 输出 `dist/`。

- [ ] **Step 3: 对改动后的 Web 文件运行一次 Impeccable 检查**

Run: `node C:\Users\16102\.codex\skills\impeccable\scripts\detect.mjs --json web-frontend/src/lib/dashboard.ts web-frontend/src/lib/api.ts web-frontend/src/views/OverviewView.vue web-frontend/src/styles/base.css web-frontend/src/components/WebSidebar.vue web-frontend/src/components/WebTopbar.vue`

Expected: 检查结果中不包含阻断性问题；如有结果，只在同一批次内修复与本计划相关的提示。

- [ ] **Step 4: 核验运行服务**

Run: `(Invoke-WebRequest 'http://127.0.0.1:5174/' -UseBasicParsing).StatusCode`

Expected: `200`。

- [ ] **Step 5: 推送当前分支**

```bash
git status --short
git push origin feature/ai-resume-demo
```
