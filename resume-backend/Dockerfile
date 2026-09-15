FROM python:3.11-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf-2.0-0 shared-mime-info && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
# 服务器镜像自带完整能力：weasyprint PDF（配合上层 apt 的 Pango/Cairo）、
# PostgreSQL 驱动、alembic 迁移与 APScheduler worker；并默认使用 weasyprint 渲染 PDF。
RUN pip install --no-cache-dir -r requirements.txt weasyprint "psycopg[binary]>=3.1,<4" "SQLAlchemy>=2.0,<3" "alembic>=1.13,<2" "APScheduler>=3.10,<4"
ENV PDF_RENDERER=weasyprint
COPY app ./app
COPY migrations ./migrations
COPY alembic.ini main.py ./
CMD ["sh", "-c", "alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port 8000"]
