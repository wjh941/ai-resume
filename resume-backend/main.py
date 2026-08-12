from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api import ai, applications, assessment, career, consultation, drafts, evidence, exports, knowledgebase, templates
from app.repositories.applications import ApplicationNotFoundError, ApplicationRepository
from app.config import Settings, load_settings
from app.db import initialize_database
from app.repositories.assessment import AssessmentNotFoundError, AssessmentRepository
from app.repositories.career_catalog import CareerCatalogRepository
from app.repositories.career_profiles import CareerProfileNotFoundError, CareerProfileRepository
from app.repositories.drafts import DraftNotFoundError, DraftRepository
from app.repositories.evidence import EvidenceRepository
from app.repositories.knowledgebase import KnowledgebaseRepository, KnowledgebaseRoleNotFoundError
from app.repositories.templates import TemplateRepository
from app.schemas.common import error, success
from app.services.ai_client import build_ai_client
from app.services.career_recommender import CareerRecommender
from app.services.downloads import DownloadNotFoundError, DownloadService
from app.services.job_catalog import JobCatalog
from app.services.official_dataset_sync import OfficialDatasetSyncService
from app.services.export_pdf import PdfRendererUnavailableError
from app.services.job_cache import JobCache
from app.services.rewrite_guard import RewriteFactViolation
from app.services.template_service import TemplateService
from app.services.web_search import build_web_search_client


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
    initialize_database(settings.database_path)

    app = FastAPI(title="Resume Demo API", lifespan=lifespan)
    app.state.settings = settings
    app.state.draft_repository = DraftRepository(settings.database_path)
    app.state.application_repository = ApplicationRepository(settings.database_path)
    app.state.evidence_repository = EvidenceRepository(settings.database_path)
    app.state.assessment_repository = AssessmentRepository(settings.database_path)
    app.state.template_service = TemplateService(TemplateRepository(settings.database_path))
    app.state.ai_client = build_ai_client(settings)
    app.state.job_cache = JobCache(settings.database_path, settings.cache_expire_day)
    app.state.job_catalog = JobCatalog(settings.database_path)
    app.state.knowledgebase_repository = KnowledgebaseRepository(settings.database_path)
    app.state.official_dataset_sync_service = OfficialDatasetSyncService(
        app.state.knowledgebase_repository
    )
    app.state.career_catalog_repository = CareerCatalogRepository(settings.database_path)
    app.state.career_profile_repository = CareerProfileRepository(settings.database_path)
    app.state.career_recommender = CareerRecommender(
        app.state.career_catalog_repository
    )
    app.state.web_search_client = build_web_search_client(settings)
    app.state.download_service = DownloadService(
        settings.database_path,
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

    @app.exception_handler(AssessmentNotFoundError)
    def assessment_not_found(_: Request, __: AssessmentNotFoundError):
        return JSONResponse(
            status_code=404,
            content=error("not_found", "Career assessment not found"),
        )

    @app.exception_handler(RequestValidationError)
    def request_validation_error(_: Request, __: RequestValidationError):
        return JSONResponse(status_code=422, content=error("validation_error", "Request validation failed"))

    @app.exception_handler(RewriteFactViolation)
    def rewrite_fact_violation(_: Request, __: RewriteFactViolation):
        return JSONResponse(
            status_code=422,
            content=error("rewrite_fact_violation", "AI rewrite changed immutable resume facts"),
        )

    @app.exception_handler(DownloadNotFoundError)
    def download_not_found(_: Request, __: DownloadNotFoundError):
        return JSONResponse(status_code=404, content=error("not_found", "Download not found"))

    @app.exception_handler(PdfRendererUnavailableError)
    def pdf_renderer_unavailable(_: Request, __: PdfRendererUnavailableError):
        return JSONResponse(
            status_code=503,
            content=error("pdf_renderer_unavailable", "PDF renderer is unavailable"),
        )

    @app.get("/health")
    def health():
        return success({"status": "healthy"})

    app.include_router(ai.router)
    app.include_router(applications.router)
    app.include_router(assessment.router)
    app.include_router(career.router)
    app.include_router(consultation.router)
    app.include_router(drafts.router)
    app.include_router(evidence.router)
    app.include_router(exports.router)
    app.include_router(knowledgebase.router)
    app.include_router(templates.router)
    return app


app = create_app()
