# Web Trust State Polish Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让岗位匹配和年度洞察准确区分真实/演示/不可用状态，并提供真正禁用、可恢复且不会残留旧错误的交互反馈。

**Architecture:** JobsView 与 InsightsView 继续消费上一轮共享 `CapabilityContext`，新增派生状态和 watch 逻辑，不复制后端能力规则。模板使用原生 `disabled`、`aria-describedby` 和统一状态文案；base.css 提供中性色状态样式。jsdom 运行时测试验证最终 DOM、事件和请求行为。

**Tech Stack:** Vue 3.5、TypeScript、Vitest、Vue Test Utils、jsdom、现有 CSS tokens。

## Global Constraints

- 只修改 `web-frontend/src/views/JobsView.vue`、`web-frontend/src/views/InsightsView.vue`、`web-frontend/src/styles/base.css` 及相关测试。
- 不修改后端、API endpoint/payload、支付协议、移动端、主题持久化或其他页面 Demo 文案。
- Demo 状态必须标记为“专业版（演示）”并说明本地/演示数据不代表实时职位或真实市场洞察。
- 不可用专业模式必须使用原生 `disabled`，不能被选中或提交；简化模式保持可用。
- 能力刷新成功清除旧 capability error；刷新失败保留旧状态和输入内容；不自动重复查询。
- 全量 Vitest、生产构建和 `git diff --check` 必须通过。

---

### Task 1: Jobs/Insights 状态模型与同步

**Files:**
- Modify: `web-frontend/src/views/JobsView.vue`
- Modify: `web-frontend/src/views/InsightsView.vue`
- Modify: `web-frontend/src/tests/interaction-state.spec.ts`

**Interfaces:**
- Produce computed state in each view: `jobMatchingState` (`loading`/`real`/`demo`/`disabled`), `professionalModeLabel`, `capabilityHint`, and `capabilityNotice` behavior.
- Consume shared `context.capabilities`, `context.refreshing`, and `context.refresh` from `CAPABILITIES_KEY`.

- [ ] **Step 1: Write failing state tests**

增加源码/状态测试，要求两个页面读取 capability `mode`；当能力由 enabled 变 disabled 且当前为 professional 时，模式回退为 simplified；刷新成功清除 capability error，刷新失败保留 error；输入 role/year 值不变。

- [ ] **Step 2: Run focused tests and verify failure**

Run: `cd web-frontend; npm.cmd run test -- --run src/tests/interaction-state.spec.ts`

Expected: FAIL because views currently use only boolean enabled and do not watch capability transitions.

- [ ] **Step 3: Implement minimal state synchronization**

为两个页面增加 `watch(jobMatchingEnabled, ...)`：从 true 变 false 时将 `reportMode` 设为 `simplified` 并保留输入；从 false 变 true 时清空 `capabilityNotice`。重试函数只调用共享 `context.refresh()`，成功后根据最新状态更新 notice，失败保留当前 notice。增加 mode/loading/demo 的 computed label，不改变查询 payload。

- [ ] **Step 4: Run focused tests and verify pass**

Run: `cd web-frontend; npm.cmd run test -- --run src/tests/interaction-state.spec.ts`

Expected: PASS。

- [ ] **Step 5: Commit**

```bash
git add web-frontend/src/views/JobsView.vue web-frontend/src/views/InsightsView.vue web-frontend/src/tests/interaction-state.spec.ts
git commit -m "fix(web): synchronize capability mode state"
```

### Task 2: 三态模板、恢复动作与可访问性

**Files:**
- Modify: `web-frontend/src/views/JobsView.vue`
- Modify: `web-frontend/src/views/InsightsView.vue`
- Modify: `web-frontend/src/tests/capability-runtime.spec.ts`

**Interfaces:**
- Professional mode buttons expose native `disabled`, `aria-describedby`, and a stable status element id when unavailable/loading.
- Recovery actions emit existing `navigate('membership')` and call shared `context.refresh()`.

- [ ] **Step 1: Write failing runtime tests**

在 jsdom 测试中注入 disabled/demo/loading contexts，断言：professional button 的 `disabled` 属性；原因文本与 `aria-describedby` 关联；按钮不能切换到 professional；mode 区直接出现“重试服务状态”和“查看会员权益”；会员按钮发出 navigate；重试按钮使用共享 refresh/loading。

- [ ] **Step 2: Run runtime tests and verify failure**

Run: `cd web-frontend; npm.cmd run test -- --run src/tests/capability-runtime.spec.ts`

Expected: FAIL because buttons currently use only `aria-disabled`, lack linked status ids, and recovery actions appear only after submit.

- [ ] **Step 3: Implement template behavior**

专业按钮在 `!jobMatchingEnabled || capabilityRefreshing` 时使用 `:disabled`，绑定稳定的 `aria-describedby`；加载状态显示“检查中”，disabled 状态显示能力 notice。恢复动作放入模式区，重试按钮绑定 `capabilityRefreshing`，会员按钮触发现有 navigate。结果顶部和 mode label 使用 Task 1 的 demo-aware label；不要自动触发查询。

- [ ] **Step 4: Run runtime tests and verify pass**

Run: `cd web-frontend; npm.cmd run test -- --run src/tests/capability-runtime.spec.ts`

Expected: PASS。

- [ ] **Step 5: Commit**

```bash
git add web-frontend/src/views/JobsView.vue web-frontend/src/views/InsightsView.vue web-frontend/src/tests/capability-runtime.spec.ts
git commit -m "feat(web): clarify professional capability states"
```

### Task 3: 统一不可用与演示视觉样式

**Files:**
- Modify: `web-frontend/src/styles/base.css`
- Modify: `web-frontend/src/tests/interaction.spec.ts` or `capability-runtime.spec.ts`

**Interfaces:**
- Produce `.mode-notice`, `.mode-notice.is-demo`, `.mode-notice.is-unavailable`, `.mode-switch button.is-unavailable`, and `[aria-disabled="true"]` style rules using existing CSS variables.

- [ ] **Step 1: Add failing style contract tests**

断言 base.css 包含中性色 mode-notice、disabled cursor/opacity、selected 与 unavailable 的优先级规则，以及 demo 信息色规则；断言不使用成功绿或促销色作为 demo 状态。

- [ ] **Step 2: Run focused tests and verify failure**

Run: `cd web-frontend; npm.cmd run test -- --run src/tests/interaction.spec.ts`

Expected: FAIL because the new selectors are absent。

- [ ] **Step 3: Implement scoped styles**

使用 `var(--surface-muted)`、`var(--line)`、`var(--muted)`、`var(--primary-tint)` 等现有 token；让 `.mode-switch button.is-unavailable` 覆盖 `.is-selected` 的视觉强调，增加 `cursor: not-allowed`；`.mode-notice` 支持内联操作按钮布局与窄屏换行。避免新增渐变、圆角卡片或单色装饰。

- [ ] **Step 4: Run focused tests and verify pass**

Run: `cd web-frontend; npm.cmd run test -- --run src/tests/interaction.spec.ts`

Expected: PASS。

- [ ] **Step 5: Commit**

```bash
git add web-frontend/src/styles/base.css web-frontend/src/tests/interaction.spec.ts web-frontend/src/tests/capability-runtime.spec.ts
git commit -m "style(web): distinguish unavailable analysis states"
```

### Task 4: 全量回归与发布验收

**Files:**
- Modify: test files only if an explicit acceptance gap is exposed
- No unrelated production files

**Interfaces:**
- Validates Jobs/Insights state transitions, runtime gates, visual contracts, and existing Web behavior together.

- [ ] **Step 1: Run complete Web tests**

Run: `cd web-frontend; npm.cmd run test -- --run`

Expected: all test files pass, including runtime demo/disabled/recovery cases.

- [ ] **Step 2: Run production build**

Run: `cd web-frontend; npm.cmd run build`

Expected: Vite build succeeds without template/compiler errors.

- [ ] **Step 3: Check diff and scope**

Run: `git diff --check; git status --short; git log --oneline -10`

Expected: no whitespace errors; only intended Web files changed by this iteration; unrelated pre-existing worktree changes preserved.

- [ ] **Step 4: Verify acceptance scenarios**

确认 demo/real/disabled/loading 状态可区分；disabled 专业按钮不可点击且原因关联；恢复动作可用；能力恢复清除旧错误；能力降级回退简化并保留输入；简化查询、密码登录、套餐/订单和 403 回归正常。

- [ ] **Step 5: Commit only an explicitly specified correction**

```bash
git add web-frontend/src/tests
git commit -m "test(web): close trust state coverage gap"
```

仅当验收发现规格明确要求但测试未覆盖的缺口时创建该提交，否则不产生空提交。
