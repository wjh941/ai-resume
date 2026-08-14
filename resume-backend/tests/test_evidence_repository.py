from app.db import initialize_database
from app.repositories.evidence import EvidenceRepository
from app.repositories.users import UserRepository
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
    users = UserRepository(database_path)
    owner_id = users.find_or_create_by_phone("13800138000").user_id
    other_id = users.find_or_create_by_phone("13900139000").user_id

    saved = repository.save(owner_id, make_payload())

    assert repository.list(owner_id) == [saved]
    assert repository.list(other_id) == []


def test_evidence_update_and_delete_require_matching_client(tmp_path):
    database_path = tmp_path / "resume_demo.db"
    initialize_database(database_path)
    repository = EvidenceRepository(database_path)
    users = UserRepository(database_path)
    owner_id = users.find_or_create_by_phone("13800138000").user_id
    other_id = users.find_or_create_by_phone("13900139000").user_id
    saved = repository.save(owner_id, make_payload())

    updated = repository.save(
        owner_id,
        make_payload(
            id=saved.id,
            title="Verified data quality coursework",
            outcome="Submitted a reproducible validation report",
        )
    )

    assert updated.id == saved.id
    assert updated.title == "Verified data quality coursework"
    assert repository.delete(other_id, saved.id) is False
    assert repository.list(owner_id) == [updated]
    assert repository.delete(owner_id, saved.id) is True
    assert repository.list(owner_id) == []
