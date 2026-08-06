from __future__ import annotations

from datetime import datetime, timedelta, timezone
import sqlite3

import pytest

from conftest import make_draft_payload
from app.services.export_pdf import chromium_is_available


def save_draft(api_client) -> dict:
    response = api_client.post("/api/draft/save", json=make_draft_payload())
    assert response.status_code == 200
    return response.json()["data"]


def test_word_export_returns_safe_filename_and_download(api_client):
    draft = save_draft(api_client)

    response = api_client.post(
        "/api/export/word",
        json={"client_id": "demo-client", "draft_id": draft["id"]},
    )

    assert response.status_code == 200
    export = response.json()["data"]
    assert export["filename"] == "Zhang San-Data Engineer-简历.docx"
    assert export["download_url"].startswith("/downloads/")
    assert datetime.fromisoformat(export["expires_at"]).tzinfo is not None

    download = api_client.get(export["download_url"])
    assert download.status_code == 200
    assert len(download.content) > 0


def test_expired_download_returns_not_found(api_client):
    draft = save_draft(api_client)
    export = api_client.post(
        "/api/export/word",
        json={"client_id": "demo-client", "draft_id": draft["id"]},
    ).json()["data"]
    token = export["download_url"].rsplit("/", 1)[-1]

    with sqlite3.connect(api_client.app.state.settings.database_path) as connection:
        connection.execute(
            "UPDATE download_file SET expires_at = ? WHERE token = ?",
            ((datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat(), token),
        )

    response = api_client.get(export["download_url"])

    assert response.status_code == 404
    assert response.json()["code"] == "not_found"


def test_pdf_export_returns_download_when_chromium_is_available(api_client):
    if not chromium_is_available(api_client.app.state.settings.playwright_browsers_path):
        pytest.skip("Chromium is not installed at configured PLAYWRIGHT_BROWSERS_PATH")
    draft = save_draft(api_client)

    response = api_client.post(
        "/api/export/pdf",
        json={"client_id": "demo-client", "draft_id": draft["id"]},
    )

    assert response.status_code == 200
    export = response.json()["data"]
    assert export["filename"] == "Zhang San-Data Engineer-简历.pdf"
    download = api_client.get(export["download_url"])
    assert download.status_code == 200
    assert download.content.startswith(b"%PDF")
