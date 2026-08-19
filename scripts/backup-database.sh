#!/usr/bin/env sh
set -eu

database_path=${DATABASE_PATH:-}
database_url=${DATABASE_URL:-}
backup_directory=${BACKUP_DIR:-}
retention_days=${BACKUP_RETENTION_DAYS:-14}

if [ "$retention_days" -lt 1 ]; then echo "BACKUP_RETENTION_DAYS must be at least 1." >&2; exit 2; fi
if [ -z "$backup_directory" ]; then
  if [ -z "$database_path" ]; then echo "Set BACKUP_DIR when backing up PostgreSQL." >&2; exit 2; fi
  backup_directory="$(dirname "$database_path")/backups"
fi
mkdir -p "$backup_directory"
timestamp=$(date -u +%Y%m%d-%H%M%S)

if [ -n "$database_url" ]; then
  command -v pg_dump >/dev/null 2>&1 || { echo "pg_dump is required for PostgreSQL backups." >&2; exit 2; }
  backup_path="$backup_directory/ai-resume-$timestamp.dump"
  pg_dump --dbname="$database_url" --format=custom --file="$backup_path"
else
  [ -n "$database_path" ] && [ -f "$database_path" ] || { echo "DATABASE_PATH must point to an existing SQLite database." >&2; exit 2; }
  snapshot_path="$backup_directory/ai-resume-$timestamp.db"
  backup_path="$backup_directory/ai-resume-$timestamp.db.gz"
  python3 - "$database_path" "$snapshot_path" <<'PY'
import sqlite3
import sys
source = sqlite3.connect(sys.argv[1])
target = sqlite3.connect(sys.argv[2])
source.backup(target)
target.close()
source.close()
PY
  gzip -c "$snapshot_path" > "$backup_path"
  rm -f "$snapshot_path"
fi

find "$backup_directory" -maxdepth 1 -type f -name 'ai-resume-*' -mtime "+$retention_days" -delete
# TODO: Register with cron or systemd only after a restore drill succeeds.
printf '%s\n' "$backup_path"
