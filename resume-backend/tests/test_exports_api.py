from __future__ import annotations

from datetime import datetime, timedelta, timezone
import sqlite3

import pytest
from fastapi.testclient import TestClient
from docx import Document

from conftest import make_draft_payload
from app.services.export_pdf import PdfRendererUnavailableError, chromium_is_available


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


def test_word_export_respects_section_visibility(api_client):
    payload = make_draft_payload()
    payload["resume"]["section_visibility"]["basic"] = False
    payload["resume"]["section_visibility"]["employment"] = False
    draft = api_client.post("/api/draft/save", json=payload).json()["data"]
    export = api_client.post(
        "/api/export/word",
        json={"client_id": "demo-client", "draft_id": draft["id"]},
    ).json()["data"]
    token = export["download_url"].rsplit("/", 1)[-1]

    with sqlite3.connect(api_client.app.state.settings.database_path) as connection:
        output_path = connection.execute(
            "SELECT file_path FROM download_file WHERE token = ?",
            (token,),
        ).fetchone()[0]
    text = "\n".join(paragraph.text for paragraph in Document(output_path).paragraphs)

    assert "Zhang San" not in text
    assert "实习/工作经历" not in text


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


def test_export_rejects_malformed_draft_id(api_client):
    response = api_client.post(
        "/api/export/word",
        json={"draft_id": "../not-a-draft"},
    )

    assert response.status_code == 422
    assert response.json()["code"] == "validation_error"


def test_export_rejects_resume_without_visible_content(api_client):
    payload = make_draft_payload()
    payload["resume"].update(
        {
            "basic": {"name": "", "phone": "", "email": "", "city": ""},
            "job": {"target_role": "", "employment_type": "", "expected_salary": ""},
            "education": [],
            "employment": [],
            "projects": [],
            "skills": {"skills": [], "certificates": []},
            "self_evaluation": "",
        }
    )
    draft = api_client.post("/api/draft/save", json=payload).json()["data"]

    response = api_client.post("/api/export/word", json={"draft_id": draft["id"]})

    assert response.status_code == 422
    assert response.json()["code"] == "export_empty"


def test_export_accepts_visible_partial_entry_when_identity_sections_are_hidden(api_client):
    payload = make_draft_payload()
    payload["resume"]["section_visibility"].update({"basic": False, "job": False})
    payload["resume"]["education"] = [
        {"school": "", "major": "Computer Science", "degree": "", "start_date": "", "end_date": ""}
    ]
    payload["resume"]["employment"] = []
    payload["resume"]["projects"] = []
    payload["resume"]["skills"] = {"skills": [], "certificates": []}
    payload["resume"]["self_evaluation"] = ""
    draft = api_client.post("/api/draft/save", json=payload).json()["data"]

    response = api_client.post("/api/export/word", json={"draft_id": draft["id"]})

    assert response.status_code == 200


def test_pdf_renderer_failure_removes_partial_output_and_returns_export_error(api_client, monkeypatch, caplog):
    draft = save_draft(api_client)

    async def partial_pdf(*_args, **kwargs):
        output_path = kwargs.get("output_path", _args[2])
        output_path.write_bytes(b"partial")
        raise PdfRendererUnavailableError("renderer unavailable")

    monkeypatch.setattr("app.api.exports.render_pdf_resume", partial_pdf)

    with TestClient(api_client.app, raise_server_exceptions=False) as client:
        client.headers.update(api_client.headers)
        response = client.post("/api/export/pdf", json={"draft_id": draft["id"]})

    assert response.status_code == 503
    assert response.json()["code"] == "export_error"
    assert not list(api_client.app.state.settings.temp_file_path.glob("*.pdf"))
    assert "export error" in caplog.text.lower()


def test_download_rejects_tampered_path_outside_export_storage(api_client, tmp_path):
    draft = save_draft(api_client)
    export = api_client.post("/api/export/word", json={"draft_id": draft["id"]}).json()["data"]
    token = export["download_url"].rsplit("/", 1)[-1]
    outside_file = tmp_path / "outside.docx"
    outside_file.write_bytes(b"must-not-be-served")

    with sqlite3.connect(api_client.app.state.settings.database_path) as connection:
        connection.execute(
            "UPDATE download_file SET file_path = ? WHERE token = ?",
            (str(outside_file), token),
        )

    response = api_client.get(export["download_url"])

    assert response.status_code == 404
    assert outside_file.exists()


def test_export_file_failure_returns_standard_error(api_client, monkeypatch, caplog):
    draft = save_draft(api_client)
    monkeypatch.setattr(
        "app.api.exports.render_word_resume",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("disk full")),
    )

    with TestClient(api_client.app, raise_server_exceptions=False) as client:
        client.headers.update(api_client.headers)
        response = client.post("/api/export/word", json={"draft_id": draft["id"]})

    assert response.status_code == 503
    assert response.json()["code"] == "export_error"
    assert "export error" in caplog.text.lower()


def test_database_error_returns_standard_error(api_client, monkeypatch, caplog):
    monkeypatch.setattr(
        api_client.app.state.draft_repository,
        "get",
        lambda *_args: (_ for _ in ()).throw(sqlite3.DatabaseError("locked")),
    )

    with TestClient(api_client.app, raise_server_exceptions=False) as client:
        client.headers.update(api_client.headers)
        response = client.post("/api/export/word", json={"draft_id": "0" * 32})

    assert response.status_code == 503
    assert response.json()["code"] == "database_error"
    assert "database error" in caplog.text.lower()


def test_unexpected_export_error_returns_standard_error(api_client, monkeypatch, caplog):
    monkeypatch.setattr(
        api_client.app.state.draft_repository,
        "get",
        lambda *_args: (_ for _ in ()).throw(RuntimeError("unexpected")),
    )

    with TestClient(api_client.app, raise_server_exceptions=False) as client:
        client.headers.update(api_client.headers)
        response = client.post("/api/export/word", json={"draft_id": "0" * 32})

    assert response.status_code == 500
    assert response.json()["code"] == "internal_error"
    assert "unexpected error" in caplog.text.lower()
