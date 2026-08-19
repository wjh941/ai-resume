# SQLite to PostgreSQL Migration

## Data type differences

Alembic uses portable SQL types for the Phase 8 baseline. IDs and timestamps
remain text values to preserve the existing API and SQLite data exactly.
SQLite stores booleans as integer affinity; PostgreSQL stores real booleans.
The two catalog insight tables use SQLite auto-increment integers and PostgreSQL
identity columns. JSON payloads remain text so no API serialization changes.

## Migration steps

1. Schedule downtime and stop all FastAPI writers.
2. Run a backup with `scripts/backup-database.ps1` or
   `scripts/backup-database.sh`; copy the generated archive off the host and
   test restoring it with SQLite.
3. Create an empty PostgreSQL database and set a private `DATABASE_URL`.
4. From `resume-backend`, install requirements and run
   `alembic -x database_url="$DATABASE_URL" upgrade head` after setting
   `DATABASE_URL` in the environment. The command must finish before the app
   is started.
5. Copy records into the empty migrated target:

   ```text
   python ../scripts/migrate_sqlite_to_postgres.py --sqlite-path ./data/resume_demo.db --database-url "$DATABASE_URL"
   ```

6. Start FastAPI with `DATABASE_URL` set, verify `/health`, sign in with a
   non-production account, open a draft, and create a non-production export.
7. Compare user, draft, career profile, application, favourite, and order
   counts before switching traffic. Keep the verified SQLite backup until the
   PostgreSQL deployment has passed its rollback window.

## Rollback

Stop writes, restore the verified SQLite backup to an isolated path, remove
`DATABASE_URL`, set `DATABASE_PATH` to that restored file, and start the prior
application version. Do not reverse-copy PostgreSQL data without a reviewed
incident plan.
