from __future__ import annotations

from app.schemas.resume import ResumePayload
from app.schemas.resume_quality import ResumeReadinessReport
from app.services.evidence_suggestions import PENDING_MARKER


def inspect_resume_readiness(resume: ResumePayload) -> ResumeReadinessReport:
    blocking_items = _blocking_items(resume)
    warning_items = _warning_items(resume)
    return ResumeReadinessReport(
        ready=not blocking_items,
        blocking_items=blocking_items,
        warning_items=warning_items,
    )


def _blocking_items(resume: ResumePayload) -> list[str]:
    requirements = (
        ("姓名", resume.basic.name),
        ("手机号", resume.basic.phone),
        ("邮箱", resume.basic.email),
        ("目标岗位", resume.job.target_role),
    )
    return [label for label, value in requirements if not value.strip()]


def _warning_items(resume: ResumePayload) -> list[str]:
    warnings: list[str] = []
    if PENDING_MARKER in _resume_text(resume):
        warnings.append("存在 [待确认] 内容，请替换为真实经历、成果或证据。")
    if not resume.projects and not resume.employment:
        warnings.append("尚未填写项目或实习/工作经历，建议补充可核验的真实经历。")
    if any(not item.description.strip() for item in resume.projects):
        warnings.append("存在项目经历未填写描述。")
    if any(not item.description.strip() for item in resume.employment):
        warnings.append("存在实习/工作经历未填写描述。")
    return warnings


def _resume_text(resume: ResumePayload) -> str:
    values = [
        resume.basic.name,
        resume.basic.phone,
        resume.basic.email,
        resume.basic.city,
        resume.job.target_role,
        resume.job.employment_type,
        resume.job.expected_salary,
        resume.self_evaluation,
    ]
    values.extend(
        value
        for item in resume.education
        for value in (
            item.school,
            item.major,
            item.degree,
            item.start_date,
            item.end_date,
        )
    )
    values.extend(
        value
        for item in resume.employment
        for value in (
            item.company,
            item.position,
            item.start_date,
            item.end_date,
            item.description,
        )
    )
    values.extend(
        value
        for item in resume.projects
        for value in (
            item.name,
            item.role,
            item.start_date,
            item.end_date,
            item.description,
        )
    )
    values.extend(resume.skills.skills)
    values.extend(resume.skills.certificates)
    return "\n".join(values)
