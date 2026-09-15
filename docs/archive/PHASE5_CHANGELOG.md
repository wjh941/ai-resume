# Phase5 Changelog

## Backend Reliability

- Added process-local rate limiting for public `POST /api/auth/*` endpoints. Limits are configurable with `AUTH_RATE_LIMIT_MAX_REQUESTS` and `AUTH_RATE_LIMIT_WINDOW_SECONDS`.
- Added an opaque `X-Request-ID` response header to support runtime troubleshooting without changing the existing JSON API envelope.
- Enabled SQLite WAL mode and a configurable short busy timeout (`SQLITE_TIMEOUT_SECONDS`) for more resilient concurrent writes.
- Preserved disk-backed DOCX/PDF exports and FastAPI `FileResponse` range support, so downloads remain streamed instead of being loaded into application memory.
- Documented SQLite, export-storage, and auth-rate-limit configuration in `resume-backend/.env.example`.

## Frontend Experience

- Added local resume and career-planning backup/restore as a versioned JSON file from Local privacy. Restore requires confirmation and does not affect server records.
- Added page-level inline resume validation feedback, safe end-user error normalization, and loading skeletons for role-driven resume generation, career-plan computation, and document export.
- Coalesced rapid career-tier selection updates to avoid unnecessary repeated recommendation rendering.
- Added lightweight empty states for an empty resume editor and empty draft history.
- Unified shared card, control, shadow, hover, and typography tokens without changing page workflows or API use.

## Compatibility

- No API endpoint, response envelope, database table, or migration behavior was removed or renamed.
- Existing local checkpoints and project data remain valid; local backups use a new versioned file format.

## Verification

- Backend full suite: `130 passed, 1 skipped`.
- Frontend full suite: `54 passed`.
- H5 production build completed successfully.
- Smoke coverage: authenticated resume draft creation, career-plan generation, Word export, unauthenticated export rejection, auth rate limiting, and local backup restore state.
