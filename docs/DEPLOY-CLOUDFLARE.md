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

### 方案 A:Render 重新部署(推荐,2 分钟)

原来的 `ai-resume-backend.onrender.com` 服务已 404(Render 侧被停/删)。登录 Render →
**New → Web Service → 连接本仓库**:

- Root Directory: `resume-backend`
- Build: `pip install -r requirements.txt`
- Start: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- 免费层 15 分钟无流量会休眠(冷启动 ~30s),演示前先自己访问一次唤醒

### 方案 B:Hugging Face Spaces(免费、带 Docker、支持 weasyprint)

仓库已带 `resume-backend/Dockerfile`。HF Space → New → **Docker** 类型 →
把 `resume-backend/` 作为 Space 仓库推送即可,得到 `https://<你>-<space>.hf.space`。
免费层 48h 无流量休眠,重建较慢(~3 分钟),适合当「常驻备份」。

## 上线后必做:补 CORS 白名单

后端环境变量 `CORS_ORIGINS` 追加两个新域名(值外不加引号、源末尾不带 `/`):

```
CORS_ORIGINS=https://ai-resume-workbench.vercel.app,https://wjh941.github.io,https://ai-resume-landing.pages.dev,https://ai-resume-web.pages.dev
```

漏一个,对应前端的浏览器请求会被 CORS 全线拦截(README 里记录过这个 P0 事故)。
