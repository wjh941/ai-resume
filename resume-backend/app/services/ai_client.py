from __future__ import annotations

import json
from typing import Literal, Protocol

import httpx

from app.config import Settings
from app.schemas.consultation import (
    AdviceTopic,
    CareerAdviceResponse,
    IdentityCode,
    JobConsultationResponse,
    ResumeReviewResponse,
)
from app.schemas.job import JobIntelligence
from app.schemas.resume import ResumePayload
from app.schemas.career import ComparisonActionPlan, JobPlanResponse
from app.services.career_assessment import score_assessment


class AIClient(Protocol):
    async def query_job(self, role_name: str) -> JobIntelligence: ...

    async def assess_career(
        self, questions: list[dict[str, object]], answers: dict[str, int]
    ) -> dict[str, object]: ...

    async def build_comparison_action_plan(
        self, role_name: str, profile: dict[str, object], evidence: list[str]
    ) -> ComparisonActionPlan: ...

    async def build_job_plan(
        self,
        role_name: str,
        profile: dict[str, object],
        evidence: list[dict[str, object]],
        resume: dict[str, object] | None,
        assessment: dict[str, object] | None,
        expand_detail: bool,
    ) -> JobPlanResponse: ...

    async def build_job_consultation(
        self,
        job: JobIntelligence,
        identity_code: IdentityCode,
        custom_requirement: str | None = None,
    ) -> JobConsultationResponse: ...

    async def review_resume_text(
        self,
        resume_text: str,
        identity_code: IdentityCode,
        role_name: str | None,
        custom_requirement: str | None = None,
    ) -> ResumeReviewResponse: ...

    async def build_career_advice(
        self,
        identity_code: IdentityCode,
        topic: AdviceTopic,
        role_name: str | None,
        question: str | None,
    ) -> CareerAdviceResponse: ...

    async def rewrite_resume(
        self,
        resume: ResumePayload,
        job: JobIntelligence,
        mode: Literal["light", "deep"],
    ) -> ResumePayload: ...


class AIServiceError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 503) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


class UnconfiguredAIClient:
    """本期真实 AI 底座未配置时的显式失败，不返回任何本地生产 Mock。"""

    @staticmethod
    def _raise() -> None:
        raise AIServiceError("ai_not_configured", "AI 服务未配置，请联系管理员完成模型部署")

    async def query_job(self, role_name: str) -> JobIntelligence:
        self._raise()

    async def assess_career(
        self, questions: list[dict[str, object]], answers: dict[str, int]
    ) -> dict[str, object]:
        self._raise()

    async def build_comparison_action_plan(
        self, role_name: str, profile: dict[str, object], evidence: list[str]
    ) -> ComparisonActionPlan:
        self._raise()

    async def build_job_plan(
        self,
        role_name: str,
        profile: dict[str, object],
        evidence: list[dict[str, object]],
        resume: dict[str, object] | None,
        assessment: dict[str, object] | None,
        expand_detail: bool,
    ) -> JobPlanResponse:
        self._raise()

    async def build_job_consultation(
        self, job: JobIntelligence, identity_code: IdentityCode, custom_requirement: str | None = None
    ) -> JobConsultationResponse:
        self._raise()

    async def review_resume_text(
        self,
        resume_text: str,
        identity_code: IdentityCode,
        role_name: str | None,
        custom_requirement: str | None = None,
    ) -> ResumeReviewResponse:
        self._raise()

    async def build_career_advice(
        self, identity_code: IdentityCode, topic: AdviceTopic, role_name: str | None, question: str | None
    ) -> CareerAdviceResponse:
        self._raise()

    async def rewrite_resume(
        self, resume: ResumePayload, job: JobIntelligence, mode: Literal["light", "deep"]
    ) -> ResumePayload:
        self._raise()


class DevelopmentAIClient(UnconfiguredAIClient):
    """Deterministic development fallback for workflows without AI credentials."""

    async def assess_career(
        self, questions: list[dict[str, object]], answers: dict[str, int]
    ) -> dict[str, object]:
        del questions
        return score_assessment(answers)


class OpenAICompatibleClient:
    """兼容 Ark 与 OpenAI Chat Completions；所有业务生成均通过这一真实云端入口。"""

    def __init__(self, settings: Settings) -> None:
        self._base_url = settings.ai_base_url.rstrip("/")
        self._api_key = settings.ai_api_key
        self._model = settings.ai_model

    async def query_job(self, role_name: str) -> JobIntelligence:
        content = await self._chat_completion(
            "Return only valid JSON matching JobIntelligence: role_name, salary_by_experience, "
            "responsibilities, hard_requirements, required_skills, bonus_skills, career_route.",
            json.dumps({"role_name": role_name}, ensure_ascii=False),
        )
        return JobIntelligence.model_validate_json(content)

    async def assess_career(
        self, questions: list[dict[str, object]], answers: dict[str, int]
    ) -> dict[str, object]:
        content = await self._chat_completion(
            "Return only JSON with top_interests, work_style_summary, strength_evidence, "
            "confidence_note, answered_count, and action_plan. action_plan must contain "
            "seven_day, thirty_day, and ninety_day arrays. Base conclusions only on supplied answers.",
            json.dumps({"questions": questions, "answers": answers}, ensure_ascii=False),
        )
        try:
            result = json.loads(content)
        except (TypeError, ValueError) as error:
            raise AIServiceError("ai_invalid_response", "AI 测评结果格式异常，请稍后重试") from error
        if not isinstance(result, dict) or not isinstance(result.get("action_plan"), dict):
            raise AIServiceError("ai_invalid_response", "AI 测评结果格式异常，请稍后重试")
        return result

    async def build_comparison_action_plan(
        self, role_name: str, profile: dict[str, object], evidence: list[str]
    ) -> ComparisonActionPlan:
        content = await self._chat_completion(
            "Return only JSON with seven_day, thirty_day, and ninety_day arrays. Build a practical "
            "career action plan for the target role using only the supplied profile and evidence. "
            "Do not invent candidate experience or guarantees.",
            json.dumps(
                {"role_name": role_name, "profile": profile, "evidence": evidence},
                ensure_ascii=False,
            ),
        )
        try:
            return ComparisonActionPlan.model_validate_json(content)
        except ValueError as error:
            raise AIServiceError("ai_invalid_response", "AI 职业规划结果格式异常，请稍后重试") from error

    async def build_job_consultation(
        self,
        job: JobIntelligence,
        identity_code: IdentityCode,
        custom_requirement: str | None = None,
    ) -> JobConsultationResponse:
        content = await self._chat_completion(
            "Return only JSON matching JobConsultationResponse. Include nine ordered job analysis "
            "sections, a three-stage career_growth_route, identity-specific plan, market_notice, "
            "risk checks, and custom_requirement_notes. Never invent candidate facts or market facts.",
            json.dumps(
                {
                    "identity_code": identity_code,
                    "job_intelligence": job.model_dump(),
                    "custom_requirement": custom_requirement,
                    "required_json_keys": [
                        "identity_code",
                        "identity_label",
                        "job_intelligence",
                        "job_analysis_sections",
                        "identity_plan",
                        "follow_up_question",
                        "market_notice",
                        "career_growth_route",
                        "custom_requirement_notes",
                    ],
                },
                ensure_ascii=False,
            ),
        )
        return JobConsultationResponse.model_validate_json(content)

    async def review_resume_text(
        self,
        resume_text: str,
        identity_code: IdentityCode,
        role_name: str | None,
        custom_requirement: str | None = None,
    ) -> ResumeReviewResponse:
        content = await self._chat_completion(
            "Return only JSON matching ResumeReviewResponse including optimized_resume_text, "
            "interview_intro, job_match_report, and custom_requirement_notes. Never invent employers, schools, "
            "dates, projects, certificates, or metrics; mark missing evidence as uncertain.",
            json.dumps(
                {
                    "identity_code": identity_code,
                    "role_name": role_name,
                    "resume_text": resume_text,
                    "custom_requirement": custom_requirement,
                },
                ensure_ascii=False,
            ),
        )
        return ResumeReviewResponse.model_validate_json(content)

    async def build_career_advice(
        self,
        identity_code: IdentityCode,
        topic: AdviceTopic,
        role_name: str | None,
        question: str | None,
    ) -> CareerAdviceResponse:
        content = await self._chat_completion(
            "Return only JSON matching CareerAdviceResponse with practical actions, copyable "
            "language, and risk checks. Never present market estimates as verified facts.",
            json.dumps(
                {
                    "identity_code": identity_code,
                    "topic": topic,
                    "role_name": role_name,
                    "question": question,
                },
                ensure_ascii=False,
            ),
        )
        return CareerAdviceResponse.model_validate_json(content)

    async def rewrite_resume(
        self,
        resume: ResumePayload,
        job: JobIntelligence,
        mode: Literal["light", "deep"],
    ) -> ResumePayload:
        content = await self._chat_completion(
            "Return only valid ResumePayload JSON. Improve wording only; never change immutable "
            "employers, dates, schools, certificates, projects, or stated metrics.",
            json.dumps({"mode": mode, "resume": resume.model_dump(), "target_job": job.model_dump()}, ensure_ascii=False),
        )
        return ResumePayload.model_validate_json(content)

    async def build_job_plan(
        self,
        role_name: str,
        profile: dict[str, object],
        evidence: list[dict[str, object]],
        resume: dict[str, object] | None,
        assessment: dict[str, object] | None,
        expand_detail: bool,
    ) -> JobPlanResponse:
        content = await self._chat_completion(
            "Return only valid JSON matching JobPlanResponse. Include exactly these six unique section "
            "keys: market_overview (six-month demand, estimated salary range, entry threshold, competition), "
            "responsibilities (complete core responsibility decomposition), hard_skills (mastered, partial, "
            "and missing gaps), soft_competencies (logic, communication, teamwork, execution), career_value "
            "(short and long term value), and risks (entry obstacles and industry risks). comparison_items must "
            "use only high, transferable, needs_upskilling, or long_shot statuses and must distinguish hard and "
            "soft competencies. promotion_tracks must contain technical and management. When expand_detail is true, "
            "both tracks must contain exactly entry, junior, mid, senior nodes in that order; each node needs salary, "
            "standard years, competencies, a realistic work case, skills, and learning actions. When false, keep "
            "the same JSON shape concise. Treat market information as estimates, use supplied candidate context only, "
            "and never invent candidate facts or evidence.",
            json.dumps({"role_name": role_name, "profile": profile, "evidence": evidence,
                        "resume": resume, "assessment": assessment, "expand_detail": expand_detail},
                       ensure_ascii=False),
        )
        try:
            return JobPlanResponse.model_validate_json(content)
        except ValueError as error:
            raise AIServiceError("ai_invalid_response", "AI job plan response format is invalid") from error

    async def _chat_completion(self, system_prompt: str, user_prompt: str) -> str:
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self._base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {self._api_key}"},
                    json={
                        "model": self._model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                        "response_format": {"type": "json_object"},
                    },
                )
        except httpx.TimeoutException as error:
            raise AIServiceError("ai_timeout", "AI 服务响应超时，请稍后重试") from error
        except httpx.HTTPError as error:
            raise AIServiceError("ai_unavailable", "AI 服务暂时不可用，请稍后重试") from error

        if response.is_error:
            detail = response.text.lower()
            if response.status_code in {401, 403}:
                raise AIServiceError("ai_auth_failed", "AI 服务密钥无效或无访问权限")
            if response.status_code == 429:
                raise AIServiceError("ai_rate_limited", "AI 服务请求过于频繁，请稍后重试")
            if response.status_code == 402 or any(word in detail for word in ("balance", "insufficient", "quota")):
                raise AIServiceError("ai_balance_exhausted", "AI 服务额度不足，请联系管理员")
            raise AIServiceError("ai_unavailable", "AI 服务暂时不可用，请稍后重试")

        try:
            content = response.json()["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError, ValueError) as error:
            raise AIServiceError("ai_invalid_response", "AI 服务返回格式异常，请稍后重试") from error
        return str(content)


class ArkAIClient(OpenAICompatibleClient):
    pass


def build_ai_client(settings: Settings) -> AIClient:
    if settings.ai_provider not in {"ark", "openai_compatible"}:
        return DevelopmentAIClient() if not settings.production else UnconfiguredAIClient()
    if not settings.ai_api_key or not settings.ai_model:
        return DevelopmentAIClient() if not settings.production else UnconfiguredAIClient()
    if settings.ai_provider == "ark":
        return ArkAIClient(settings)
    return OpenAICompatibleClient(settings)
