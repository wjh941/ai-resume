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
    web_search_provider: str = "disabled"
    tavily_api_key: str = ""
    web_search_base_url: str = "https://api.tavily.com"
    web_search_max_results: int = 5
    # 本期 SQLite 过渡鉴权配置；二期切换云数据库时 JWT 载荷规则保持不变。
    jwt_secret: str = "development-only-change-me"
    jwt_expire_hours: int = 24
    auth_demo_mode: bool = True
    sms_provider: str = "disabled"
    sms_aliyun_access_key_id: str = ""
    sms_aliyun_access_key_secret: str = ""
    sms_tencent_secret_id: str = ""
    sms_tencent_secret_key: str = ""
    sms_http_endpoint: str = ""
    sms_http_token: str = ""
    wechat_open_app_id: str = ""
    wechat_open_app_secret: str = ""
    wechat_open_redirect_uri: str = ""
    cors_origins: tuple[str, ...] = ()


def _read_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _read_csv(name: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in os.getenv(name, "").split(",") if item.strip())


def load_settings() -> Settings:
    backend_root = Path(__file__).resolve().parents[1]
    _load_dotenv(backend_root / ".env")
    app_env = os.getenv("APP_ENV", "development")
    return Settings(
        app_env=app_env,
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
        web_search_provider=os.getenv("WEB_SEARCH_PROVIDER", "disabled"),
        tavily_api_key=os.getenv("TAVILY_API_KEY", ""),
        web_search_base_url=os.getenv("WEB_SEARCH_BASE_URL", "https://api.tavily.com"),
        web_search_max_results=int(os.getenv("WEB_SEARCH_MAX_RESULTS", "5")),
        jwt_secret=os.getenv("JWT_SECRET", "development-only-change-me"),
        jwt_expire_hours=int(os.getenv("JWT_EXPIRE_HOURS", "24")),
        auth_demo_mode=_read_bool("AUTH_DEMO_MODE", app_env != "production"),
        sms_provider=os.getenv("SMS_PROVIDER", "disabled").strip().lower(),
        sms_aliyun_access_key_id=os.getenv("SMS_ALIYUN_ACCESS_KEY_ID", ""),
        sms_aliyun_access_key_secret=os.getenv("SMS_ALIYUN_ACCESS_KEY_SECRET", ""),
        sms_tencent_secret_id=os.getenv("SMS_TENCENT_SECRET_ID", ""),
        sms_tencent_secret_key=os.getenv("SMS_TENCENT_SECRET_KEY", ""),
        sms_http_endpoint=os.getenv("SMS_HTTP_ENDPOINT", ""),
        sms_http_token=os.getenv("SMS_HTTP_TOKEN", ""),
        wechat_open_app_id=os.getenv("WECHAT_OPEN_APP_ID", ""),
        wechat_open_app_secret=os.getenv("WECHAT_OPEN_APP_SECRET", ""),
        wechat_open_redirect_uri=os.getenv("WECHAT_OPEN_REDIRECT_URI", ""),
        cors_origins=_read_csv("CORS_ORIGINS"),
    )
