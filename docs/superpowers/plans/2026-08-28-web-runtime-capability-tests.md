# Web Runtime Capability Tests Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 用共享能力控制器替换页面局部 override，并以真实 Vue 挂载测试验证短信、支付和专业查询在不可用状态下不会发起受保护请求。

**Architecture:** `lib/capabilities.ts` 提供 `CapabilityContext`、上下文工厂和共享 `refresh()`；`App.vue` 创建唯一实例并注入，所有页面读取同一响应式状态。测试仅在新的 jsdom 运行时文件中挂载组件，mock `requestApi`/能力请求，既保留现有源码契约测试，也验证最终 DOM 与事件行为。

**Tech Stack:** Vue 3.5、TypeScript、Vitest 2.1、Vite 5.2.8、`@vue/test-utils`、jsdom。

## Global Constraints

- 只修改 `web-frontend` 及其测试配置和开发依赖，不修改后端接口、请求 endpoint/payload、主题视觉、Demo 文案或移动端导航。
- 首次能力请求失败保持默认 disabled；已有有效状态后的重试失败保留最近一次有效状态。
- 所有页面使用同一个 `CapabilityContext`，删除 Jobs/Insights 局部 `capabilityOverride`。
- disabled 短信、支付购买和专业查询不得发起受保护请求；密码登录、简化查询、套餐/订单展示和后端 403 行为保持可用。
- `@vue/test-utils`、jsdom 仅加入 `devDependencies`，不进入生产构建。

---

### Task 1: 共享能力上下文

**Files:**
- Modify: `web-frontend/src/lib/capabilities.ts`
- Modify: `web-frontend/src/tests/capabilities.spec.ts`

**Interfaces:**
- Add `CapabilityContext` with `capabilities: Readonly<Ref<Capabilities>>`, `refreshing: Readonly<Ref<boolean>>`, and `refresh: () => Promise<Capabilities>`。
- Add `createCapabilityContext(): CapabilityContext`。
- Preserve `CAPABILITIES_KEY`, `defaultCapabilities`, `mapCapabilities`, `getCapabilities`, and `isCapabilityEnabled` exports.

- [ ] **Step 1: Write failing context tests**

在 `capabilities.spec.ts` 增加：首次上下文状态等于默认 disabled；`refresh()` 将 `refreshing` 设为 true，成功后替换 capabilities 并恢复 false；刷新进行中再次调用不产生第二次请求；首次失败仍为默认值；已有有效状态后失败保留旧值。

- [ ] **Step 2: Run focused tests and verify failure**

Run: `cd web-frontend; npm.cmd run test -- --run src/tests/capabilities.spec.ts`

Expected: FAIL because `CapabilityContext` and `createCapabilityContext` are not defined。

- [ ] **Step 3: Implement context and fallback semantics**

为 `getCapabilities` 增加可选 fallback 参数，默认仍为 `defaultCapabilities()`；上下文 `refresh()` 记录当前状态，调用期间设置 `refreshing`，成功替换状态，失败传入当前状态作为 fallback。并发调用直接返回当前 promise/状态，不发起重复 `/health` 请求。

- [ ] **Step 4: Run focused tests and verify pass**

Run: `cd web-frontend; npm.cmd run test -- --run src/tests/capabilities.spec.ts`

Expected: PASS。

- [ ] **Step 5: Commit**

```bash
git add web-frontend/src/lib/capabilities.ts web-frontend/src/tests/capabilities.spec.ts
git commit -m "feat(web): centralize capability refresh state"
```

### Task 2: App 与页面迁移到共享上下文

**Files:**
- Modify: `web-frontend/src/App.vue`
- Modify: `web-frontend/src/components/LoginPanel.vue`
- Modify: `web-frontend/src/views/MembershipView.vue`
- Modify: `web-frontend/src/views/JobsView.vue`
- Modify: `web-frontend/src/views/InsightsView.vue`
- Modify: `web-frontend/src/tests/interaction.spec.ts`
- Modify: `web-frontend/src/tests/interaction-state.spec.ts`

**Interfaces:**
- `App.vue` creates one `createCapabilityContext()` instance and provides it with `CAPABILITIES_KEY`; startup calls `context.refresh()` once。
- All consumers inject `CapabilityContext`; Jobs/Insights use `context.refreshing` and `context.refresh`, with no local `capabilityOverride` or direct `getCapabilities` call。

- [ ] **Step 1: Add failing migration assertions**

断言 App 使用 `createCapabilityContext` 并只调用上下文刷新；Jobs/Insights 不再包含 `capabilityOverride`；重试调用 `refresh` 且读取共享 refreshing；登录和会员仍消费同一 key。

- [ ] **Step 2: Run focused tests and verify failure**

Run: `cd web-frontend; npm.cmd run test -- --run src/tests/interaction.spec.ts src/tests/interaction-state.spec.ts`

Expected: FAIL because current views still use local overrides/direct requests。

- [ ] **Step 3: Migrate production consumers**

替换 App 的 ref/Promise 初始化为上下文工厂；页面通过 `const capabilityContext = inject(CAPABILITIES_KEY, createCapabilityContext())` 读取 `capabilityContext.capabilities.value`。Jobs/Insights 的重试直接 `await capabilityContext.refresh()`，使用共享 `capabilityContext.refreshing.value` 绑定按钮 loading；保留原 endpoint、payload、错误和恢复事件。

- [ ] **Step 4: Run focused tests and verify pass**

Run: `cd web-frontend; npm.cmd run test -- --run src/tests/interaction.spec.ts src/tests/interaction-state.spec.ts`

Expected: PASS。

- [ ] **Step 5: Commit**

```bash
git add web-frontend/src/App.vue web-frontend/src/components/LoginPanel.vue web-frontend/src/views/MembershipView.vue web-frontend/src/views/JobsView.vue web-frontend/src/views/InsightsView.vue web-frontend/src/tests/interaction.spec.ts web-frontend/src/tests/interaction-state.spec.ts
git commit -m "refactor(web): share capability refresh context"
```

### Task 3: 配置组件级运行时测试环境

**Files:**
- Modify: `web-frontend/package.json`
- Modify: `web-frontend/package-lock.json`
- Create: `web-frontend/src/tests/capability-runtime.spec.ts`

**Interfaces:**
- The new test file runs under jsdom via `// @vitest-environment jsdom` and imports `mount` from `@vue/test-utils`。
- Test helpers provide a `CapabilityContext` through `CAPABILITIES_KEY` and stub child components/icons as needed。

- [ ] **Step 1: Add dependency installation and a failing mount smoke test**

运行 `cd web-frontend; npm.cmd install --save-dev @vue/test-utils jsdom`，在新测试文件写一个挂载 `LoginPanel` 的 smoke test，断言存在密码输入框。

- [ ] **Step 2: Run smoke test and verify environment failure/success boundary**

Run: `cd web-frontend; npm.cmd run test -- --run src/tests/capability-runtime.spec.ts`

Expected: the test executes in jsdom; before component behavior assertions are added, only the smoke test should pass。

- [ ] **Step 3: Commit test environment setup**

```bash
git add web-frontend/package.json web-frontend/package-lock.json web-frontend/src/tests/capability-runtime.spec.ts
git commit -m "test(web): add component runtime environment"
```

### Task 4: 补齐真实组件行为覆盖

**Files:**
- Modify: `web-frontend/src/tests/capability-runtime.spec.ts`
- Modify: `web-frontend/src/tests/capabilities.spec.ts` only if shared helper coverage needs a focused correction

**Interfaces:**
- Tests use `mount(Component, { global: { provide: { [CAPABILITIES_KEY as symbol]: context }, stubs: ... } })` and mock `requestApi` at module boundaries。
- No production endpoint/payload changes are allowed。

- [ ] **Step 1: Write failing runtime behavior tests**

加入以下测试：LoginPanel disabled SMS tab 与说明渲染；能力由 enabled 变 disabled 后提交短信表单不调用 `/api/auth/send-code`，密码表单仍可触发登录；MembershipPackageCard disabled payment 不发 `purchase` 事件，enabled 发出原参数；JobsView/InsightsView 专业模式 disabled 时提交不调用查询 API、显示能力错误和重试按钮，简化模式发送原 payload；两个消费者在 context.refresh 后同时看到新能力状态。

- [ ] **Step 2: Run runtime tests and verify failure**

Run: `cd web-frontend; npm.cmd run test -- --run src/tests/capability-runtime.spec.ts`

Expected: FAIL on the current local override behavior or missing runtime guards。

- [ ] **Step 3: Adjust only test-safe production defects**

若失败来自共享上下文迁移遗漏，修正对应页面注入；若是测试 stub 配置问题，修正测试 helper。不得改变既定 endpoint、payload、文案范围或后端鉴权。

- [ ] **Step 4: Run runtime tests and verify pass**

Run: `cd web-frontend; npm.cmd run test -- --run src/tests/capability-runtime.spec.ts`

Expected: all runtime assertions pass。

- [ ] **Step 5: Commit**

```bash
git add web-frontend/src/tests/capability-runtime.spec.ts web-frontend/src/lib/capabilities.ts web-frontend/src/views web-frontend/src/components/LoginPanel.vue
git commit -m "test(web): verify capability gates at runtime"
```

### Task 5: 全量回归与发布验收

**Files:**
- Modify: test files only if a specified acceptance gap is exposed
- No unrelated production files

**Interfaces:**
- Verifies the shared context and all existing Web flows together。

- [ ] **Step 1: Run the complete Web suite**

Run: `cd web-frontend; npm.cmd run test -- --run`

Expected: all existing and runtime tests pass。

- [ ] **Step 2: Run the production build**

Run: `cd web-frontend; npm.cmd run build`

Expected: Vite build succeeds and test-only dependencies do not appear in production output。

- [ ] **Step 3: Check diff and scope**

Run: `git diff --check; git status --short; git log --oneline -8`

Expected: no whitespace errors; only intended Web files are changed by this iteration; unrelated pre-existing worktree changes remain untouched。

- [ ] **Step 4: Verify acceptance scenarios**

确认初次 `/health` 失败仍可密码登录；有效状态后重试失败保留旧状态；任一页面重试同步其他页面；disabled 短信、支付购买和专业查询无受保护请求；简化模式、套餐/订单和 403 恢复正常。

- [ ] **Step 5: Commit only an explicitly specified test correction**

```bash
git add web-frontend/src/tests
git commit -m "test(web): close runtime capability coverage gap"
```

仅当 Task 5 发现规格明确要求但测试未覆盖的缺口时创建该提交，否则不产生空提交。
