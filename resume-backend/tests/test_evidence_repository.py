from app.db import initialize_database
from app.repositories.evidence import EvidenceRepository
from app.schemas.evidence import ResumeEvidenceSaveRequest


def make_payload(**changes) -> ResumeEvidenceSaveRequest:
    payload = {
        "client_id": "client-a",
        "kind": "project",
        "title": "Data quality coursework",
        "context": "Database systems course",
        "actions": "Implemented validation rules",
        "outcome": "",
        "proof_note": "Repository screenshot",
        "verified": True,
    }
    payload.update(changes)
    return ResumeEvidenceSaveRequest(**payload)


def test_evidence_round_trip_is_scoped_to_client(tmp_path):
    database_path = tmp_path / "resume_demo.db"
    initialize_database(database_path)
    repository = EvidenceRepository(database_path)

    saved = repository.save(make_payload())

    assert repository.list("client-a") == [saved]
    assert repository.list("client-b") == []


def test_evidence_update_and_delete_require_matching_client(tmp_path):
    database_path = tmp_path / "resume_demo.db"
    initialize_database(database_path)
    repository = EvidenceRepository(database_path)
    saved = repository.save(make_payload())

    updated = repository.save(
        make_payload(
            id=saved.id,
            title="Verified data quality coursework",
            outcome="Submitted a reproducible validation report",
        )
    )

    assert updated.id == saved.id
    assert updated.title == "Verified data quality coursework"
    assert repository.delete(saved.id, "client-b") is False
    assert repository.list("client-a") == [updated]
    assert repository.delete(saved.id, "client-a") is True
    assert repository.list("client-a") == []
