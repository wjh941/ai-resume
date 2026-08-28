# Web 运行时能力测试与全局刷新设计

## 背景与目标

当前 Web 已接入能力状态，但 Jobs/Insights 的重试使用局部 `capabilityOverride`，不同页面可能看到不一致的服务状态；新增测试主要是源码契约，无法证明按钮 disabled、请求抑制和提示渲染等真实行为。本轮建立共享能力控制器，并用真实 Vue 组件挂载测试验证受保护入口的运行时行为。

## 范围

本轮只修改 `web-frontend` 及其测试配置和开发依赖，不改变后端接口、请求 endpoint/payload、主题视觉、Demo 文案或移动端导航。保留现有纯函数和源码契约测试，新增组件级运行时覆盖。

## 共享能力控制器

`web-frontend/src/lib/capabilities.ts` 在现有 `Capabilities` 映射基础上提供统一上下文：

```ts
interface CapabilityContext {
  capabilities: Readonly<Ref<Capabilities>>
  refreshing: Readonly<Ref<boolean>>
  refresh: () => Promise<Capabilities>
}
```

`createCapabilityContext()` 创建默认 disabled 状态、刷新状态和 `refresh()`。`refresh()` 使用现有 `/health` 映射服务；请求期间设置 `refreshing`，成功后原子替换共享能力。初次请求失败保持默认 disabled；已有有效状态后的重试失败则保留最近一次有效状态。`CAPABILITIES_KEY` 类型扩展为该上下文。

`App.vue` 创建唯一上下文并在启动时非阻塞调用一次 `refresh()`。`LoginPanel`、`MembershipView`、`JobsView`、`InsightsView` 均注入同一上下文。页面重试直接调用 `refresh()`，删除局部 `capabilityOverride`，并使用共享 `refreshing` 防止并发。

未挂载在 App 下的单组件通过 `createCapabilityContext()` 作为注入缺省值，不触发网络请求；这保证组件测试和异步页面加载都能安全运行。为实现失败后保留最近状态，`getCapabilities` 接受可选 fallback，首次使用默认值，重试时传入当前状态。

## 运行时测试方案

开发依赖增加 `@vue/test-utils` 和 `jsdom`。新增测试文件在顶部声明 `@vitest-environment jsdom`，不改变现有纯函数测试环境。

- LoginPanel：注入 disabled/ready 能力，验证短信 tab 的 disabled 属性、说明文案；能力由可用变为 disabled 后点击获取验证码不调用 `/api/auth/send-code`；密码登录仍可提交。
- MembershipPackageCard：payment disabled 时购买按钮真实 disabled、显示原因且不发出 `purchase` 事件；enabled 时保留原事件。
- JobsView/InsightsView：填写岗位并选择专业模式，在 `job_matching` disabled 时提交不调用查询 API，显示能力说明和重试动作；简化模式仍调用原 endpoint 并发送原 payload。
- CapabilityContext：验证 refresh 的 refreshing 生命周期、成功后多个消费者读取同一新状态、失败时保持安全回退。

运行时测试 mock `requestApi` 和能力请求，不启动后端，不复制会员权限规则。现有源码契约测试继续保留，作为接线回归。

## 错误与兼容性

刷新失败不清空用户输入，不阻塞密码登录、简历编辑、套餐/订单展示和简化查询。后端 403 仍由现有 `ErrorNotice` 处理。能力上下文只负责可选能力预检，不替代服务端鉴权。

`@vue/test-utils`、`jsdom` 仅加入 `devDependencies`，不会进入生产构建。保留 `CAPABILITIES_KEY` 导出名称，页面 endpoint、payload 和后端字段映射保持不变。

## 验收标准

1. App 只创建一个能力上下文；任一页面重试能同步其他消费者，无局部 override。
2. `refreshing` 在请求期间为 true，重复重试被忽略，请求完成后恢复 false。
3. 真实挂载测试证明 disabled 短信、支付购买和专业查询不发起受保护请求。
4. 密码登录、简化岗位/报告、套餐与订单展示、后端 403 提示保持可用。
5. 完整 Vitest、生产构建和 `git diff --check` 全部通过。

## 非目标

不增加 Demo 状态文案、不新增不可用入口视觉样式、不实现主题持久化、不修改移动端抽屉无障碍、不修改后端能力或支付协议。
