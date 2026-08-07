from __future__ import annotations

from copy import deepcopy
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
from app.services.career_consultation import (
    build_career_advice,
    build_job_consultation,
    build_resume_review,
)
from app.services.job_cache import normalize_role_name

MOCK_CACHE_KEY = "mock-v2"


class AIClient(Protocol):
    async def query_job(self, role_name: str) -> JobIntelligence: ...

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


def mock_job_profile(role_name: str) -> JobIntelligence:
    normalized_role = normalize_role_name(role_name)
    display_role = " ".join(part.capitalize() for part in normalized_role.split())

    data_profile = {
        "salary_by_experience": {
            "graduate": "10k-16k",
            "1-3_years": "16k-26k",
            "3-5_years": "26k-38k",
            "5_plus_years": "38k-55k",
        },
        "responsibilities": [
            "Build reliable data pipelines and data models.",
            "Collaborate with analysts and product teams on data delivery.",
        ],
        "hard_requirements": ["Bachelor degree or equivalent practical experience."],
        "required_skills": ["Python", "SQL", "Data warehousing"],
        "bonus_skills": ["Airflow", "Spark", "Cloud platforms"],
        "career_route": ["Data Engineer", "Senior Data Engineer", "Data Platform Lead"],
    }
    frontend_profile = {
        "salary_by_experience": {
            "graduate": "12k-18k",
            "1-3_years": "18k-30k",
            "3-5_years": "30k-45k",
            "5_plus_years": "45k-65k",
        },
        "responsibilities": [
            "Build responsive interfaces and reusable component systems.",
            "Collaborate with product and design teams to improve web experiences.",
        ],
        "hard_requirements": ["Bachelor degree or equivalent practical experience."],
        "required_skills": ["JavaScript", "TypeScript", "Vue or React"],
        "bonus_skills": ["Vite", "State management", "Frontend performance"],
        "career_route": ["Frontend Engineer", "Senior Frontend Engineer", "Frontend Architect"],
    }
    backend_profile = {
        "salary_by_experience": {
            "graduate": "12k-18k",
            "1-3_years": "18k-30k",
            "3-5_years": "30k-44k",
            "5_plus_years": "44k-62k",
        },
        "responsibilities": [
            "Design stable service APIs and core business modules.",
            "Improve reliability, observability, and delivery efficiency.",
        ],
        "hard_requirements": ["Bachelor degree or equivalent practical experience."],
        "required_skills": ["Python or Java", "SQL", "API design"],
        "bonus_skills": ["Docker", "Redis", "Distributed systems"],
        "career_route": ["Backend Engineer", "Senior Backend Engineer", "Technical Lead"],
    }
    product_profile = {
        "salary_by_experience": {
            "graduate": "10k-15k",
            "1-3_years": "15k-25k",
            "3-5_years": "25k-36k",
            "5_plus_years": "36k-52k",
        },
        "responsibilities": [
            "Define user problems, product goals, and measurable outcomes.",
            "Coordinate research, design, engineering, and launch decisions.",
        ],
        "hard_requirements": ["Bachelor degree or equivalent practical experience."],
        "required_skills": ["Requirement analysis", "User research", "Data analysis"],
        "bonus_skills": ["Experiment design", "Roadmap planning", "Stakeholder management"],
        "career_route": ["Product Manager", "Senior Product Manager", "Product Lead"],
    }
    generic_profile = {
        "salary_by_experience": {
            "graduate": "8k-14k",
            "1-3_years": "14k-22k",
            "3-5_years": "22k-32k",
            "5_plus_years": "32k-48k",
        },
        "responsibilities": [
            f"Deliver reliable outcomes for the {display_role} role.",
            "Collaborate across teams to improve quality and delivery efficiency.",
        ],
        "hard_requirements": ["Bachelor degree or equivalent practical experience."],
        "required_skills": ["Domain knowledge", "Communication", "Problem solving"],
        "bonus_skills": ["Data literacy", "Project coordination", "Continuous improvement"],
        "career_route": [display_role, f"Senior {display_role}", "Team Lead"],
    }

    if any(keyword in normalized_role for keyword in ("数据", "data", "etl", "数仓")):
        profile = data_profile
    elif any(keyword in normalized_role for keyword in ("前端", "frontend", "vue", "react")):
        profile = frontend_profile
    elif any(keyword in normalized_role for keyword in ("后端", "backend", "服务端", "java")):
        profile = backend_profile
    elif any(keyword in normalized_role for keyword in ("产品", "product")):
        profile = product_profile
    else:
        profile = generic_profile

    return JobIntelligence(role_name=display_role, **profile)


class MockAIClient:
    def __init__(self) -> None:
        self.job_query_count = 0
        self.rewrite_result: ResumePayload | dict | None = None

    async def query_job(self, role_name: str) -> JobIntelligence:
        self.job_query_count += 1
        return mock_job_profile(role_name)

    async def build_job_consultation(
        self,
        job: JobIntelligence,
        identity_code: IdentityCode,
        custom_requirement: str | None = None,
    ) -> JobConsultationResponse:
        return build_job_consultation(job, identity_code, custom_requirement)

    async def review_resume_text(
        self,
        resume_text: str,
        identity_code: IdentityCode,
        role_name: str | None,
        custom_requirement: str | None = None,
    ) -> ResumeReviewResponse:
        return build_resume_review(resume_text, identity_code, role_name, custom_requirement)

    async def build_career_advice(
        self,
        identity_code: IdentityCode,
        topic: AdviceTopic,
        role_name: str | None,
        question: str | None,
    ) -> CareerAdviceResponse:
        return build_career_advice(identity_code, topic, role_name, question)

    async def rewrite_resume(
        self,
        resume: ResumePayload,
        job: JobIntelligence,
        mode: Literal["light", "deep"],
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

    async def build_job_consultation(
        self,
        job: JobIntelligence,
        identity_code: IdentityCode,
        custom_requirement: str | None = None,
    ) -> JobConsultationResponse:
        content = await self._chat_completion(
            system_prompt=(
                "You are an experienced Chinese career consultant. Return only valid JSON. "
                "Provide exactly nine concise job-analysis sections ordered 1 through 9: "
                "基础工作, 薪酬分层, 硬性准入门槛, 隐性软要求, 双晋升通道, 行业前景, "
                "求职竞争, 岗位优缺点, 岗位避雷点. Then provide an identity-specific "
                "practical plan with copyable templates. Return career_growth_route with exactly "
                "three actionable stages: 初级, 中级, 高级; each must include role_name, "
                "years_reference, core_skills, responsibilities, and assessment_criteria. "
                "Return custom_requirement_notes and explicitly apply custom_requirement when it "
                "is supplied. Make 隐性软要求 and 行业前景 specific about observable work behavior "
                "and evidence. Prefix job risks with 【避雷】 or 【高频坑】. Include a market_notice "
                "and state whether information is a verified live source or an estimate. Do not "
                "invent candidate facts, salary facts, or market facts."
            ),
            user_prompt=json.dumps(
                {
                    "identity_code": identity_code,
                    "identity_label": {
                        "1": "在校学生（寻找短期实习）",
                        "2": "应届毕业生（秋招/春招）",
                        "3": "在职人员（想跳槽）",
                        "4": "无业待业（有工作经验空档期）",
                        "5": "零基础跨行业转行",
                    }[identity_code],
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
            system_prompt=(
                "You are an experienced Chinese career consultant. Return only valid JSON with "
                "identity_code, identity_label, issues, rewrite_examples, keywords, "
                "optimized_resume_text, interview_intro, job_match_report, and "
                "custom_requirement_notes. Do not output job analysis. "
                "Never invent employers, schools, dates, projects, certificates, or metrics. "
                "Mark unknown evidence as [待确认]. job_match_report must include an integer 0-100 "
                "coverage score, transparent score_basis, matching_advantages, missing_skills, "
                "and priority_gaps with learning_direction, project_practice, and practice_task. "
                "Apply custom_requirement when supplied without changing user facts."
            ),
            user_prompt=json.dumps(
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
            system_prompt=(
                "You are an experienced Chinese career consultant. Return only valid JSON with "
                "identity_code, identity_label, topic, title, and sections. Use concise mobile "
                "friendly bullet-style items. Never invent candidate facts, legal conclusions, or "
                "market data. Mark uncertain items as [待确认]."
            ),
            user_prompt=json.dumps(
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
