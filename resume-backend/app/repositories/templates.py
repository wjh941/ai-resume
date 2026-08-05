from __future__ import annotations

import json
from pathlib import Path

from app.db import connect


class TemplateRepository:
    def __init__(self, database_path: Path):
        self.database_path = database_path

    def list_active(self) -> list[dict]:
        with connect(self.database_path) as connection:
            rows = connection.execute(
                "SELECT * FROM template_table WHERE active = 1 ORDER BY rowid"
            ).fetchall()
        return [
            {
                "id": row["id"],
                "name": row["name"],
                "description": row["description"],
                "config": json.loads(row["config_json"]),
                "docx_template_path": row["docx_template_path"],
            }
            for row in rows
        ]
