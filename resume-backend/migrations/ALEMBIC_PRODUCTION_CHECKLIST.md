# Production Database Migration Checklist

This backend currently uses versioned, idempotent SQLite SQL migrations in this directory. If the deployment is managed with Alembic, treat the matching Alembic revision as the execution mechanism and keep this checklist as the production gate.

## Before Any Migration

1. Schedule a maintenance window and stop application writes.
2. **Back up the production database before running any migration.** For SQLite, copy the database with `sqlite3 <database> ".backup '<backup-path>'"` or use the platform's consistent snapshot procedure.
3. Back up the export storage directory separately. Database rollback does not restore generated files.
4. Verify the database backup: open it with SQLite, run `PRAGMA integrity_check;`, and retain the command output with the deployment record.
5. Record the running application version, database path, current migration/revision, and backup locations.

## Apply

1. Confirm the target revision or SQL file is reviewed and contains no `DROP TABLE`, destructive rebuild, or user-data rewrite.
2. Run `alembic upgrade <target-revision>` when Alembic controls the deployment, or apply the reviewed idempotent SQL through the approved SQLite migration process.
3. Start the application against the migrated copy/database.
4. Call `GET /health/detail` and verify `database.status` is `connected` and `storage.status` is `ready`.
5. Run a read-only draft query and a non-production export smoke test with an authorized account.

## Rollback

1. Stop application writes again.
2. Restore the verified pre-migration database backup; do not attempt an unreviewed manual reverse migration in production.
3. Restore export storage only when the incident requires it.
4. Restart the prior application version and confirm `/health/detail` before reopening traffic.

## Phase4 Scope

Phase4 adds no table, column, index, or destructive data migration. The application guards and health diagnostics are source-only changes; existing database tables and API success payloads remain compatible.
