# 联网岗位搜索与简历生成体验实施计划

> **执行说明：** 本计划按测试驱动方式在 `feature/ai-resume-demo` 隔离工作树执行。除非用户后续明确要求，不执行推送、合并或 Pull Request 创建。

**目标：** 增强岗位联想、提供可选联网市场搜索、为完全空缺的项目/实习经历生成三条安全待确认草案，并优化岗位搜索页面的移动端交互。

**架构：** SQLite 本地岗位目录提供即时联想；可配置的 Tavily 服务提供用户主动触发的公开信息搜索；前端分别呈现目录与来源。简历补全仅追加 `[待确认]` 草案，保留用户已填写数据。

**技术栈：** FastAPI、Pydantic、SQLite、httpx、Vue 3、Uni-App、Vitest、pytest。

---

### 任务 1：先补充后端测试

**文件：**
- 修改：`resume-backend/tests/test_job_query_api.py`
- 新增：`resume-backend/tests/test_web_search.py`

**步骤：**
1. 为“数据”关联岗位和禁用联网搜索 API 写失败测试。
2. 用 `httpx.MockTransport` 为 Tavily 请求头、请求体和映射结果写失败测试。
3. 执行：
   `resume-backend\.venv\Scripts\python.exe -m pytest resume-backend/tests/test_job_query_api.py resume-backend/tests/test_web_search.py -v`
4. 确认新增测试在实现前失败。

### 任务 2：实现后端目录与联网搜索

**文件：**
- 修改：`resume-backend/app/config.py`
- 修改：`resume-backend/app/db.py`
- 修改：`resume-backend/app/services/ai_client.py`
- 修改：`resume-backend/app/schemas/job.py`
- 修改：`resume-backend/main.py`
- 修改：`resume-backend/app/api/ai.py`
- 新增：`resume-backend/app/services/web_search.py`
- 修改：`resume-backend/.env.example`

**步骤：**
1. 添加联网配置并以禁用模式作为默认后备。
2. 新增联网搜索模型、客户端工厂和 Tavily 实现。
3. 将客户端放入 `app.state`，增加只读市场搜索接口。
4. 扩展数据类岗位目录与 mock profile。
5. 重新执行任务 1 的 pytest 命令，确认通过。

### 任务 3：先补充前端测试

**文件：**
- 修改：`resume-miniprogram/src/tests/resume-autofill.spec.ts`
- 修改：`resume-miniprogram/src/tests/consultation-api.spec.ts`

**步骤：**
1. 更新空简历补全预期：两条项目草案和一条实习草案，已有数据不覆盖。
2. 为市场搜索 API 映射写失败测试。
3. 执行：
   `npm.cmd run test:unit -- resume-autofill.spec.ts consultation-api.spec.ts`
4. 确认新增测试在实现前失败。

### 任务 4：实现简历草案和前端岗位工作台

**文件：**
- 修改：`resume-miniprogram/src/types/consultation.ts`
- 修改：`resume-miniprogram/src/services/resume-api.ts`
- 修改：`resume-miniprogram/src/utils/resume-autofill.ts`
- 修改：`resume-miniprogram/src/pages/job-search/index.vue`
- 视需要修改：`resume-miniprogram/src/pages/resume-form/index.vue`

**步骤：**
1. 增加市场搜索类型与请求函数。
2. 用两条不同项目草案和一条实习草案替代单项目草案逻辑。
3. 将岗位建议改为清晰的下拉面板，增加岗位摘要、来源区和可折叠详情区。
4. 执行任务 3 的测试命令，确认通过。

### 任务 5：完整验证和本地预览

**步骤：**
1. 执行后端完整测试：
   `resume-backend\.venv\Scripts\python.exe -m pytest resume-backend/tests -v`
2. 执行前端完整测试：
   `npm.cmd run test:unit`
3. 执行构建：
   `npm.cmd run build:h5`
   `npm.cmd run build:mp-weixin`
4. 启动本地 FastAPI 与 H5 开发服务，检查岗位输入、身份选择、不同岗位结果、三条草案与禁用联网搜索提示。
5. 检查 `git diff`，只创建本地提交；不推送。
