from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.db import connect
from app.schemas.evidence import ResumeEvidence, ResumeEvidenceSaveRequest


class EvidenceRepository:
    def __init__(self, database_path: Path) -> None:
        self._database_path = database_path

    def list(self, client_id: str) -> list[ResumeEvidence]:
        with connect(self._database_path) as connection:
            rows = connection.execute(
                """
                SELECT id, client_id, kind, title, context, actions, outcome, proof_note,
                       verified, created_at, updated_at
                FROM resume_evidence
                WHERE client_id = ?
                ORDER BY updated_at DESC, id DESC
                """,
                (client_id,),
            ).fetchall()
        return [self._from_row(row) for row in rows]

    def save(self, payload: ResumeEvidenceSaveRequest) -> ResumeEvidence:
        evidence_id = payload.id or str(uuid4())
        now = datetime.now(timezone.utc).isoformat()
        with connect(self._database_path) as connection:
            if payload.id:
                cursor = connection.execute(
                    """
                    UPDATE resume_evidence
                    SET kind = ?, title = ?, context = ?, actions = ?, outcome = ?,
                        proof_note = ?, verified = ?, updated_at = ?
                    WHERE id = ? AND client_id = ?
                    """,
                    (
                        payload.kind,
                        payload.title,
                        payload.context,
                        payload.actions,
                        payload.outcome,
                        payload.proof_note,
                        int(payload.verified),
                        now,
                        evidence_id,
                        payload.client_id,
                    ),
                )
                if cursor.rowcount == 0:
                    raise KeyError(evidence_id)
            else:
                connection.execute(
                    """
                    INSERT INTO resume_evidence (
                        id, client_id, kind, title, context, actions, outcome, proof_note,
                        verified, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        evidence_id,
                        payload.client_id,
                        payload.kind,
                        payload.title,
                        payload.context,
                        payload.actions,
                        payload.outcome,
                        payload.proof_note,
                        int(payload.verified),
                        now,
                        now,
                    ),
                )
            row = connection.execute(
                """
                SELECT id, client_id, kind, title, context, actions, outcome, proof_note,
                       verified, created_at, updated_at
                FROM resume_evidence
                WHERE id = ? AND client_id = ?
                """,
                (evidence_id, payload.client_id),
            ).fetchone()
        if row is None:
            raise KeyError(evidence_id)
        return self._from_row(row)

    def delete(self, evidence_id: str, client_id: str) -> bool:
        with connect(self._database_path) as connection:
            cursor = connection.execute(
                "DELETE FROM resume_evidence WHERE id = ? AND client_id = ?",
                (evidence_id, client_id),
            )
        return cursor.rowcount > 0

    @staticmethod
    def _from_row(row) -> ResumeEvidence:
        return ResumeEvidence(
            id=str(row["id"]),
            client_id=str(row["client_id"]),
            kind=str(row["kind"]),
            title=str(row["title"]),
            context=str(row["context"]),
            actions=str(row["actions"]),
            outcome=str(row["outcome"]),
            proof_note=str(row["proof_note"]),
            verified=bool(row["verified"]),
            created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"]),
        )
