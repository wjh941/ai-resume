# Phase 8 Changelog

## Implemented

- Added portable Alembic baseline migrations for fresh SQLite and PostgreSQL
  databases. SQLite remains the default; `DATABASE_URL` selects PostgreSQL.
- Added a PostgreSQL connection adapter that preserves existing repository
  query contracts and seeds the current catalog after a migrated startup.
- Added SQLite-to-PostgreSQL migration guidance and a guarded copy utility.
- Added production mode hardening through `PRODUCTION=true`: disabled docs and
  OpenAPI, strict origin rejection, sanitized error behavior, and security
  response headers.
- Extended health responses with database type, backup guidance, and masked
  critical-configuration status only.
- Restricted generated download registration to `TEMP_FILE_PATH` and added TTL
  cleanup for expired registered and orphaned docx/pdf/xlsx/zip exports.
- Added Windows and Linux backup scripts with compressed SQLite backups,
  PostgreSQL custom dumps, retention, and scheduler-registration comments.
- Added an HTTP-only PostgreSQL/FastAPI/static-H5 Docker Compose template.
  HTTPS must be terminated by an external Nginx or Caddy reverse proxy.
- Added short frontend guidance for missing SMS, WeChat OAuth, payment, and
  export storage configuration without exposing backend details.

## Deferred

- PostgreSQL backup automation, monitoring, and restore alerts beyond the
  supplied manual scripts.
- Provider-specific WeChat OAuth code exchange and payment callback handling.
- Shared distributed rate-limit/code storage for multi-instance deployments.
- Scheduled job-alert workers and external job-source synchronization.
- Application reminders, resume version management, admin functions, and team
  collaboration remain later-phase work.
