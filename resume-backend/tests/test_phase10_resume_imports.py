from __future__ import annotations

from conftest import make_draft_payload


def _saved_draft(api_client) -> str:
    response = api_client.post("/api/draft/save", json=make_draft_payload())
    assert response.status_code == 200
    return response.json()["data"]["id"]


def test_pdf_upload_returns_mock_resume_preview(api_client) -> None:
    draft_id = _saved_draft(api_client)

    response = api_client.post(
        f"/api/draft/{draft_id}/imports",
        files={"file": ("resume.pdf", b"%PDF-1.4\n", "application/pdf")},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "parsed_mock"
    assert data["original_filename"] == "resume.pdf"
    assert data["parsed_resume"]["basic"]["name"] == ""
    assert data["parsed_resume"]["skills"] == {"skills": [], "certificates": []}
    assert "path" not in data


def test_upload_rejects_unsafe_type(api_client) -> None:
    draft_id = _saved_draft(api_client)

    response = api_client.post(
        f"/api/draft/{draft_id}/imports",
        files={"file": ("resume.exe", b"MZ", "application/octet-stream")},
    )

    assert response.status_code == 422
    assert response.json()["code"] == "validation_error"


def test_upload_rejects_file_larger_than_configured_limit(api_client) -> None:
    draft_id = _saved_draft(api_client)
    oversized = b"x" * (api_client.app.state.settings.resume_import_max_file_bytes + 1)

    response = api_client.post(
        f"/api/draft/{draft_id}/imports",
        files={"file": ("resume.docx", oversized, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
    )

    assert response.status_code == 422
    assert response.json()["code"] == "validation_error"
