from __future__ import annotations

from copy import deepcopy
from typing import Literal

from app.schemas.consultation import (
    AdviceTopic,
    CareerAdviceResponse,
    IdentityCode,
    JobConsultationResponse,
    ResumeReviewResponse,
)
from app.schemas.job import JobIntelligence
from app.schemas.resume import ResumePayload
from app.schemas.career import (
    ComparisonActionPlan,
    JobPlanResponse,
    JobPlanSection,
    PromotionNode,
    PromotionTrack,
)
from app.services.career_consultation import (
    build_career_advice,
    build_job_consultation,
    build_resume_review,
)
from app.services.career_assessment import score_assessment


class TestAIClient:
    """测试专用替身：通过 app.state 注入，生产代码绝不导入该类。"""

    __test__ = False

    def __init__(self) -> None:
        self.job_query_count = 0
        self.assessment_query_count = 0
        self.action_plan_query_count = 0
        self.job_plan_query_count = 0
        self.rewrite_result: ResumePayload | dict | None = None

    async def query_job(self, role_name: str) -> JobIntelligence:
        self.job_query_count += 1
        normalized = role_name.casefold()
        if any(word in normalized for word in ("frontend", "vue", "react", "前端")):
            return JobIntelligence(
                role_name=role_name.strip(),
                required_skills=["JavaScript", "TypeScript", "Vue or React"],
                bonus_skills=["Performance profiling"],
                responsibilities=["Build accessible product interfaces."],
            )
        if "agent" in normalized:
            return JobIntelligence(
                role_name=role_name.strip(),
                required_skills=["Python", "LLM应用开发", "Agent工作流"],
                bonus_skills=["RAG"],
                responsibilities=["Build reliable AI workflows."],
            )
        return JobIntelligence(
            role_name=role_name.strip(),
            required_skills=["Python", "SQL", "Data warehousing"],
            bonus_skills=["Airflow", "Spark"],
            responsibilities=["Build reliable data pipelines."],
        )

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
        for item in [*rewritten.employment, *rewritten.projects]:
            if item.description:
                item.description = f"{item.description}{suffix}"
        if rewritten.self_evaluation:
            rewritten.self_evaluation = f"{rewritten.self_evaluation}{suffix}"
        return rewritten

    async def assess_career(
        self,
        questions: list[dict[str, object]],
        answers: dict[str, int],
    ) -> dict[str, object]:
        self.assessment_query_count += 1
        return score_assessment(answers)

    async def build_comparison_action_plan(
        self, role_name: str, profile: dict[str, object], evidence: list[str]
    ) -> ComparisonActionPlan:
        self.action_plan_query_count += 1
        return ComparisonActionPlan(
            seven_day=[f"Review {role_name} requirements."],
            thirty_day=[f"Build a {role_name} portfolio artifact."],
            ninety_day=[f"Run a {role_name} interview retrospective."],
        )

    async def build_job_plan(
        self,
        role_name: str,
        profile: dict[str, object],
        evidence: list[str],
        resume: dict[str, object] | None,
        assessment: dict[str, object] | None,
        expand_detail: bool,
    ) -> JobPlanResponse:
        self.job_plan_query_count += 1
        sections = [
            JobPlanSection(key=key, title=title, summary=f"{title} for {role_name}")
            for key, title in (
                ("market_context", "Market context"),
                ("responsibilities", "Responsibilities"),
                ("hard_skill_gaps", "Hard-skill gaps"),
                ("soft_competencies", "Soft competencies"),
                ("career_value", "Career value"),
                ("risks", "Risks"),
            )
        ]
        tracks = [
            PromotionTrack(
                key="technical",
                title="Technical track",
                nodes=[
                    PromotionNode(title="Associate", level="entry", description=f"Start {role_name} work.", salary_band="10k-18k", standard_years="1-3 years", competencies=["Delivery"], case_detail="Ship a verified project."),
                    PromotionNode(title="Senior", level="advanced", description=f"Lead {role_name} delivery.", salary_band="18k-30k", standard_years="3-6 years", competencies=["Architecture"], case_detail="Lead a measurable outcome."),
                ],
            ),
            PromotionTrack(
                key="management",
                title="Management track",
                nodes=[
                    PromotionNode(title="Lead", level="lead", description=f"Coordinate {role_name} work.", salary_band="20k-32k", standard_years="4-7 years", competencies=["Planning"], case_detail="Coordinate a cross-functional delivery."),
                    PromotionNode(title="Manager", level="manager", description=f"Manage {role_name} teams.", salary_band="28k-45k", standard_years="7+ years", competencies=["People leadership"], case_detail="Set goals and review outcomes."),
                ],
            ),
        ]
        return JobPlanResponse(
            role_name=role_name,
            report_scope="detailed" if expand_detail else "brief",
            sections=sections,
            comparison_items=[],
            promotion_tracks=tracks,
            action_plan=ComparisonActionPlan(
                seven_day=[f"Review {role_name} requirements."],
                thirty_day=[f"Build a {role_name} portfolio artifact."],
                ninety_day=[f"Run a {role_name} interview retrospective."],
            ),
        )
