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
    database_url: str = ""
    web_search_provider: str = "disabled"
    tavily_api_key: str = ""
    web_search_base_url: str = "https://api.tavily.com"
    web_search_max_results: int = 5
    # 本期 SQLite 过渡鉴权配置；二期切换云数据库时 JWT 载荷规则保持不变。
    jwt_secret: str = "development-only-change-me"
    jwt_expire_hours: int = 24
    auth_demo_mode: bool = True
    sms_provider: str = "disabled"
    sms_access_key: str = ""
    sms_access_secret: str = ""
    sms_sign_name: str = ""
    sms_template_id: str = ""
    sms_aliyun_access_key_id: str = ""
    sms_aliyun_access_key_secret: str = ""
    sms_tencent_secret_id: str = ""
    sms_tencent_secret_key: str = ""
    sms_http_endpoint: str = ""
    sms_http_token: str = ""
    sms_code_ttl_seconds: int = 300
    sms_code_cooldown_seconds: int = 60
    wechat_open_app_id: str = ""
    wechat_open_app_secret: str = ""
    wechat_open_redirect_uri: str = ""
    # 二期商业化底座。真实支付接入前只能在演示环境开启模拟回调。
    membership_enabled: bool = True
    payment_demo_mode: bool = True
    wechat_pay_mch_id: str = ""
    wechat_pay_api_v3_key: str = ""
    wechat_pay_app_id: str = ""
    alipay_app_id: str = ""
    alipay_private_key: str = ""
    payment_callback_secret: str = ""
    order_payment_expire_minutes: int = 30
    cors_origins: tuple[str, ...] = ()
    ai_config_ui_enabled: bool = True
    sqlite_timeout_seconds: float = 3.0
    auth_rate_limit_max_requests: int = 10
    auth_rate_limit_window_seconds: int = 60
    worker_enabled: bool = False
    worker_scan_interval_seconds: int = 300
    worker_lock_ttl_seconds: int = 600
    operator_phone_allowlist: tuple[str, ...] = ()
    push_dispatcher_mode: str = "mock"
    log_level: str = "INFO"
    resume_import_max_file_bytes: int = 10 * 1024 * 1024
    password_bcrypt_rounds: int = 12

    @property
    def database_target(self) -> Path | str:
        return self.database_url or self.database_path

    @property
    def database_kind(self) -> str:
        return "postgresql" if self.database_url.startswith(("postgresql://", "postgresql+psycopg://")) else "sqlite"

    @property
    def production(self) -> bool:
        return _read_bool("PRODUCTION", self.app_env.strip().lower() == "production")


def _read_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _read_csv(name: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in os.getenv(name, "").split(",") if item.strip())


def _read_phone_allowlist(name: str) -> tuple[str, ...]:
    return tuple("".join(item.split()) for item in _read_csv(name))


def load_settings() -> Settings:
    backend_root = Path(__file__).resolve().parents[1]
    _load_dotenv(backend_root / ".env")
    app_env = os.getenv("APP_ENV", "development")
    return Settings(
        app_env=app_env,
        app_host=os.getenv("APP_HOST", "127.0.0.1"),
        app_port=int(os.getenv("APP_PORT", "8000")),
        database_path=Path(os.getenv("DATABASE_PATH", "./data/resume_demo.db")).resolve(),
        database_url=os.getenv("DATABASE_URL", "").strip(),
        ai_provider=os.getenv("AI_PROVIDER", "openai_compatible"),
        ai_api_key=os.getenv("AI_API_KEY", ""),
        ai_base_url=os.getenv("AI_BASE_URL", "https://ark.cn-beijing.volces.com/api/v1"),
        ai_model=os.getenv("AI_MODEL", ""),
        # Development-only convenience. Production must keep the model key in server env.
        ai_config_ui_enabled=_read_bool("AI_CONFIG_UI_ENABLED", app_env != "production"),
        cache_expire_day=int(os.getenv("CACHE_EXPIRE_DAY", "7")),
        temp_file_path=Path(os.getenv("TEMP_FILE_PATH", "./temp")).resolve(),
        export_file_expire_minutes=int(os.getenv("EXPORT_FILE_EXPIRE_MINUTES", "60")),
        sqlite_timeout_seconds=float(os.getenv("SQLITE_TIMEOUT_SECONDS", "3")),
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
        sms_access_key=os.getenv("SMS_ACCESS_KEY", os.getenv("SMS_ALIYUN_ACCESS_KEY_ID", "")),
        sms_access_secret=os.getenv("SMS_ACCESS_SECRET", os.getenv("SMS_ALIYUN_ACCESS_KEY_SECRET", "")),
        sms_sign_name=os.getenv("SMS_SIGN_NAME", ""),
        sms_template_id=os.getenv("SMS_TEMPLATE_ID", ""),
        sms_aliyun_access_key_id=os.getenv("SMS_ALIYUN_ACCESS_KEY_ID", ""),
        sms_aliyun_access_key_secret=os.getenv("SMS_ALIYUN_ACCESS_KEY_SECRET", ""),
        sms_tencent_secret_id=os.getenv("SMS_TENCENT_SECRET_ID", ""),
        sms_tencent_secret_key=os.getenv("SMS_TENCENT_SECRET_KEY", ""),
        sms_http_endpoint=os.getenv("SMS_HTTP_ENDPOINT", ""),
        sms_http_token=os.getenv("SMS_HTTP_TOKEN", ""),
        sms_code_ttl_seconds=int(os.getenv("SMS_CODE_TTL_SECONDS", "300")),
        sms_code_cooldown_seconds=int(os.getenv("SMS_CODE_COOLDOWN_SECONDS", "60")),
        wechat_open_app_id=os.getenv("WECHAT_OPEN_APP_ID", ""),
        wechat_open_app_secret=os.getenv("WECHAT_OPEN_APP_SECRET", ""),
        wechat_open_redirect_uri=os.getenv("WECHAT_OPEN_REDIRECT_URI", ""),
        membership_enabled=_read_bool("MEMBERSHIP_ENABLED", True),
        payment_demo_mode=_read_bool("PAYMENT_DEMO_MODE", app_env != "production"),
        wechat_pay_mch_id=os.getenv("WECHAT_PAY_MCH_ID", ""),
        wechat_pay_api_v3_key=os.getenv("WECHAT_PAY_API_V3_KEY", ""),
        wechat_pay_app_id=os.getenv("WECHAT_PAY_APP_ID", ""),
        alipay_app_id=os.getenv("ALIPAY_APP_ID", ""),
        alipay_private_key=os.getenv("ALIPAY_PRIVATE_KEY", ""),
        payment_callback_secret=os.getenv("PAYMENT_CALLBACK_SECRET", ""),
        order_payment_expire_minutes=int(os.getenv("ORDER_PAYMENT_EXPIRE_MINUTES", "30")),
        cors_origins=_read_csv("CORS_ORIGINS"),
        auth_rate_limit_max_requests=int(os.getenv("AUTH_RATE_LIMIT_MAX_REQUESTS", "10")),
        auth_rate_limit_window_seconds=int(os.getenv("AUTH_RATE_LIMIT_WINDOW_SECONDS", "60")),
        worker_enabled=_read_bool("WORKER_ENABLED", False),
        worker_scan_interval_seconds=max(15, int(os.getenv("TASK_SCAN_INTERVAL_SECONDS", "300"))),
        worker_lock_ttl_seconds=max(30, int(os.getenv("WORKER_LOCK_TTL_SECONDS", "600"))),
        operator_phone_allowlist=_read_phone_allowlist("OPERATOR_PHONE_ALLOWLIST"),
        push_dispatcher_mode=(
            os.getenv("PUSH_DISPATCHER_MODE", "mock").strip().lower()
            if os.getenv("PUSH_DISPATCHER_MODE", "mock").strip().lower() in {"mock", "real"}
            else "mock"
        ),
        log_level=os.getenv("LOG_LEVEL", "INFO").strip().upper(),
        resume_import_max_file_bytes=max(1, int(os.getenv("RESUME_IMPORT_MAX_FILE_BYTES", str(10 * 1024 * 1024)))),
        password_bcrypt_rounds=min(31, max(4, int(os.getenv("PASSWORD_BCRYPT_ROUNDS", "12")))),
    )
