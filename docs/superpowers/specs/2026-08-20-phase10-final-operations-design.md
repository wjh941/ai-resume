# Phase 10 Final Operations Design

## Scope and Compatibility

Phase 10 extends the Phase 9 application without changing current URLs,
request fields, database columns, or the H5 `5186` / FastAPI `8000` port
contract. New behavior is additive. SQLite remains the development default and
the existing PostgreSQL compatibility adapter remains the production path.

Every new or changed visible H5 string is Simplified Chinese. PDF, Word, JWT,
SMS, OAuth, ZIP, APScheduler, PostgreSQL, and SQLite remain technical proper
nouns. Source identifiers, logs, and comments remain English.

## Authorization and Operator Access

`users.role` is added with `user` as its default. `OPERATOR_PHONE_ALLOWLIST`
is a comma-separated bootstrap source. Phone login synchronizes a matching
user to `operator` and a non-matching user to `user`; this makes allowlist
removal take effect at the next login.

JWTs gain a signed `role` claim. Verification loads the current user, checks
token version and role consistency, and returns an authenticated principal.
Existing endpoints retain their user-id dependency. New operator endpoints use
an additional `require_operator` dependency and reject non-operator tokens
with 403. The H5 session stores the role solely to show an operator entry; it
never authorizes a request without backend verification.

## Push Dispatcher

`PushDispatcher` owns event dispatch and `push_send_log` persists every
attempt with user, event, target, dispatcher mode, status, payload summary,
and error context. `PUSH_DISPATCHER_MODE=mock` is the default and records
successful simulated WeChat subscription-message and SMS sends. `real` keeps
the same contract but records a skipped, configuration-oriented result because
no third-party HTTP call is enabled in this release.

The worker dispatches newly created job-subscription alerts, due interview
reminders, and newly expired unpaid orders. A source reference plus prior-log
lookup makes repeated worker cycles idempotent. Push provider credentials are
environment-only configuration; the WeChat and SMS provider call sites are
explicitly deferred for a future provider integration.

## Resume Import

`POST /api/draft/{draft_id}/imports` accepts PDF, DOC, and DOCX only. It
streams the file into a generated directory below `TEMP_FILE_PATH`, accepts a
bounded configured size, validates extension and content type, and never uses
the user-supplied filename as a filesystem path. A virus-scanning integration
is an explicit production prerequisite outside this release.

`resume_import` stores safe metadata, status, and a JSON mock parsing result.
No actual PDF or Word parser is invoked. The response presents a safe empty
resume structure that the H5 editor lets the user change before applying to
the local draft and saving through the existing draft API.

## Operator Knowledge Base

The existing public knowledge APIs remain compatible. A separate
`/api/operator/knowledge-items` group manages a lightweight `knowledge_item`
table and immutable `knowledge_item_version` history. Operators can create,
edit, set active/offline/invalid state, list history, and restore an earlier
version by creating a new current version. The H5 operator page uses existing
controls and is only reachable from the role-aware account entry; the backend
remains the authorization boundary.

## Observability and Error Handling

`LOG_LEVEL` controls structured application logging. Middleware assigns a
request ID, principal dependencies attach a user ID when known, and exception
handlers log method, path, status, request ID, user ID, and exception type.
Responses remain sanitized. A small authenticated-or-anonymous client-error
endpoint writes sanitized H5 failure context to the structured backend log.

The global H5 Vue error handler reports sanitized context and routes to a
Chinese recovery page rather than rendering raw errors. The health response
keeps existing fields and adds push-dispatcher mode plus a worker heartbeat
derived from persisted worker task runs.

## Schema and Migration

The Phase 10 Alembic revision adds `users.role`, `push_send_log`,
`resume_import`, `knowledge_item`, `knowledge_item_version`, and
`background_task_run`. SQLite initialization creates the same additive schema
and migration helpers upgrade existing local databases. No destructive
migration or table rewrite is required.

## Verification

Backend tests cover role synchronization and RBAC denial, push mock logging,
file validation and parse preview, operator item version restore, structured
error logging, and health metrics. H5 tests cover role-aware session handling,
new service mappings, import preview application, and error recovery. Final
verification runs the full backend and frontend suites, the H5 build, a
temporary-port current-worktree health smoke, and an explicit read-through of
the deployment checklist. Docker Compose validation is run only when Docker is
installed; it is not required for local development tests.

## Deferred Roadmap

Real WeChat subscription-message and SMS calls, PDF/Word extraction, shared
team review, mentor comments, external job crawling, and a full admin system
remain outside Phase 10.
