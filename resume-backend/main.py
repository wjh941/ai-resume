from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api import drafts, templates
from app.config import Settings, load_settings
from app.db import initialize_database
from app.repositories.drafts import DraftNotFoundError, DraftRepository
from app.repositories.templates import TemplateRepository
from app.schemas.common import error, success
from app.services.template_service import TemplateService


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or load_settings()
    initialize_database(settings.database_path)

    app = FastAPI(title="Resume Demo API")
    app.state.settings = settings
    app.state.draft_repository = DraftRepository(settings.database_path)
    app.state.template_service = TemplateService(TemplateRepository(settings.database_path))

    @app.exception_handler(DraftNotFoundError)
    def draft_not_found(_: Request, __: DraftNotFoundError):
        return JSONResponse(status_code=404, content=error("not_found", "Draft not found"))

    @app.exception_handler(RequestValidationError)
    def request_validation_error(_: Request, __: RequestValidationError):
        return JSONResponse(status_code=422, content=error("validation_error", "Request validation failed"))

    @app.get("/health")
    def health():
        return success({"status": "healthy"})

    app.include_router(drafts.router)
    app.include_router(templates.router)
    return app


app = create_app()
