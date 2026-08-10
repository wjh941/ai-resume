from app.schemas.evidence import ResumeEvidence
from app.services.evidence_suggestions import build_evidence_suggestions


def make_evidence(**changes) -> ResumeEvidence:
    payload = {
        "id": "evidence-1",
        "client_id": "client-a",
        "kind": "project",
        "title": "Data quality coursework",
        "context": "Database systems course",
        "actions": "Implemented ETL validation rules",
        "outcome": "",
        "proof_note": "Repository screenshot",
        "verified": True,
        "created_at": "2026-08-10T00:00:00+00:00",
        "updated_at": "2026-08-10T00:00:00+00:00",
    }
    payload.update(changes)
    return ResumeEvidence(**payload)


def test_suggestions_keep_unknown_outcome_marked_pending():
    suggestion = build_evidence_suggestions(
        "Data Engineer",
        [make_evidence()],
    )[0]

    assert suggestion.target_section == "project"
    assert suggestion.source_evidence_id == "evidence-1"
    assert "Implemented ETL validation rules" in suggestion.description
    assert "[待确认" in suggestion.description
    assert "40%" not in suggestion.description


def test_suggestions_prioritize_verified_evidence_and_limit_to_three():
    evidence = [
        make_evidence(id="unverified", verified=False, title="Unverified evidence"),
        make_evidence(id="verified-1", title="Verified evidence one"),
        make_evidence(id="verified-2", title="Verified evidence two"),
        make_evidence(id="verified-3", title="Verified evidence three"),
    ]

    suggestions = build_evidence_suggestions("Data Engineer", evidence)

    assert [item.source_evidence_id for item in suggestions] == [
        "verified-1",
        "verified-2",
        "verified-3",
    ]
