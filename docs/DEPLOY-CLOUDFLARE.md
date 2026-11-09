# 部署到 Cloudflare:能做什么、不能做什么(2026-11-06)

## 结论先行

| 组件 | 能否上 Cloudflare | 方式 |
| --- | --- | --- |
| 落地页 `site/` | ✅ 完全可以 | Cloudflare Pages(直传静态目录) |
| Web 端 `web-frontend/dist` | ✅ 完全可以 | Cloudflare Pages(Vite 构建产物) |
| 小程序/H5 | H5 同理可发 Pages | uni-app H5 构建产物 |
| **后端 FastAPI** | ❌ **不适合 Workers** | 见下方「后端复活方案」 |

后端不上 Workers 的三个硬原因:

1. **运行模型不匹配**——Workers 没有可监听的 socket,uvicorn 的 `listen/accept` 模型跑不起来(Python Workers 走 Pyodide + fetch handler,还是 beta);
2. **依赖轮子**——bcrypt(rust 核心)、SQLAlchemy+alembic 链条在 Pyodide 环境没有现成 wheel;
3. **SQLite 持久化**——Workers 文件系统是临时的,SQLite 落盘即失;要持久得换 D1(方言迁移=重写数据层)。

## 静态端上线步骤(约 10 分钟)

1. Cloudflare Dashboard → 右上角头像 → **My Profile → API Tokens → Create Token**,选 **Cloudflare Pages — Edit** 权限模板
2. 同页拿到 **Account ID**(右栏)
3. GitHub 仓库 → Settings → Secrets and variables → Actions → 添加两个 secret:
   - `CLOUDFLARE_API_TOKEN`
   - `CLOUDFLARE_ACCOUNT_ID`
4. Actions 页选 **cloudflare-pages** → **Run workflow**
5. 完成后得到:`https://ai-resume-landing.pages.dev` 与 `https://ai-resume-web.pages.dev`

## 后端复活方案(二选一)

### 方案 A:Render(2026-11-09 已解决——后端其实一直活着)

**关键教训:Render 给服务 URL 加随机后缀**。仓库蓝图(`render.yaml`)创建的服务实际地址是:

> **https://ai-resume-backend-1ouv.onrender.com** ← 当前在线(`/health` 与 `/docs` 均验证通过,CORS 已放行 Vercel 前端)

裸域名 `ai-resume-backend.onrender.com` 一直是 404——那不是本服务的地址,排查时曾被误判为「服务被停」。以 Dashboard 服务页「Connect」按钮显示的 URL 为准。

当前 Render 工作区有两个后端服务(同仓库同分支):

| 服务 | 运行时 | 区域 | 地址 | 状态 |
| --- | --- | --- | --- | --- |
| `ai-resume-backend` | Python 3(Blueprint 管理) | oregon | `ai-resume-backend-1ouv.onrender.com` | **主用**——env 齐全(CORS/AI Key 建仓时已填),随仓库自动同步 |
| `ai-resume` | Docker(2026-11-09 新建) | singapore | `ai-resume-iv50.onrender.com` | 备用——根目录 Dockerfile,自带 weasyprint PDF;AI Key 未配 |

**最终安排(2026-11-09 定):双服务并存,主备分工**——

- **主用 = 蓝图服务(1ouv)**:env 齐全(AI Key 已配),随仓库推送自动同步,对外文档/简历一律引用它
- **备用 = Docker 服务(iv50)**:新加坡区域(离用户更近,延迟低)+ 自带 weasyprint(PDF 导出能力更全),自动跟随分支部署,已配 CORS;**要在备用机启用 AI 功能,需在它 Environment 里补 `AI_API_KEY` / `AI_BASE_URL` / `AI_MODEL`(值与主用一致)**,切换时只需把引用域名换掉

免费层各自 15 分钟无流量休眠(冷启动 ~30s),演示前先访问一次唤醒。

### 方案 B:Hugging Face Spaces(免费、带 Docker、原生支持 weasyprint)

仓库根 `Dockerfile` 现在也满足 HF「Dockerfile 必须在仓库根」的约定。HF Space → New →
**Docker** → 指向本仓库即可。**注意 HF 不注入 PORT**:要么在 Space Settings → Variables
里设 `PORT=7860`,要么在 Space README 头部加 `app_port: 8000`。免费层 48h 无流量休眠,
重建 ~3 分钟,适合当「常驻备份」。

## 上线后必做:补 CORS 白名单

后端环境变量 `CORS_ORIGINS` 追加两个新域名(值外不加引号、源末尾不带 `/`):

```
CORS_ORIGINS=https://ai-resume-workbench.vercel.app,https://wjh941.github.io,https://ai-resume-landing.pages.dev,https://ai-resume-web.pages.dev
```

漏一个,对应前端的浏览器请求会被 CORS 全线拦截(README 里记录过这个 P0 事故)。
