# Web 工作区连续性实施计划

## 任务 1：路由纯函数

- 新增 `web-frontend/src/lib/workspace-route.ts`。
- 提供 URL 解析、序列化和页面标题函数。
- 先以 Vitest 覆盖默认值、无效值、编辑上下文、参数保留和标题。

## 任务 2：接入应用壳

- 从 URL 初始化 `activeView` 与 `editingDraftId`。
- 侧边栏、打开简历、保存/取消编辑写入历史记录。
- 监听 `popstate`，复用导航守卫恢复或延迟目标。
- 使用统一标题反映当前页面。

## 任务 3：验证

- 运行 Web 全量测试和 TypeScript 构建。
- 运行界面静态检测，确认本轮改动没有新增体验反模式。
