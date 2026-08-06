from datetime import datetime, timedelta, timezone
import sqlite3

from app.db import initialize_database
from app.schemas.job import JobIntelligence
from app.services.job_cache import JobCache


def assert_success(response):
    assert response.status_code == 200
    assert response.json()["code"] == "ok"
    assert response.json()["message"] == ""
    return response.json()["data"]


def test_same_normalized_role_uses_unexpired_mock_cache(api_client):
    first = assert_success(api_client.post("/api/job/query", json={"role_name": " Data Engineer "}))
    second = assert_success(api_client.post("/api/job/query", json={"role_name": "data   engineer"}))

    assert first == second
    assert api_client.app.state.ai_client.job_query_count == 1


def test_expired_job_cache_refreshes_role_intelligence(api_client):
    assert_success(api_client.post("/api/job/query", json={"role_name": "Data Engineer"}))
    with sqlite3.connect(api_client.app.state.settings.database_path) as connection:
        connection.execute(
            """
            UPDATE job_cache
            SET expires_at = ?
            WHERE normalized_role = ? AND provider_mode = ?
            """,
            ((datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat(), "data engineer", "mock"),
        )

    assert_success(api_client.post("/api/job/query", json={"role_name": "Data Engineer"}))
    assert api_client.app.state.ai_client.job_query_count == 2


def test_blank_role_name_returns_validation_error(api_client):
    response = api_client.post("/api/job/query", json={"role_name": "   "})

    assert response.status_code == 422
    assert response.json()["code"] == "validation_error"


def test_job_cache_migrates_legacy_single_provider_primary_key(tmp_path):
    database_path = tmp_path / "legacy.db"
    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            CREATE TABLE job_cache (
                normalized_role TEXT PRIMARY KEY,
                provider_mode TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )

    initialize_database(database_path)
    cache = JobCache(database_path, expire_days=7)
    job = JobIntelligence(role_name="Data Engineer")
    cache.put("Data Engineer", "mock", job)
    cache.put("Data Engineer", "ark", job)

    assert cache.get("Data Engineer", "mock") is not None
    assert cache.get("Data Engineer", "ark") is not None
