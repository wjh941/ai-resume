from __future__ import annotations

from copy import deepcopy
import json
from typing import Protocol

import httpx

from app.config import Settings
from app.schemas.job import JobIntelligence
from app.schemas.resume import ResumePayload
from app.services.job_cache import normalize_role_name


class AIClient(Protocol):
    async def query_job(self, role_name: str) -> JobIntelligence: ...

    async def rewrite_resume(
        self,
        resume: ResumePayload,
        job: JobIntelligence,
        mode: str,
    ) -> ResumePayload: ...


class MockAIClient:
    def __init__(self) -> None:
        self.job_query_count = 0
        self.rewrite_result: ResumePayload | dict | None = None

    async def query_job(self, role_name: str) -> JobIntelligence:
        self.job_query_count += 1
        display_role = " ".join(part.capitalize() for part in normalize_role_name(role_name).split())
        return JobIntelligence(
            role_name=display_role,
            salary_by_experience={
                "graduate": "10k-16k",
                "1-3_years": "16k-26k",
                "3-5_years": "26k-38k",
                "5_plus_years": "38k-55k",
            },
            responsibilities=[
                "Build reliable data pipelines and data models.",
                "Collaborate with analysts and product teams on data delivery.",
            ],
            hard_requirements=["Bachelor degree or equivalent practical experience."],
            required_skills=["Python", "SQL", "Data warehousing"],
            bonus_skills=["Airflow", "Spark", "Cloud platforms"],
            career_route=["Data Engineer", "Senior Data Engineer", "Data Platform Lead"],
        )

    async def rewrite_resume(
        self,
        resume: ResumePayload,
        job: JobIntelligence,
        mode: str,
    ) -> ResumePayload:
        if self.rewrite_result is not None:
            return ResumePayload.model_validate(self.rewrite_result)

        rewritten = deepcopy(resume)
        suffix = f" Optimized for {job.role_name} keywords."
        for item in rewritten.employment:
            if item.description:
                item.description = f"{item.description}{suffix}"
        for item in rewritten.projects:
            if item.description:
                item.description = f"{item.description}{suffix}"
        if rewritten.self_evaluation:
            rewritten.self_evaluation = f"{rewritten.self_evaluation}{suffix}"
        return rewritten


class OpenAICompatibleClient:
    def __init__(self, settings: Settings) -> None:
        self._base_url = settings.ai_base_url.rstrip("/")
        self._api_key = settings.ai_api_key
        self._model = settings.ai_model or "default"

    async def query_job(self, role_name: str) -> JobIntelligence:
        content = await self._chat_completion(
            system_prompt="Return only valid JSON matching the requested job intelligence schema.",
            user_prompt=(
                "Create market-estimate job intelligence for this role. "
                "Use keys role_name, salary_by_experience, responsibilities, "
                "hard_requirements, required_skills, bonus_skills, career_route. "
                f"Role: {role_name}"
            ),
        )
        return JobIntelligence.model_validate_json(content)

    async def rewrite_resume(
        self,
        resume: ResumePayload,
        job: JobIntelligence,
        mode: str,
    ) -> ResumePayload:
        content = await self._chat_completion(
            system_prompt=(
                "Return only valid JSON. Improve wording only. Never change employers, "
                "dates, schools, certificates, project identity, or stated metrics."
            ),
            user_prompt=json.dumps(
                {
                    "mode": mode,
                    "resume": resume.model_dump(),
                    "target_job": job.model_dump(),
                },
                ensure_ascii=False,
            ),
        )
        return ResumePayload.model_validate_json(content)

    async def _chat_completion(self, system_prompt: str, user_prompt: str) -> str:
        headers = {"Authorization": f"Bearer {self._api_key}"}
        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "response_format": {"type": "json_object"},
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self._base_url}/chat/completions",
                headers=headers,
                json=payload,
            )
        response.raise_for_status()
        data = response.json()
        return str(data["choices"][0]["message"]["content"])


class ArkAIClient(OpenAICompatibleClient):
    pass


def build_ai_client(settings: Settings) -> AIClient:
    if settings.ai_provider == "mock":
        return MockAIClient()
    if settings.ai_provider == "ark":
        return ArkAIClient(settings)
    if settings.ai_provider == "openai_compatible":
        return OpenAICompatibleClient(settings)
    raise ValueError(f"Unsupported AI_PROVIDER: {settings.ai_provider}")
