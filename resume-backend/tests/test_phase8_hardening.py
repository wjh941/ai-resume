from __future__ import annotations

from datetime import datetime, timedelta, timezone
import os

from fastapi.testclient import TestClient
import pytest

from app.db import initialize_database
from app.services.downloads import DownloadService, ExportPathError


def test_production_hides_docs_rejects_unknown_origin_and_adds_security_headers(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "resume.db"))
    monkeypatch.setenv("TEMP_FILE_PATH", str(tmp_path / "exports"))
    monkeypatch.setenv("PRODUCTION", "true")
    monkeypatch.setenv("CORS_ORIGINS", "https://app.example.com")

    from main import create_app

    with TestClient(create_app()) as client:
        docs = client.get("/docs")
        rejected = client.get("/health", headers={"Origin": "https://unknown.example.com"})
        health = client.get("/health")

    assert docs.status_code == 404
    assert rejected.status_code == 403
    assert rejected.json()["code"] == "origin_forbidden"
    assert health.headers["x-content-type-options"] == "nosniff"
    assert health.headers["x-frame-options"] == "DENY"
    assert health.json()["data"]["database_type"] == "sqlite"


def test_download_registration_rejects_path_outside_export_directory(tmp_path):
    export_directory = tmp_path / "exports"
    export_directory.mkdir()
    outside_file = tmp_path / "outside.pdf"
    outside_file.write_bytes(b"not an export")
    service = DownloadService(tmp_path / "resume.db", export_directory, 60)

    with pytest.raises(ExportPathError):
        service.register("user-1", outside_file, "resume.pdf")


def test_cleanup_removes_expired_orphan_export_without_removing_unrelated_file(tmp_path):
    database_path = tmp_path / "resume.db"
    export_directory = tmp_path / "exports"
    export_directory.mkdir()
    initialize_database(database_path)
    orphan = export_directory / "orphan.pdf"
    unrelated = export_directory / "notes.txt"
    orphan.write_bytes(b"partial export")
    unrelated.write_text("keep me", encoding="utf-8")
    expired = (datetime.now(timezone.utc) - timedelta(minutes=61)).timestamp()
    os.utime(orphan, (expired, expired))
    os.utime(unrelated, (expired, expired))

    removed = DownloadService(database_path, export_directory, 60).cleanup_expired()

    assert removed == 1
    assert not orphan.exists()
    assert unrelated.exists()
