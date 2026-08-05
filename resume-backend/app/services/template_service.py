from __future__ import annotations

from app.repositories.templates import TemplateRepository


class TemplateService:
    def __init__(self, repository: TemplateRepository):
        self.repository = repository

    def list_templates(self) -> list[dict]:
        return self.repository.list_active()
