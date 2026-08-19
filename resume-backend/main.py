from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager, suppress
import logging
import sqlite3
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import account, ai, applications, assessment, auth, career, consultation, drafts, evidence, exports, job_collections, knowledgebase, membership, system, templates
from app.repositories.account_privacy import AccountPrivacyRepository
from app.repositories.applications import ApplicationNotFoundError, ApplicationRepository
from app.config import Settings, load_settings
from app.db import initialize_database
from app.repositories.assessment import AssessmentNotFoundError, AssessmentRepository
from app.repositories.career_catalog import CareerCatalogRepository
from app.repositories.career_profiles import CareerProfileNotFoundError, CareerProfileRepository
from app.repositories.career_tasks import CareerTaskNotFoundError, CareerTaskRepository
from app.repositories.drafts import DraftNotFoundError, DraftRepository
from app.repositories.evidence import EvidenceRepository
from app.repositories.knowledgebase import KnowledgebaseRepository, KnowledgebaseRoleNotFoundError
from app.repositories.job_collections import FavoriteJobNotFoundError, JobCollectionRepository
from app.repositories.membership import MembershipRepository, OrderExpiredError, OrderNotFoundError, PaymentCallbackConflictError
from app.repositories.templates import TemplateRepository
from app.repositories.users import UserRepository
from app.schemas.common import error, success
from app.services.ai_client import AIServiceError, build_ai_client
from app.services.career_recommender import CareerRecommender
from app.services.downloads import DownloadNotFoundError, DownloadService
from app.services.job_catalog import JobCatalog
from app.services.official_dataset_sync import OfficialDatasetSyncService
from app.services.export_pdf import PdfRendererUnavailableError
from app.api.exports import ExportEmptyError, ExportGenerationError
from app.services.job_cache import JobCache
from app.services.job_matching import JobMatcher
from app.services.rewrite_guard import RewriteFactViolation
from app.services.template_service import TemplateService
from app.services.auth import AuthService
from app.services.sms import SmsService
from app.services.auth import current_user_id
from app.services.membership import MembershipPackageConflictError, MembershipService, PaymentChannelUnavailableError, PaymentDemoDisabledError, PaymentSignatureInvalidError, VipPermissionError, get_current_vip
from app.services.rate_limit import InMemoryRateLimiter
from app.services.web_search import build_web_search_client
from pydantic import ValidationError


logger = logging.getLogger("resume_api")


def _add_security_headers(response: JSONResponse, production: bool) -> None:
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    if production:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.download_service.cleanup_expired()
    cleanup_task = asyncio.create_task(_cleanup_downloads_periodically(app.state.download_service))
    try:
        yield
    finally:
        cleanup_task.cancel()
        with suppress(asyncio.CancelledError):
            await cleanup_task


async def _cleanup_downloads_periodically(download_service: DownloadService) -> None:
    while True:
        await asyncio.sleep(15 * 60)
        download_service.cleanup_expired()


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or load_settings()
    database_target = settings.database_target
    initialize_database(
        database_target,
        timeout_seconds=settings.sqlite_timeout_seconds,
    )

    app = FastAPI(
        title="Resume Demo API",
        debug=False,
        docs_url=None if settings.production else "/docs",
        redoc_url=None if settings.production else "/redoc",
        openapi_url=None if settings.production else "/openapi.json",
        lifespan=lifespan,
    )
    if settings.cors_origins:
        # 一期前端/小程序跨域白名单；生产必须填写确切 HTTPS 域名，禁止使用通配符。
        app.add_middleware(
            CORSMiddleware,
            allow_origins=list(settings.cors_origins),
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
            allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
            expose_headers=["X-Request-ID"],
        )
    app.state.settings = settings
    app.state.auth_rate_limiter = InMemoryRateLimiter(
        settings.auth_rate_limit_max_requests,
        settings.auth_rate_limit_window_seconds,
    )

    @app.middleware("http")
    async def add_request_id_and_limit_auth(request: Request, call_next):
        request_id = uuid4().hex
        origin = request.headers.get("origin")
        if settings.production and origin and origin not in settings.cors_origins:
            response = JSONResponse(
                status_code=403,
                content=error("origin_forbidden", "Origin is not allowed."),
            )
            response.headers["X-Request-ID"] = request_id
            _add_security_headers(response, settings.production)
            return response
        if request.method == "POST" and request.url.path.startswith("/api/auth/"):
            client_host = request.client.host if request.client else "unknown"
            key = f"{request.method}:{request.url.path}:{client_host}"
            decision = app.state.auth_rate_limiter.check(key)
            if not decision.allowed:
                response = JSONResponse(
                    status_code=429,
                    content=error("rate_limited", "Too many authentication attempts. Please try again later."),
                    headers={"Retry-After": str(decision.retry_after_seconds)},
                )
                response.headers["X-Request-ID"] = request_id
                _add_security_headers(response, settings.production)
                return response

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        _add_security_headers(response, settings.production)
        return response
    app.state.user_repository = UserRepository(database_target)
    app.state.account_privacy_repository = AccountPrivacyRepository(database_target)
    app.state.auth_service = AuthService(settings, app.state.user_repository)
    app.state.sms_service = SmsService(settings)
    app.state.membership_repository = MembershipRepository(database_target)
    app.state.membership_service = MembershipService(app.state.membership_repository, settings)
    app.state.draft_repository = DraftRepository(database_target)
    app.state.application_repository = ApplicationRepository(database_target)
    app.state.job_collection_repository = JobCollectionRepository(database_target)
    app.state.evidence_repository = EvidenceRepository(database_target)
    app.state.assessment_repository = AssessmentRepository(database_target)
    app.state.template_service = TemplateService(TemplateRepository(database_target))
    app.state.ai_client = build_ai_client(settings)
    app.state.job_cache = JobCache(database_target, settings.cache_expire_day)
    app.state.job_catalog = JobCatalog(database_target)
    app.state.job_matcher = JobMatcher()
    app.state.knowledgebase_repository = KnowledgebaseRepository(database_target)
    app.state.official_dataset_sync_service = OfficialDatasetSyncService(
        app.state.knowledgebase_repository
    )
    app.state.career_catalog_repository = CareerCatalogRepository(database_target)
    app.state.career_profile_repository = CareerProfileRepository(database_target)
    app.state.career_task_repository = CareerTaskRepository(database_target)
    app.state.career_recommender = CareerRecommender(
        app.state.career_catalog_repository
    )
    app.state.web_search_client = build_web_search_client(settings)
    app.state.download_service = DownloadService(
        database_target,
        settings.temp_file_path,
        settings.export_file_expire_minutes,
    )

    @app.exception_handler(DraftNotFoundError)
    def draft_not_found(_: Request, __: DraftNotFoundError):
        return JSONResponse(status_code=404, content=error("not_found", "Draft not found"))

    @app.exception_handler(ApplicationNotFoundError)
    def application_not_found(_: Request, __: ApplicationNotFoundError):
        return JSONResponse(
            status_code=404,
            content=error("not_found", "Application not found"),
        )

    @app.exception_handler(FavoriteJobNotFoundError)
    def favorite_job_not_found(_: Request, __: FavoriteJobNotFoundError):
        return JSONResponse(status_code=404, content=error("not_found", "Favorite job not found"))

    @app.exception_handler(KnowledgebaseRoleNotFoundError)
    def knowledgebase_role_not_found(_: Request, __: KnowledgebaseRoleNotFoundError):
        return JSONResponse(
            status_code=404, content=error('not_found', 'Knowledgebase role not found')
        )

    @app.exception_handler(CareerProfileNotFoundError)
    def career_profile_not_found(_: Request, __: CareerProfileNotFoundError):
        return JSONResponse(
            status_code=404,
            content=error("not_found", "Career profile not found"),
        )

    @app.exception_handler(CareerTaskNotFoundError)
    def career_task_not_found(_: Request, __: CareerTaskNotFoundError):
        return JSONResponse(status_code=404, content=error("not_found", "Career task not found"))

    @app.exception_handler(AssessmentNotFoundError)
    def assessment_not_found(_: Request, __: AssessmentNotFoundError):
        return JSONResponse(
            status_code=404,
            content=error("not_found", "Career assessment not found"),
        )

    @app.exception_handler(RequestValidationError)
    def request_validation_error(request: Request, _: RequestValidationError):
        logger.info("validation error: %s %s", request.method, request.url.path)
        return JSONResponse(status_code=422, content=error("validation_error", "Request validation failed"))

    @app.exception_handler(ValidationError)
    def model_validation_error(request: Request, _: ValidationError):
        logger.info("validation error: %s %s", request.method, request.url.path)
        return JSONResponse(status_code=422, content=error("validation_error", "Request validation failed"))

    @app.exception_handler(sqlite3.Error)
    def database_error(request: Request, exception: sqlite3.Error):
        logger.error("database error: %s %s (%s)", request.method, request.url.path, type(exception).__name__)
        return JSONResponse(status_code=503, content=error("database_error", "Database operation failed"))

    @app.exception_handler(ExportEmptyError)
    def export_empty(request: Request, _: ExportEmptyError):
        logger.info("export error: %s %s (empty resume)", request.method, request.url.path)
        return JSONResponse(status_code=422, content=error("export_empty", "Resume has no visible export content"))

    @app.exception_handler(ExportGenerationError)
    def export_generation_error(request: Request, exception: ExportGenerationError):
        logger.error("export error: %s %s (%s)", request.method, request.url.path, type(exception).__name__)
        return JSONResponse(status_code=503, content=error("export_error", "Export could not be generated"))

    @app.exception_handler(HTTPException)
    def http_error(request: Request, exception: HTTPException):
        logger.info("request error: %s %s (%s)", request.method, request.url.path, exception.status_code)
        code = {401: "unauthorized", 403: "forbidden", 404: "not_found", 422: "validation_error"}.get(
            exception.status_code, "request_error"
        )
        message = exception.detail if isinstance(exception.detail, str) else "Request failed"
        return JSONResponse(status_code=exception.status_code, content=error(code, message))

    @app.exception_handler(Exception)
    def unexpected_error(request: Request, exception: Exception):
        logger.error("unexpected error: %s %s (%s)", request.method, request.url.path, type(exception).__name__)
        return JSONResponse(status_code=500, content=error("internal_error", "Internal server error"))

    @app.exception_handler(RewriteFactViolation)
    def rewrite_fact_violation(_: Request, __: RewriteFactViolation):
        return JSONResponse(
            status_code=422,
            content=error("rewrite_fact_violation", "AI rewrite changed immutable resume facts"),
        )

    @app.exception_handler(DownloadNotFoundError)
    def download_not_found(_: Request, __: DownloadNotFoundError):
        return JSONResponse(status_code=404, content=error("not_found", "Download not found"))

    @app.exception_handler(OrderNotFoundError)
    def order_not_found(_: Request, __: OrderNotFoundError):
        return JSONResponse(status_code=404, content=error("not_found", "Order not found"))

    @app.exception_handler(OrderExpiredError)
    def order_expired(_: Request, __: OrderExpiredError):
        return JSONResponse(status_code=409, content=error("order_expired", "This unpaid order has expired."))

    @app.exception_handler(PaymentCallbackConflictError)
    def payment_callback_conflict(_: Request, __: PaymentCallbackConflictError):
        return JSONResponse(status_code=409, content=error("payment_callback_conflict", "Payment callback conflicts with the recorded transaction."))

    @app.exception_handler(PaymentSignatureInvalidError)
    def payment_signature_invalid(_: Request, __: PaymentSignatureInvalidError):
        return JSONResponse(status_code=403, content=error("payment_signature_invalid", "Payment callback signature is invalid."))

    @app.exception_handler(VipPermissionError)
    def vip_permission_denied(_: Request, exception: VipPermissionError):
        return JSONResponse(status_code=403, content=error("vip_required", exception.message))

    @app.exception_handler(PaymentDemoDisabledError)
    def payment_demo_disabled(_: Request, __: PaymentDemoDisabledError):
        return JSONResponse(
            status_code=503,
            content=error("payment_demo_disabled", "演示支付已关闭，请配置真实支付渠道"),
        )

    @app.exception_handler(MembershipPackageConflictError)
    def membership_package_conflict(_: Request, __: MembershipPackageConflictError):
        return JSONResponse(
            status_code=409,
            content=error("membership_package_conflict", "当前高级会员有效，请在到期后购买基础套餐"),
        )

    @app.exception_handler(PaymentChannelUnavailableError)
    def payment_channel_unavailable(_: Request, __: PaymentChannelUnavailableError):
        return JSONResponse(
            status_code=503,
            content=error("payment_channel_unavailable", "支付渠道尚未配置，请使用演示支付或联系管理员"),
        )

    @app.exception_handler(PdfRendererUnavailableError)
    def pdf_renderer_unavailable(_: Request, __: PdfRendererUnavailableError):
        return JSONResponse(
            status_code=503,
            content=error("pdf_renderer_unavailable", "PDF renderer is unavailable"),
        )

    @app.exception_handler(AIServiceError)
    def ai_service_error(_: Request, exception: AIServiceError):
        return JSONResponse(
            status_code=exception.status_code,
            content=error(exception.code, exception.message),
        )

    @app.get("/health")
    def health():
        summary = system.health_summary(settings)
        return success({
            "status": summary["status"],
            "capabilities": ["job_plan", "job_match", "ai_setup"],
            "database_type": summary["database"]["type"],
            "backup": summary["backup"],
            "critical_config": summary["critical_config"],
        })

    @app.get("/health/detail")
    def health_detail():
        return success(system.health_detail(settings))

    # 业务 Router 在组装处统一注入 JWT 依赖，新增端点不会遗漏鉴权边界。
    business_routers = (
        account.router,
        ai.router,
        applications.router,
        assessment.router,
        career.router,
        consultation.router,
        drafts.router,
        evidence.router,
        exports.router,
        job_collections.router,
        knowledgebase.router,
        membership.router,
        system.router,
        templates.router,
    )
    for router in business_routers:
        app.include_router(router, dependencies=[Depends(current_user_id), Depends(get_current_vip)])
    app.include_router(auth.router)
    return app


app = create_app()
