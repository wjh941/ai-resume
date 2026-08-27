# Web Capability Trust Loop Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将后端 `/health.data.features` 接入 Web 前端，让短信、支付、岗位和报告入口在可用、演示、暂不可用三种状态下给出真实且可恢复的反馈，同时保持核心简历流程可用。

**Architecture:** 在 `web-frontend/src/lib/capabilities.ts` 建立纯映射器和非阻塞请求服务，`App.vue` 通过 Vue `provide/inject` 提供单一能力引用。受影响页面只消费能力接口，在提交前做可选能力校验；后端仍是最终鉴权来源。

**Tech Stack:** Vue 3.5、TypeScript、Vitest、Vite 5.2.8、lucide-vue-next。

## Global Constraints

- 只修改 `web-frontend` 与对应测试，不修改后端业务接口。
- 能力字段为 `enabled`、`mode`（`real`、`demo`、`disabled`）和 `notice`。
- `/health` 失败或响应畸形时，可选能力回落为 disabled，核心页面仍必须渲染。
- disabled 入口保留但置灰并说明原因；demo 入口必须明确标注演示语义。
- 前端预检不得替代后端鉴权，后端 403 继续使用现有恢复提示。
- 不纳入主题持久化、移动端抽屉无障碍及其他独立体验改造。

---

### Task 1: 建立 Web 能力服务

**Files:**
- Create: `web-frontend/src/lib/capabilities.ts`
- Create: `web-frontend/src/tests/capabilities.spec.ts`
- Reference: `resume-miniprogram/src/services/capability-api.ts`
- Reference: `web-frontend/src/lib/api.ts`

**Interfaces:**
- Produces `CapabilityMode`, `Capability`, `Capabilities`, `CapabilityName`。
- Produces `defaultCapabilities(): Capabilities`、`mapCapabilities(payload: unknown): Capabilities`、`getCapabilities(): Promise<Capabilities>`、`isCapabilityEnabled(capabilities, name): boolean`。
- `getCapabilities` 使用现有 `requestApi` 请求 `/health`，请求异常返回 `defaultCapabilities()`。

- [ ] **Step 1: Write the failing mapper tests**

在 `capabilities.spec.ts` 写入以下行为断言：完整 `features` 保留每个字段；缺失字段回落 disabled；非法 `mode` 或空 `notice` 的单项回落 disabled；payload 为 `null`/数组时整体使用默认值；`getCapabilities` 请求失败时返回默认值；`isCapabilityEnabled` 只有 `enabled === true` 且 `mode !== "disabled"` 才返回 true。

- [ ] **Step 2: Run the focused tests and verify they fail**

Run: `cd web-frontend; npm.cmd run test -- --run src/tests/capabilities.spec.ts`

Expected: FAIL because `src/lib/capabilities.ts` does not exist。

- [ ] **Step 3: Implement the minimal capability module**

实现固定能力名到后端 snake_case 字段的映射；用类型守卫校验布尔值、三种模式和非空字符串；不要把未知字段透传给页面。`mapCapabilities` 对每项调用单项映射器，`getCapabilities` 只捕获请求错误并回落默认对象。

- [ ] **Step 4: Run the focused tests and verify they pass**

Run: `cd web-frontend; npm.cmd run test -- --run src/tests/capabilities.spec.ts`

Expected: PASS。

- [ ] **Step 5: Commit**

```bash
git add web-frontend/src/lib/capabilities.ts web-frontend/src/tests/capabilities.spec.ts
git commit -m "feat(web): add capability state service"
```

### Task 2: 注入能力状态并约束登录入口

**Files:**
- Modify: `web-frontend/src/App.vue`
- Modify: `web-frontend/src/components/LoginPanel.vue`
- Modify: `web-frontend/src/tests/interaction.spec.ts`
- Modify: `web-frontend/src/tests/auth.spec.ts`

**Interfaces:**
- `App.vue` provides a readonly/ref-backed `Capabilities` context under a named injection key exported by `lib/capabilities.ts`。
- `LoginPanel.vue` consumes the context; phone tab and `sendCode` use `sms_login` state。

- [ ] **Step 1: Add failing source/interaction tests**

断言 `App.vue` 调用 `getCapabilities` 并提供 context；登录组件包含 `sms_login` disabled 判断；短信入口 disabled 时不调用 `/api/auth/send-code`。测试必须覆盖 capability 请求 pending/失败时密码登录仍存在。

- [ ] **Step 2: Run focused tests to verify failure**

Run: `cd web-frontend; npm.cmd run test -- --run src/tests/interaction.spec.ts src/tests/auth.spec.ts`

Expected: FAIL on missing provider/disabled behavior。

- [ ] **Step 3: Implement non-blocking provider and login gate**

在 `App.vue` 创建 `ref(defaultCapabilities())`，`onMounted`/启动逻辑异步更新为 `getCapabilities()`，不让模板等待请求。`LoginPanel` 默认密码模式；短信 tab 使用 `:disabled`，显示能力 `notice`，`sendCode` 首行检查 `isCapabilityEnabled` 并设置可读提示后返回。

- [ ] **Step 4: Run focused tests to verify pass**

Run: `cd web-frontend; npm.cmd run test -- --run src/tests/interaction.spec.ts src/tests/auth.spec.ts`

Expected: PASS。

- [ ] **Step 5: Commit**

```bash
git add web-frontend/src/App.vue web-frontend/src/components/LoginPanel.vue web-frontend/src/tests/interaction.spec.ts web-frontend/src/tests/auth.spec.ts
git commit -m "feat(web): gate unavailable sms login"
```

### Task 3: 会员支付状态与演示标记

**Files:**
- Modify: `web-frontend/src/views/MembershipView.vue`
- Modify: `web-frontend/src/tests/membership-workflow.spec.ts`
- Modify: `web-frontend/src/lib/membership.ts` only if a typed guard is needed for the existing callback

**Interfaces:**
- Membership consumes the injected `Capabilities` context and reads `payment.enabled`/`payment.mode`/`payment.notice`。
- Existing `purchase` and `completeDemoPayment` APIs remain unchanged。

- [ ] **Step 1: Add failing payment-state tests**

覆盖 payment disabled 时支付 CTA 不可点击且显示 `notice`；payment demo 时按钮文本包含“演示支付”；disabled 状态下 `payDemo` 不调用 `/api/pay/callback`；套餐和订单列表仍渲染。

- [ ] **Step 2: Run focused tests to verify failure**

Run: `cd web-frontend; npm.cmd run test -- --run src/tests/membership-workflow.spec.ts`

Expected: FAIL because membership has no capability gate。

- [ ] **Step 3: Implement payment guard**

在 `payDemo` 开头检查 payment 能力；disabled 时设置非误导性错误/说明并返回。待支付按钮绑定 disabled/loading 状态；demo mode 显示“演示支付”，非 demo 不调用演示回调。不要隐藏套餐、权益或历史订单。

- [ ] **Step 4: Run focused tests to verify pass**

Run: `cd web-frontend; npm.cmd run test -- --run src/tests/membership-workflow.spec.ts`

Expected: PASS。

- [ ] **Step 5: Commit**

```bash
git add web-frontend/src/views/MembershipView.vue web-frontend/src/tests/membership-workflow.spec.ts web-frontend/src/lib/membership.ts
git commit -m "feat(web): make payment capability explicit"
```

### Task 4: 岗位匹配与专业报告提交前校验

**Files:**
- Modify: `web-frontend/src/views/JobsView.vue`
- Modify: `web-frontend/src/views/InsightsView.vue`
- Modify: `web-frontend/src/tests/interaction-state.spec.ts`
- Modify: `web-frontend/src/tests/domain-api.spec.ts` if request-level assertions are needed

**Interfaces:**
- Jobs reads `job_matching` capability; simplified mode remains usable when optional service is unavailable, while gated professional mode is stopped before `requestApi`。
- Insights reads the same capability context for professional report preflight; simplified mode remains usable。

- [ ] **Step 1: Add failing preflight tests**

断言 professional mode + capability disabled 时 jobs/insights 显示原因、提供会员/重试恢复动作且不发送查询请求；simplified mode 仍发送原请求；loading 时重复提交仍被忽略；后端 403 错误仍走现有 `ErrorNotice` 文案。

- [ ] **Step 2: Run focused tests to verify failure**

Run: `cd web-frontend; npm.cmd run test -- --run src/tests/interaction-state.spec.ts src/tests/domain-api.spec.ts`

Expected: FAIL on missing preflight checks。

- [ ] **Step 3: Implement mode gates and recovery UI**

在 `queryRole`/`queryInsights` 的输入校验之后、`loading = true` 之前检查能力；阻断时设置 inline error，不触发 API。专业模式按钮保留并置灰或附带说明；重试动作重新调用能力刷新函数，跳转会员使用现有 `navigate` 事件。不要改变请求 payload 或后端 403 处理。

- [ ] **Step 4: Run focused tests to verify pass**

Run: `cd web-frontend; npm.cmd run test -- --run src/tests/interaction-state.spec.ts src/tests/domain-api.spec.ts`

Expected: PASS。

- [ ] **Step 5: Commit**

```bash
git add web-frontend/src/views/JobsView.vue web-frontend/src/views/InsightsView.vue web-frontend/src/tests/interaction-state.spec.ts web-frontend/src/tests/domain-api.spec.ts
git commit -m "feat(web): preflight professional analysis modes"
```

### Task 5: 全量回归与发布验收

**Files:**
- Modify: `web-frontend/src/tests/capabilities.spec.ts` or affected test files only when failures reveal a specified gap
- No production files unless a test exposes a direct implementation defect

**Interfaces:**
- Validates the public capability service and all four consuming flows together。

- [ ] **Step 1: Run the complete Web test suite**

Run: `cd web-frontend; npm.cmd run test -- --run`

Expected: all existing and new Vitest tests pass。

- [ ] **Step 2: Run the production build**

Run: `cd web-frontend; npm.cmd run build`

Expected: Vite production build succeeds without TypeScript/Vue compiler errors。

- [ ] **Step 3: Check whitespace and inspect the diff**

Run: `git diff --check; git status --short; git log -5 --oneline`

Expected: no whitespace errors; only intended Web capability commits are present in this iteration, while unrelated pre-existing worktree changes remain untouched。

- [ ] **Step 4: Verify acceptance scenarios manually or with focused tests**

Check `/health` success, malformed response, and network failure; confirm password login/core workspace render in every case; confirm no disabled flow calls SMS/payment/professional endpoints; confirm demo labels are visible and 403 still presents recovery.

- [ ] **Step 5: Commit any test-only correction**

```bash
git add web-frontend/src/tests
git commit -m "test(web): cover capability trust loop"
```

Only create this final commit when Task 5 reveals a test gap that is explicitly covered by the specification; do not commit unrelated formatting or generated files.
