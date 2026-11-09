# 仓库根 Dockerfile:供「约定 Dockerfile 必须在根目录」的平台使用(Render Docker 运行时、
# HF Spaces 等)——克隆即建,零配置。构建上下文 = 仓库根;能力完全等同
# resume-backend/Dockerfile(那份的上下文是 resume-backend,供 docker build 手动指定路径时用)。
FROM python:3.11-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

# weasyprint PDF 渲染需要系统级 Pango/Cairo;PostgreSQL 驱动/迁移/定时任务按服务器形态一并装齐
RUN apt-get update && apt-get install -y --no-install-recommends \
      libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf-2.0-0 shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

COPY resume-backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
      weasyprint "psycopg[binary]>=3.1,<4" "SQLAlchemy>=2.0,<3" "alembic>=1.13,<2" "APScheduler>=3.10,<4"
ENV PDF_RENDERER=weasyprint

COPY resume-backend/app ./app
COPY resume-backend/migrations ./migrations
COPY resume-backend/alembic.ini resume-backend/main.py ./

# PaaS 会注入 PORT(Render 默认 10000);未被注入时回落 8000。
# HF Spaces 注意:它不注入 PORT,需在 Space 变量里设 PORT=7860,或在 Space README 加 app_port: 8000。
ENV PORT=8000
EXPOSE 8000
CMD ["sh", "-c", "mkdir -p data && alembic upgrade head && exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
