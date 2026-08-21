from __future__ import annotations

from app.schemas.report import LayeredReport, ReportEvidence, ReportMode
from app.services.membership import VipStatus


class ReportEvidenceInput(ReportEvidence):
    pass


def project_report(
    requested_mode: ReportMode | None,
    default_mode: ReportMode,
    vip: VipStatus | None,
    required_feature: str,
    summary: str,
    actions: list[str],
    evidence: list[ReportEvidenceInput],
    source_notice: str,
    professional_actions: list[str],
) -> LayeredReport:
    desired_mode = requested_mode or default_mode
    is_professional = (
        desired_mode == "professional"
        and vip is not None
        and vip.allows(required_feature)
    )
    validated_evidence = [ReportEvidence.model_validate(item) for item in evidence]
    return LayeredReport(
        mode="professional" if is_professional else "simplified",
        summary=summary,
        actions=professional_actions if is_professional else actions[:3],
        evidence=validated_evidence if is_professional else [],
        source_notice=source_notice,
        upgrade_notice="" if is_professional else "Upgrade to view professional evidence and detailed actions.",
    )
