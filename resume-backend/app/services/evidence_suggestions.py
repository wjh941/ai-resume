from __future__ import annotations

from app.schemas.evidence import ResumeEvidence
from app.schemas.resume_quality import EvidenceSuggestion


PENDING_MARKER = "[待确认]"
PENDING_OUTCOME = "[待确认：补充真实成果或核验证据]"
PENDING_CONTEXT = "[待确认：补充真实场景]"


def build_evidence_suggestions(
    role_name: str,
    evidence_items: list[ResumeEvidence],
) -> list[EvidenceSuggestion]:
    ranked = sorted(
        enumerate(evidence_items),
        key=lambda item: (not item[1].verified, item[0]),
    )
    return [
        _build_suggestion(role_name, evidence)
        for _, evidence in ranked[:3]
    ]


def _build_suggestion(role_name: str, evidence: ResumeEvidence) -> EvidenceSuggestion:
    target_section = (
        "employment"
        if evidence.kind in {"internship", "employment"}
        else "project"
    )
    context = evidence.context or PENDING_CONTEXT
    outcome = evidence.outcome or PENDING_OUTCOME
    risk_note = "" if evidence.verified and evidence.outcome else (
        "该建议仅使用你保存的经历；请确认场景、成果和证据后再导出。"
    )
    return EvidenceSuggestion(
        source_evidence_id=evidence.id,
        source_title=evidence.title,
        target_section=target_section,
        title=evidence.title,
        role=f"{role_name} 相关经历",
        description="\n".join(
            (
                f"场景：{context}",
                f"行动：{evidence.actions}",
                f"成果与证据：{outcome}",
            )
        ),
        risk_note=risk_note,
    )
