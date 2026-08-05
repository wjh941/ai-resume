from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os


def _load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


@dataclass(frozen=True)
class Settings:
    app_env: str
    app_host: str
    app_port: int
    database_path: Path
    ai_provider: str
    ai_api_key: str
    ai_base_url: str
    ai_model: str
    cache_expire_day: int
    temp_file_path: Path
    export_file_expire_minutes: int
    pdf_renderer: str
    playwright_browsers_path: str


def load_settings() -> Settings:
    backend_root = Path(__file__).resolve().parents[1]
    _load_dotenv(backend_root / ".env")
    return Settings(
        app_env=os.getenv("APP_ENV", "development"),
        app_host=os.getenv("APP_HOST", "127.0.0.1"),
        app_port=int(os.getenv("APP_PORT", "8000")),
        database_path=Path(os.getenv("DATABASE_PATH", "./data/resume_demo.db")).resolve(),
        ai_provider=os.getenv("AI_PROVIDER", "mock"),
        ai_api_key=os.getenv("AI_API_KEY", ""),
        ai_base_url=os.getenv("AI_BASE_URL", "https://ark.cn-beijing.volces.com/api/v1"),
        ai_model=os.getenv("AI_MODEL", ""),
        cache_expire_day=int(os.getenv("CACHE_EXPIRE_DAY", "7")),
        temp_file_path=Path(os.getenv("TEMP_FILE_PATH", "./temp")).resolve(),
        export_file_expire_minutes=int(os.getenv("EXPORT_FILE_EXPIRE_MINUTES", "60")),
        pdf_renderer=os.getenv("PDF_RENDERER", "playwright"),
        playwright_browsers_path=os.getenv(
            "PLAYWRIGHT_BROWSERS_PATH", "D:/Projects/ai-resume-miniprogram/.cache/playwright"
        ),
    )
