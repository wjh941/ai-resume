# 面试讲述稿 / 项目深度导读

本文档面向两种读者：想在面试中讲清这个项目工程价值的开发者，以及想快速理解关键设计决策的新维护者。所有数字与文件引用均对应仓库当前代码，可逐一验证。

## 一、30 秒定位

> 这是一个三端求职工作台：FastAPI 后端、uni-app 小程序/H5、Vue3 Web 端，单仓库同一套 JWT 账号。功能上它把"经历证据 → 职业决策 → 简历制作 → 投递跟进"串成闭环；工程上我最在意的是三件事——**可量化的性能优化、故障场景下的系统行为、用结构而不是自觉保证的安全边界**。

## 二、三个 STAR 深度故事

### 故事 1：小程序主包 854KB → 448KB(-47.5%)

- **S/T**：微信小程序主包有 2MB 上限，构建产物里混入了只在 H5 有意义的静态工作台页（`premium-dashboard.html` 及其脚本），白占一半体积。
- **A**：没有用分包（那些页面根本不该进小程序产物），而是写了自定义 Vite 插件（`resume-miniprogram/vite.config.ts` 的 `stripH5OnlyPublicAssets`），在 `closeBundle` 钩子按 `UNI_PLATFORM === "mp-weixin"` 条件删除 H5 专有文件；再开启 `lazyCodeLoading: "requiredComponents"`（验证写入 dist 的 `app.json`）。产物体积分析确认 0 sourcemap、无冗余资源，剩余大头是 Vue 运行时 vendor（138KB），无可再挤。
- **R**：主包 854KB → 448KB（-47.5%），H5 产物与开发服务器不受影响；152 个单测全绿。
- **追问预案**：
  - *为什么不用分包？* 分包解决的是"页面太多"，这里的问题是"不属于该平台的产物混入"——正确的刀口是构建期剔除，分包反而把不属于小程序的东西合法化。
  - *怎么验证没删错？* H5 构建后 `premium-dashboard.html` 存在（`npm run build:h5` 后断言），mp-weixin 构建后不存在；`scripts/verify-premium-dashboard.mjs`。

### 故事 2：离线队列的分布式语义

- **S/T**：网络不可用时投递记录进入本机待同步队列（`stores/applications.ts`）。初版逻辑"失败就入队"有个隐患：服务端返回 422（参数校验失败）的记录也会入队，然后每次同步都失败，**毒丸记录阻塞整条队列**。
- **A**：http 层先做错误分类（`services/http.ts` 的 `ApiRequestError`：network/http/auth/business 四类），队列只收 `isRetryableApiError`（网络与 5xx）；同步时毒丸记录跳过并计数（`synced/remaining/skipped`），页面展示"X 条记录内容有误已跳过"；重试语义上 POST 不自动重试（非幂等）、GET 幂等重试一次（150ms）。
- **R**：队列不会死循环，用户得到明确反馈而不是"一直在同步"；152 个单测覆盖全部路径（入队/拒入队/毒丸隔离/断网中止）。
- **追问预案**：
  - *为什么 GET 才重试？* 幂等性。POST 重试可能造成重复创建。
  - *毒丸为什么跳过而不是丢弃？* 数据是用户的投递记录，跳过保序 + 明确提示，把删除权留给用户。

### 故事 3：纵深防御的安全边界

- **S/T**：三端共用后端，端口暴露面大；知识库官方数据源同步是重操作，不能任何登录用户都能触发。
- **A**：四层——①鉴权靠结构：所有业务路由在组装处统一注入 `Depends(current_user_id)`（`main.py` 注释原话"新增端点不会遗漏鉴权边界"），业务路由不从请求参数读身份；②RBAC：`require_operator` 依赖注入守写端点，前端按角色隐藏入口；③分场景限流：LLM 端点按用户 30 次/60s、公开认证端点、连客户端错误上报都按用户 10 次/60s（防日志灌水），429 带 `Retry-After` 标准信封；④JWT 带 `token_version`，登出/改密即时失效旧 token，密码只存 bcrypt 哈希。
- **R**：新增端点默认就在鉴权边界内；限流器共享一个带惰性过期和键数上限的 `InMemoryRateLimiter`（防内存膨胀），后端 234 个测试含限流、403、429 全路径。
- **追问预案**：
  - *进程内限流多实例怎么办？* 诚实答：单实例语义。生产多副本需要 Redis 滑动窗口——属于已识别的扩展点而非疏漏（`.env` 分层文档里写明了部署边界）。
  - *为什么连错误上报都限流？* 它是无业务价值的公开写入点，会被用来灌日志。

## 三、其他可讲的决策点（备选弹药）

| 决策 | 一句话讲述 | 代码位置 |
| --- | --- | --- |
| 测试对环境不设防 | 开发者本地 `.env` 曾让 3 个测试偶发失败，根因是 `_load_dotenv` 用 `setdefault` 注入；加 `RESUME_SKIP_DOTENV` 守卫后根除 | `tests/conftest.py`、`app/config.py` |
| 测试锁死实现细节 | Web 端用源码字符串断言钉住旧结构，重构时全碎；迁移为行为断言并补 composable 专项测试 | `web-frontend/src/tests/use-api-resource.spec.ts` |
| 全局错误防雪崩 | 同签名错误 60s 去重、会话上限 5 条上报、错误页跳转在途守卫 | `services/client-error-reporting.ts` |
| SQLite 写延迟 | WAL + `synchronous=NORMAL`，讲清"应用崩溃不丢、断电可能回滚最近事务"的权衡 | `app/db.py` |
| AI 诚实体感 | 未配置 AI 返回 `ai_not_configured` 明确降级，绝不造假数据；简历未知经历保留 `[待确认]` | `app/services/ai_client.py` |
| 依赖瘦身 | requirements 拆 base + 惰性导入 extras；Docker 默认 weasyprint（修掉容器内 PDF 必挂的问题） | `requirements.txt`、`Dockerfile` |

## 四、演示脚本（5 分钟）

1. `powershell -File scripts/start-resume-backend.ps1`（或直接 uvicorn）——`/health` 显示能力声明。
2. `resume-backend\.venv\Scripts\python.exe -X utf8 scripts\smoke_e2e.py`——30 秒跑完 10 步全链路，屏幕上直接出现真实延迟数字。
3. 打开 Web 工作台演示暗色模式持久化；小程序开发者工具导入 `dist/build/mp-weixin` 演示包体积（微信工具里可见主包 < 500KB）。
4. 断网点一次"保存投递"，恢复网络点"重试同步"——演示离线队列与跳过提示。

## 五、弱点与预案（主动说）

- **单人项目**：用流程回答——630 测试、每阶段强制全量回归、可重复冒烟脚本、提交按模块拆分，用工程纪律替代协作评审。
- **SQLite 而不是 MySQL**：场景匹配（个人部署零运维），PostgreSQL 迁移文档与 alembic 链路已备（`docs/POSTGRESQL_MIGRATION.md`）。
- **AI 能力看起来"假"**：capability 门控是刻意设计——没有 KEY 就明确说没有，绝不 Mock 造假；真实接入只需配 env 三项。
- **列表无分页**：如实承认是个人规模取向，已写入部署检查文档作为已知限制。
