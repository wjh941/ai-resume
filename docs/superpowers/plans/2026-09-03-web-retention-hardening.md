# Web 留存链路加固实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task with verification checkpoints.

**Goal:** 保留工作区状态、正确处理会话过期，并让账户导出和岗位资料补全都能在 Web 内完成。

**Architecture:** 继续使用现有 Vue 应用壳和 Fetch 封装。KeepAlive 负责视图生命周期；API 层负责统一 401 事件与鉴权下载；账户页只编排导出请求和浏览器下载。

**Tech Stack:** Vue 3、TypeScript、Vitest、原生 Fetch/Blob/URL API。

## Global Constraints

- 不新增 npm 依赖。
- 不改变既有后端 API 路径和响应契约。
- 所有用户可见文字使用简体中文。

---

### Task 1: 视图保留与会话过期事件

**Files:**
- Modify: `web-frontend/src/App.vue`
- Modify: `web-frontend/src/lib/api.ts`
- Test: `web-frontend/src/tests/workspace-navigation.spec.ts`
- Test: `web-frontend/src/tests/api.spec.ts`

- [x] 先增加 KeepAlive、popstate 过期监听和 401 事件的失败断言。
- [x] 运行对应测试确认因实现缺失而失败。
- [x] 在 App 动态视图外加入 KeepAlive，在 API 401 分支派发固定事件，并由 App 切换登录态。
- [x] 运行路由、API 和交互测试确认通过。

### Task 2: 鉴权二进制下载与账户导出

**Files:**
- Modify: `web-frontend/src/lib/api.ts`
- Create: `web-frontend/src/lib/download-file.ts`
- Modify: `web-frontend/src/views/AccountView.vue`
- Test: `web-frontend/src/tests/download-file.spec.ts`

- [x] 先测试 Blob 下载链接创建、点击和 URL 清理行为。
- [x] 运行测试确认失败。
- [x] 实现 `downloadApi` 和最小下载触发器，账户页调用 POST 准备接口后下载 GET ZIP。
- [x] 运行下载和账户静态契约测试确认通过。

### Task 3: 跨端提示与最终验证

**Files:**
- Modify: `web-frontend/src/views/ComparisonView.vue`
- Modify: `web-frontend/src/tests/interaction.spec.ts`

- [x] 先增加 Web 端资料补全提示的失败断言。
- [x] 运行测试确认失败。
- [x] 改为导航到当前 Web 的职业规划页面，并保留可继续操作的文案。
- [x] 运行 Web 全量测试、生产构建和 Impeccable 检测。
