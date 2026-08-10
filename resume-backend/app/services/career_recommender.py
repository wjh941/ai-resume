from __future__ import annotations

from datetime import datetime, timezone

from app.repositories.career_catalog import CareerCatalogRepository
from app.schemas.career import (
    AssessmentGuidance,
    CareerComparisonItem,
    CareerComparisonResponse,
    CareerProfile,
    CareerRecommendation,
    CareerRecommendationResponse,
    ComparisonActionPlan,
    MajorFitReport,
    MatchingLevel,
    RoleProfile,
    ScoreBreakdown,
)


class CareerRecommender:
    """Produces explainable direction recommendations, not offer predictions."""

    def __init__(self, catalog_repository: CareerCatalogRepository) -> None:
        self._catalog_repository = catalog_repository

    def recommend(
        self,
        profile: CareerProfile,
        assessment_result: dict[str, object] | None = None,
    ) -> CareerRecommendationResponse:
        ranked = [
            self._score_role(profile, role)
            for role in self._catalog_repository.list_roles()
        ]
        ranked.sort(key=lambda item: (-item.total_score, item.role.role_name))
        tiers = self._build_tiers(ranked)
        major_report = self._build_major_report(profile, tiers)
        return CareerRecommendationResponse(
            profile=profile,
            generated_at=datetime.now(timezone.utc).isoformat(),
            recommendation_notice=(
                "推荐基于已填写的专业、技能和偏好生成，用于比较发展方向和补齐路径，"
                "不代表录用概率、薪资承诺或岗位保证。"
            ),
            major_report=major_report,
            assessment_guidance=self._assessment_guidance(assessment_result),
            tiers=tiers,
        )

    def compare(
        self,
        profile: CareerProfile,
        roles: list[RoleProfile],
    ) -> CareerComparisonResponse:
        items = [
            self._comparison_item(profile, role)
            for role in roles
        ]
        common_strengths = (
            list(
                set.intersection(
                    *(set(item.matching_advantages) for item in items)
                )
            )
            if items
            else []
        )
        return CareerComparisonResponse(
            profile=profile,
            items=items,
            common_strengths=sorted(common_strengths),
            recommendation_notice=(
                "对比仅使用本地岗位库、已填写职业画像与已确认经历作为方向支持，"
                "不代表录用概率、薪资承诺或市场实时预测。"
            ),
        )

    def _comparison_item(
        self,
        profile: CareerProfile,
        role: RoleProfile,
    ) -> CareerComparisonItem:
        recommendation = self._score_role(profile, role)
        priorities = recommendation.missing_skills[:3] or role.entry_skills[:3]
        action_plan = ComparisonActionPlan(
            seven_day=[
                f"完成 {skill} 的基础练习，并保留代码、笔记或截图证据。"
                for skill in priorities[:2]
            ],
            thirty_day=[
                f"围绕 {role.role_name} 完成一个小型练习项目，记录真实职责、过程和结果。",
                "将练习过程整理为可复核材料；没有结果时保留[待确认]。",
            ],
            ninety_day=[
                f"投递或参与与“{role.internship_roles[0]}”相关的真实机会，并复盘反馈。",
                f"根据真实反馈更新 {role.role_name} 的技能缺口和下一轮行动。",
            ],
        )
        advantages = [*recommendation.matching_advantages]
        return CareerComparisonItem(
            role=role,
            total_score=recommendation.total_score,
            matching_level=recommendation.matching_level,
            score_breakdown=recommendation.score_breakdown,
            matching_advantages=advantages,
            missing_skills=recommendation.missing_skills,
            alternatives=recommendation.alternatives,
            risk_notice=(
                f"{self._feasibility_reason(profile, role)} "
                "评分仅用于方向比较，不代表录用概率、薪资承诺或岗位保证。"
            ),
            action_plan=action_plan,
        )

    @staticmethod
    def _assessment_guidance(
        assessment_result: dict[str, object] | None,
    ) -> AssessmentGuidance | None:
        if not assessment_result:
            return None

        raw_interests = assessment_result.get("top_interests", [])
        top_interest_keys = [
            str(item["key"])
            for item in raw_interests
            if isinstance(item, dict) and item.get("key")
        ]
        raw_evidence = assessment_result.get("strength_evidence", [])
        strength_evidence = [str(item) for item in raw_evidence if str(item).strip()]
        raw_plan = assessment_result.get("action_plan", {})
        action_plan = {
            key: [str(item) for item in raw_plan.get(key, []) if str(item).strip()]
            for key in ("seven_day", "thirty_day", "ninety_day")
            if isinstance(raw_plan, dict)
        }
        return AssessmentGuidance(
            top_interest_keys=top_interest_keys,
            strength_evidence=strength_evidence,
            action_plan=action_plan,
            notice=(
                "测评结果只作为补充的职业决策支持，请结合真实经历、岗位要求和实际反馈调整方向。"
            ),
        )

    def _score_role(
        self,
        profile: CareerProfile,
        role: RoleProfile,
    ) -> CareerRecommendation:
        professional, professional_reason = self._professional_score(profile, role)
        skill, missing_skills = self._skill_score(profile, role)
        feasibility = self._feasibility_score(profile, role)
        preference, preference_reason = self._preference_score(profile, role)
        market_reason = "未接入授权城市薪资数据时，市场信号按中性 5/10 计入。"

        breakdown = [
            ScoreBreakdown(
                key="professional",
                label="专业关联",
                score=professional,
                max_score=30,
                reason=professional_reason,
            ),
            ScoreBreakdown(
                key="skills",
                label="技能匹配",
                score=skill,
                max_score=25,
                reason=(
                    "已覆盖岗位核心技能。"
                    if not missing_skills
                    else f"优先补齐：{'、'.join(missing_skills[:3])}。"
                ),
                missing_evidence=missing_skills,
            ),
            ScoreBreakdown(
                key="feasibility",
                label="进入可行性",
                score=feasibility,
                max_score=20,
                reason=self._feasibility_reason(profile, role),
            ),
            ScoreBreakdown(
                key="preference",
                label="个人偏好",
                score=preference,
                max_score=15,
                reason=preference_reason,
            ),
            ScoreBreakdown(
                key="market",
                label="市场信号",
                score=5,
                max_score=10,
                reason=market_reason,
                missing_evidence=(
                    ["可在联网授权数据接入后补充目标城市和薪资验证。"]
                    if profile.city_preferences or profile.minimum_salary
                    else []
                ),
            ),
        ]
        total_score = round(sum(item.score for item in breakdown))
        matching_level = self._matching_level(
            professional,
            role,
            profile,
            missing_skills,
        )
        advantages = self._advantages(profile, role, professional, skill, preference)
        return CareerRecommendation(
            role=role,
            tier="stable",
            total_score=max(0, min(total_score, 100)),
            matching_level=matching_level,
            score_breakdown=breakdown,
            matching_advantages=advantages,
            missing_skills=missing_skills,
            action_plan=self._action_plan(role, missing_skills),
            alternatives=role.alternative_roles,
        )

    @staticmethod
    def _professional_score(profile: CareerProfile, role: RoleProfile) -> tuple[float, str]:
        major = _normalized(profile.major)
        recommended = {_normalized(value) for value in role.recommended_majors}
        adjacent = {_normalized(value) for value in role.adjacent_majors}
        if major in recommended:
            return 30, "所学专业与该岗位的直接推荐专业一致。"
        if major in adjacent:
            return 22, "所学专业属于该岗位可迁移的相邻专业。"
        return 10, "属于跨专业方向，需要以课程、项目和技能证据证明转化能力。"

    @staticmethod
    def _skill_score(profile: CareerProfile, role: RoleProfile) -> tuple[float, list[str]]:
        user_skills = {_normalized(value) for value in profile.skills}
        required_skills = role.required_skills
        matched = [
            skill
            for skill in required_skills
            if _normalized(skill) in user_skills
        ]
        missing = [skill for skill in required_skills if skill not in matched]
        if not required_skills:
            return 0, []
        return round(25 * len(matched) / len(required_skills), 1), missing

    @staticmethod
    def _feasibility_score(profile: CareerProfile, role: RoleProfile) -> float:
        base_by_difficulty = {1: 20, 2: 18, 3: 14, 4: 9, 5: 5}
        score = base_by_difficulty[role.entry_difficulty]
        if profile.identity_code in {"1", "2", "5"} and role.entry_difficulty >= 4:
            score -= 2
        if profile.identity_code == "3" and role.entry_difficulty >= 4:
            score += 2
        return max(0, min(float(score), 20))

    @staticmethod
    def _feasibility_reason(profile: CareerProfile, role: RoleProfile) -> str:
        identity_hint = {
            "1": "实习求职阶段",
            "2": "校招阶段",
            "3": "在职转岗或跳槽阶段",
            "4": "待业求职阶段",
            "5": "零基础转行阶段",
        }[profile.identity_code]
        return f"{identity_hint}下，该方向的入门门槛评估为 {role.entry_difficulty}/5。"

    @staticmethod
    def _preference_score(profile: CareerProfile, role: RoleProfile) -> tuple[float, str]:
        preferences = {_normalized(value) for value in profile.industry_preferences}
        industry_tags = {_normalized(value) for value in role.industry_tags}
        if not preferences:
            industry_score = 6
            industry_reason = "尚未限定行业，保留探索空间。"
        elif preferences & industry_tags:
            industry_score = 10
            industry_reason = "岗位常见行业与已选偏好存在交集。"
        else:
            industry_score = 3
            industry_reason = "与当前行业偏好交集有限，可作为备选方向。"

        work_score = 5 if profile.work_types else 3
        work_reason = "已提供工作形式偏好。" if profile.work_types else "尚未限定工作形式。"
        return float(industry_score + work_score), f"{industry_reason}{work_reason}"

    @staticmethod
    def _matching_level(
        professional_score: float,
        role: RoleProfile,
        profile: CareerProfile,
        missing_skills: list[str],
    ) -> MatchingLevel:
        covered = len(role.required_skills) - len(missing_skills)
        if professional_score == 30 and covered >= max(1, len(role.required_skills) // 3):
            return "high"
        if professional_score >= 22:
            return "transferable"
        if professional_score >= 10 and covered >= 1:
            return "needs_upskilling"
        return "long_shot"

    @staticmethod
    def _advantages(
        profile: CareerProfile,
        role: RoleProfile,
        professional_score: float,
        skill_score: float,
        preference_score: float,
    ) -> list[str]:
        advantages = [
            (
                "专业与岗位方向直接关联。"
                if professional_score == 30
                else "专业具备可迁移基础，可通过作品或项目形成证据。"
            )
        ]
        if skill_score:
            advantages.append("已填写技能中存在岗位可复用基础。")
        if preference_score >= 13:
            advantages.append("岗位行业方向与当前个人偏好较为一致。")
        if profile.draft_id:
            advantages.append("可将现有简历草稿作为该方向的优化起点。")
        return advantages

    @staticmethod
    def _action_plan(role: RoleProfile, missing_skills: list[str]) -> list[str]:
        priorities = missing_skills[:3] or list(role.entry_skills[:3])
        return [
            f"学习并完成 {skill} 的基础练习，保留过程截图、代码或文档证据。"
            for skill in priorities
        ] + [
            f"围绕 {role.role_name} 完成一个可验证的小型项目，不把未知成果写进简历。",
            f"寻找“{role.internship_roles[0]}”或“{role.alternative_roles[0]}”相关机会，先积累真实场景经验。",
        ]

    @staticmethod
    def _build_tiers(
        ranked: list[CareerRecommendation],
    ) -> dict[str, list[CareerRecommendation]]:
        used: set[str] = set()

        def eligible(recommendation: CareerRecommendation, predicate) -> bool:
            return (
                recommendation.role.role_name not in used
                and predicate(recommendation)
            )

        def take(
            predicate,
            tier: str,
            limit: int = 6,
            prefer_distinct_families: bool = False,
        ) -> list[CareerRecommendation]:
            items: list[CareerRecommendation] = []
            selected_families: set[str] = set()

            if prefer_distinct_families:
                for recommendation in ranked:
                    if (
                        not eligible(recommendation, predicate)
                        or recommendation.role.family in selected_families
                    ):
                        continue
                    used.add(recommendation.role.role_name)
                    selected_families.add(recommendation.role.family)
                    items.append(recommendation.model_copy(update={"tier": tier}))
                    if len(items) == limit:
                        return items

            for recommendation in ranked:
                if not eligible(recommendation, predicate):
                    continue
                used.add(recommendation.role.role_name)
                items.append(recommendation.model_copy(update={"tier": tier}))
                if len(items) == limit:
                    break
            return items

        stable = take(
            lambda item: item.total_score >= 58
            and item.matching_level in {"high", "transferable"},
            "stable",
            prefer_distinct_families=True,
        )
        safe = take(
            lambda item: item.role.entry_difficulty <= 3 and item.total_score >= 42,
            "safe",
        )
        stretch = take(
            lambda item: item.role.entry_difficulty >= 4
            or item.matching_level in {"needs_upskilling", "long_shot"},
            "stretch",
        )
        if not stable:
            stable = take(lambda _: True, "stable", limit=3, prefer_distinct_families=True)
        if not safe:
            safe = take(lambda _: True, "safe", limit=3)
        if not stretch:
            stretch = take(lambda _: True, "stretch", limit=3)
        return {"stretch": stretch, "stable": stable, "safe": safe}
    @staticmethod
    def _build_major_report(
        profile: CareerProfile,
        tiers: dict[str, list[CareerRecommendation]],
    ) -> MajorFitReport:
        preferred = (
            tiers["stable"][:1]
            or tiers["stretch"][:1]
            or tiers["safe"][:1]
        )
        if not preferred:
            return MajorFitReport(
                major=profile.major,
                matching_level="long_shot",
                matching_advantages=[],
                missing_skills=[],
                recommended_courses=[],
                recommended_projects=[],
                practice_tasks=[],
            )
        target = preferred[0]
        return MajorFitReport(
            major=profile.major,
            matching_level=target.matching_level,
            matching_advantages=target.matching_advantages,
            missing_skills=target.missing_skills[:5],
            recommended_courses=target.role.relevant_courses[:4],
            recommended_projects=[
                f"完成一个与 {target.role.role_name} 相关的课程或个人项目，并记录真实职责。",
                "将项目拆为需求、过程、结果三部分，结果缺失时标记为[待确认]。",
            ],
            practice_tasks=target.action_plan[:4],
        )


def _normalized(value: str) -> str:
    return " ".join(value.split()).casefold()
