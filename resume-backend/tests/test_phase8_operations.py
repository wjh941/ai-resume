from __future__ import annotations

from pathlib import Path
import sqlite3
import subprocess
import zipfile


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKUP_SCRIPT = PROJECT_ROOT / "scripts" / "backup-database.ps1"


def test_windows_backup_script_creates_readable_sqlite_archive(tmp_path):
    database_path = tmp_path / "resume.db"
    backup_directory = tmp_path / "backups"
    with sqlite3.connect(database_path) as connection:
        connection.execute("CREATE TABLE sample (value TEXT NOT NULL)")
        connection.execute("INSERT INTO sample (value) VALUES ('preserved')")

    result = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(BACKUP_SCRIPT),
            "-DatabasePath",
            str(database_path),
            "-BackupDirectory",
            str(backup_directory),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    archive = next(backup_directory.glob("ai-resume-*.zip"))
    with zipfile.ZipFile(archive) as bundle:
        member = bundle.namelist()[0]
        restored = tmp_path / "restored.db"
        restored.write_bytes(bundle.read(member))
    with sqlite3.connect(restored) as connection:
        assert connection.execute("SELECT value FROM sample").fetchone()[0] == "preserved"
