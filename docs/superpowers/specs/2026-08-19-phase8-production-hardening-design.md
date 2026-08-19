# Phase 8 Production Hardening Design

## Scope and invariants

Phase 8 preserves the current API envelopes, repository-facing business
methods, SQLite development default, and development topology: the H5 server
uses `127.0.0.1:5186` and proxies to FastAPI at `127.0.0.1:8000`.

`DATABASE_URL` selects PostgreSQL for a production deployment. `DATABASE_PATH`
remains the SQLite default when no URL is supplied. SQLite migration history is
retained for existing development databases; new portable Alembic revisions
are the schema authority for fresh SQLite and PostgreSQL deployments.

## Database approach

The existing repositories use the small `connect(...).execute(...)` contract.
Replacing every repository with an ORM would create unnecessary behavioral
risk. A database connection adapter therefore preserves that contract:

- SQLite continues using `sqlite3` and its existing initialization path.
- PostgreSQL uses `psycopg`, maps positional parameters to PostgreSQL syntax,
  and translates the few shared SQLite-only statements used by repositories.
- Alembic owns a portable baseline schema and runs with either a SQLite URL or
  a PostgreSQL URL. Production deployment runs `alembic upgrade head` before
  starting FastAPI; the app does not silently mutate a PostgreSQL schema.
- A dedicated SQLite-to-PostgreSQL copy utility moves tables in dependency
  order, preserves IDs and JSON payloads, converts boolean fields, and resets
  PostgreSQL sequences.

## Hardening approach

`PRODUCTION=true` enables production behavior independently of legacy
`APP_ENV`: OpenAPI/docs routes are unavailable, unknown browser origins are
rejected, debug output is disabled, and every response gains conservative
security headers. Health data reports only database type, readiness, backup
guidance, and configuration booleans; secrets and connection strings are never
returned.

Export registration accepts only files under `TEMP_FILE_PATH`; existing token
resolution and TTL cleanup remain in place and are extended to clean orphaned
generated files under that same controlled directory.

## Deployment and UX

The compose template runs PostgreSQL, FastAPI, and an HTTP-only static H5
frontend. The frontend proxy forwards `/api` and `/downloads` to FastAPI.
TLS remains the responsibility of an external Nginx or Caddy reverse proxy.

Frontend request handling maps known production configuration failures for SMS,
WeChat OAuth, and payment into short actionable messages. Existing page flows
and server error redaction remain unchanged.

## Verification

Backend tests cover production docs/CORS/security headers, health summaries,
export path ownership and cleanup, settings selection, and portable Alembic
SQLite upgrades. PostgreSQL compatibility is verified by generating offline
Alembic PostgreSQL SQL because this workstation has no Docker or PostgreSQL
service. The backup scripts are exercised against a disposable SQLite database.
Full backend and frontend suites plus the H5 production build remain required.
