# AI 岗位查询与智能简历生成

一个本地可运行的求职辅助 Demo，包含 Uni-App 微信小程序前端与 FastAPI 后端。

仓库地址：`https://github.com/wjh941/ai-resume`

## 功能

- 岗位情报查询与关联岗位联想
- 按求职身份生成岗位解析、求职建议和工具箱内容
- 简历填写、AI 润色、模板预览、草稿保存与 Word/PDF 导出
- 空白经历生成带 `[待确认]` 标记的项目、实习草稿，不虚构事实
- 经历证据库：先记录真实课程、项目、实习或工作经历，再按目标岗位生成可确认的简历草案
- 简历就绪检查：缺少姓名、手机号、邮箱或目标岗位时阻止模板预览；待确认内容必须由用户明确确认
- 求职志愿规划：基于专业、技能、城市和行业偏好，输出冲刺、稳妥、保底三档岗位建议
- 岗位横向对比：选择 2-4 个本地岗位，比较匹配依据、技能缺口、风险提示与 7/30/90 天行动计划
- 12 个岗位大类、204 个标准岗位、36 个专业的本地知识库
- 岗位匹配评分、专业匹配报告、技能缺口与补齐行动建议
- 可选联网市场信息检索；默认关闭，不会爬取招聘平台

## 目录

```text
ai-resume/
├─ resume-backend/       # FastAPI、SQLite、导出服务与岗位推荐引擎
├─ resume-miniprogram/   # Uni-App Vue 3 小程序
└─ docs/                 # 设计与实施文档
```

## 环境

- Windows 10/11
- Python 3.11+
- Node.js 20+
- npm 10+
- 微信开发者工具，仅在编译或预览微信小程序时需要

## 本地启动

### 1. 启动后端

```powershell
cd resume-backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

健康检查地址：`http://127.0.0.1:8000/health`

### 2. 启动 H5 预览

另开一个 PowerShell 窗口：

```powershell
cd resume-miniprogram
npm install
Copy-Item .env.example .env.local
npm run dev:h5
```

控制台会输出本地访问地址，通常为 `http://127.0.0.1:5173`。浏览器打开后，从首页点击“求职志愿规划”即可使用三档职业推荐。

`VITE_RESUME_API_URL` 留空时，H5 开发服务器会将 `/api` 和 `/downloads` 代理到本机后端 `http://127.0.0.1:8000`。部署 H5 或编译微信小程序前，请在 `resume-miniprogram/.env.local` 中填写已部署的 HTTPS 后端地址，例如：

```dotenv
VITE_RESUME_API_URL=https://api.example.com
```

### 3. 构建微信小程序

```powershell
cd resume-miniprogram
npm run build:mp-weixin
```

打开微信开发者工具，导入以下目录：

```text
resume-miniprogram/dist/build/mp-weixin
```

真机、模拟器与正式小程序必须使用可访问的 HTTPS 后端地址：在 `resume-miniprogram/.env.local` 配置 `VITE_RESUME_API_URL` 后重新构建，并在微信小程序后台配置对应的合法域名。无需修改前端源码；前端环境变量不得存放 API Key 等敏感信息。

## AI 与联网配置

后端使用 `resume-backend/.env` 读取配置。默认 `AI_PROVIDER=mock`，无需 API Key 即可演示。

```dotenv
AI_PROVIDER=mock
AI_API_KEY=
AI_BASE_URL=https://ark.cn-beijing.volces.com/api/v1
AI_MODEL=

# 可选：授权公开网页搜索，默认关闭
WEB_SEARCH_PROVIDER=disabled
TAVILY_API_KEY=
```

- 使用豆包或 OpenAI 兼容接口时，填写 API Key、Base URL 与模型名。
- `WEB_SEARCH_PROVIDER` 仅在具备合法 API 授权时开启。
- 项目不包含招聘网站爬虫、登录绕过或批量抓取。

## 测试与构建

### 后端

```powershell
cd resume-backend
.\.venv\Scripts\python.exe -m pytest tests -v
```

### 前端

```powershell
cd resume-miniprogram
npm run test:unit
npm run build:h5
npm run build:mp-weixin
```

## 数据与隐私

- 草稿、岗位缓存、职业画像默认存储在本地 SQLite 数据库。
- 经历证据按本机匿名 `client_id` 隔离保存，仅作为当前设备上的简历辅助资料。
- 职业规划评分用于比较求职方向，不代表录用概率、薪资承诺或岗位保证。
- 简历补全只生成待确认草稿，不会把未知经历写成真实事实。

## 经历证据与简历检查

1. 在“填写简历”页的“经历证据库”入口中，录入真实课程、项目、校园活动、实习或工作经历。
2. 填写目标岗位后，表单会显示最多三条岗位相关建议；点击“写入空白区”只会写入尚无内容的项目或实习区，不会覆盖已有经历。
3. 没有真实成果、时间、公司或可验证材料时，保留 `[待确认]` 标记；导出前应替换为真实信息，或删除不准备展示的草案。
4. 删除证据只会删除证据库条目，不会追溯修改已保存的简历草稿、Word 或 PDF 文件。

## 岗位对比与行动计划

1. 在“求职志愿规划”中将 2-4 个推荐岗位加入对比，再点击“查看对比”。
2. 对比仅使用本地岗位库、保存的职业画像、可选职业测评结果以及用户主动确认的经历证据；不会请求招聘网站职位描述。
3. 已确认经历中的既有技能词可补充技能评分；未确认资料不会消除技能缺口，也不会被改写。
4. 分数仅用于比较求职方向，不是录用概率、薪资结果或市场预测。选择“设为本周主目标”只保存当前方向，后续可据此安排简历与投递计划。

## 后续扩展

- 将 SQLite 迁移至 MySQL/PostgreSQL
- 接入已授权的招聘数据源或企业 ATS 数据
- 增加登录、多端同步、付费套餐和团队版能力
- 将 H5 前端与 FastAPI 部署到 HTTPS 域名，供微信小程序正式调用
## 职业测评与年度洞察

- 新增四步职业测评：兴趣偏好、工作方式、专长证据、现实约束；使用 1-5 分量表，可跳过题目。
- 测评结果只把高分且有真实证据的内容作为职业信号，并输出 7 / 30 / 90 天可执行计划。
- 已完成的测评会作为可选 `assessment_guidance` 附加到职业规划结果，不改变原有冲刺、稳妥、保底三档推荐数据。
- 年度就业洞察仅保存本地归档的公开静态资料摘要，并强制保留来源、发布日期和置信说明；项目不提供招聘网站爬虫或职位描述抓取功能。
- 小程序入口：首页的“职业测评”，或“求职志愿规划”页顶部的“先做职业测评”。

详细操作与资料来源要求见 [职业测评与年度洞察操作说明](docs/graduate-career-assessment-operations.md)。
