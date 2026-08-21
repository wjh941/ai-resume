from __future__ import annotations

from dataclasses import dataclass

from app.schemas.career import JobMatchItem, JobMatchRequest, RoleProfile
from app.services.mock_job_samples import get_mock_job_sample


def _normalized(value: str) -> str:
    return "".join(str(value).casefold().split())


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        normalized = _normalized(value)
        if normalized and normalized not in seen:
            seen.add(normalized)
            result.append(value)
    return result


@dataclass(frozen=True)
class MatchContext:
    skills: list[str]
    evidence_text: str
    target_roles: list[str]


class JobMatcher:
    """Explainable local-catalog matcher. It never claims to return live vacancies."""

    _cities_by_family = {
        "数据与分析": ("北京", "上海", "杭州", "深圳"),
        "人工智能": ("北京", "上海", "深圳", "杭州"),
        "产品与运营": ("北京", "上海", "广州", "杭州"),
        "技术基础设施": ("北京", "上海", "深圳", "成都"),
    }

    def match(
        self,
        context: MatchContext,
        roles: list[RoleProfile],
        filters: JobMatchRequest,
        *,
        detail_unlocked: bool,
    ) -> list[JobMatchItem]:
        matches = [
            item
            for role in roles
            if (item := self._match_role(context, role, detail_unlocked)) is not None
            and self._matches_filters(item, filters)
        ]
        return sorted(matches, key=lambda item: (-item.match_score, item.role_name))

    def _match_role(
        self,
        context: MatchContext,
        role: RoleProfile,
        detail_unlocked: bool,
    ) -> JobMatchItem:
        sample = get_mock_job_sample(role.role_name)
        requirements = list(sample.requirements) if sample else _unique([*role.required_skills, *role.entry_skills])
        known_skills = {_normalized(skill) for skill in context.skills}
        evidence_text = _normalized(context.evidence_text)
        matched = [
            skill
            for skill in requirements
            if _normalized(skill) in known_skills or _normalized(skill) in evidence_text
        ]
        missing = [skill for skill in requirements if skill not in matched]
        coverage = len(matched) / len(requirements) if requirements else 0
        target_signal = any(
            _normalized(role.role_name) in _normalized(target)
            or _normalized(target) in _normalized(role.role_name)
            for target in context.target_roles
            if _normalized(target)
        )
        evidence_bonus = min(10, 2 * len(matched))
        score = min(100, round(28 + coverage * 52 + evidence_bonus + (10 if target_signal else 0)))
        seniority = "entry" if role.entry_difficulty <= 2 else "mid" if role.entry_difficulty <= 4 else "senior"
        salary_min = 6 + role.entry_difficulty * 2
        salary_max = salary_min + 8 + role.entry_difficulty * 2
        cities = self._cities_by_family.get(role.family, ("北京", "上海", "深圳"))
        return JobMatchItem(
            role_name=role.role_name,
            company=sample.company if sample else "本地岗位库参考",
            city=sample.city if sample else " / ".join(cities),
            salary_range=sample.salary_range if sample else f"{salary_min}k-{salary_max}k（本地参考）",
            seniority=seniority,
            category=role.family,
            match_score=score,
            matched_skills=matched,
            missing_skills=missing if detail_unlocked else missing[:2],
            description=role.description,
            responsibilities=(
                list(sample.responsibilities)
                if sample
                else [f"参与{role.role_name}相关的可验证交付"]
            ),
            requirements=requirements if detail_unlocked else requirements[:3],
            match_score_reference=sample.match_score_reference if sample else None,
            detail_unlocked=detail_unlocked,
        )

    @staticmethod
    def _matches_filters(item: JobMatchItem, filters: JobMatchRequest) -> bool:
        if filters.category and _normalized(filters.category) not in _normalized(item.category):
            return False
        if filters.city and _normalized(filters.city) not in _normalized(item.city):
            return False
        if filters.seniority and filters.seniority != item.seniority:
            return False
        salary_values = [int(value.rstrip("k")) for value in item.salary_range.split("（", 1)[0].split("-")]
        if filters.salary_min is not None and salary_values[1] < filters.salary_min:
            return False
        if filters.salary_max is not None and salary_values[0] > filters.salary_max:
            return False
        return True
