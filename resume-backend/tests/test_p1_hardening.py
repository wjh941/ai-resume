from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.config import load_settings
from app.db import connect
from app.services.worker import BackgroundWorker


def _draft_payload() -> dict:
    return {
        "job_title": "Data Engineer",
        "template_id": "technology",
        "resume": {
            "version": 1,
            "basic": {"name": "Zhang San", "phone": "13800138000", "email": "z@example.com", "city": "Beijing"},
            "job": {"target_role": "Data Engineer", "employment_type": "full_time", "expected_salary": "20k"},
            "education": [{"school": "Example University", "major": "CS", "degree": "Bachelor", "start_date": "2018", "end_date": "2022"}],
            "employment": [],
            "projects": [],
            "skills": {"skills": ["Python"], "certificates": []},
            "self_evaluation": "Reliable",
            "section_visibility": {"basic": True, "job": True, "education": True, "employment": True, "projects": True, "skills": True, "self_evaluation": True},
        },
    }


def test_draft_round_trip_preserves_education_courses(api_client) -> None:
    payload = _draft_payload()
    payload["resume"]["education"][0]["courses"] = "Distributed Systems, SQL"

    saved = api_client.post("/api/draft/save", json=payload)
    assert saved.status_code == 200
    draft_id = saved.json()["data"]["id"]

    loaded = api_client.get(f"/api/draft/{draft_id}")
    assert loaded.status_code == 200
    assert loaded.json()["data"]["resume"]["education"][0]["courses"] == "Distributed Systems, SQL"


def test_production_rejects_default_jwt_secret(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("PRODUCTION", "true")
    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.delenv("JWT_SECRET", raising=False)
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "resume.db"))

    with pytest.raises(ValueError, match="JWT_SECRET"):
        load_settings()


def test_worker_cleans_expired_resume_import_files(api_client, monkeypatch) -> None:
    monkeypatch.setenv("RESUME_IMPORT_EXPIRE_MINUTES", "60")

    draft_id = api_client.post("/api/draft/save", json=_draft_payload()).json()["data"]["id"]
    database_path = api_client.app.state.settings.database_path
    import_dir = api_client.app.state.settings.temp_file_path / "resume-imports"
    import_dir.mkdir(parents=True)
    expired_file = import_dir / "expired.pdf"
    expired_file.write_bytes(b"expired")
    created_at = (datetime.now(timezone.utc) - timedelta(minutes=61)).isoformat()
    with connect(database_path) as connection:
        connection.execute(
            """
            INSERT INTO resume_import
            (id, user_id, draft_id, stored_filename, original_filename, content_type,
             byte_size, status, parsed_resume_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "import-expired",
                api_client.app.state.auth_service.verify(api_client.headers["Authorization"].split(" ", 1)[1]),
                draft_id,
                expired_file.name,
                "resume.pdf",
                "application/pdf",
                7,
                "parsed_mock",
                "{}",
                created_at,
            ),
        )

    settings = load_settings()
    worker = BackgroundWorker.from_settings(settings, owner_id="cleanup-test")
    result = worker.run_all_once()

    assert result["expired_resume_imports"] == 1
    assert not expired_file.exists()
    with connect(database_path) as connection:
        assert connection.execute(
            "SELECT 1 FROM resume_import WHERE id = ?", ("import-expired",)
        ).fetchone() is None
