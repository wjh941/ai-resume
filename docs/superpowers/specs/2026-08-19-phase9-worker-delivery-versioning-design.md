# Phase 9 Worker, Delivery, and Versioning Design

## Scope and invariants

Phase 9 keeps the H5 development server at `127.0.0.1:5186` and FastAPI at
`127.0.0.1:8000`. SQLite remains the default development database, while
`DATABASE_URL` continues to select PostgreSQL for production. Existing API
responses, paths, database columns, and business behavior remain valid; this
phase adds optional fields and new endpoints only.

All Phase9 user-facing frontend text, including titles, buttons, loading
states, empty states, and errors, is Simplified Chinese. Technical proper nouns
such as PDF, Word, JWT, SMS, OAuth, ZIP, APScheduler, PostgreSQL, and SQLite
remain unchanged. Code identifiers, logs, and source comments stay English.

## Worker infrastructure

`resume-backend/worker.py` is a separate APScheduler process and does not run
inside FastAPI. It loads the same Settings and database target as the web
server, schedules each task at `TASK_SCAN_INTERVAL_SECONDS`, and can execute a
single complete cycle for tests and operational diagnosis.

A `background_task_lock` table gives each named task a lease with an owner ID
and expiry. A task acquires the lease before work and releases it after work.
This avoids duplicate work when more than one worker container is started;
leases also recover from a crashed worker. The lock is advisory and must be
backed by a single shared database in multi-instance production deployments.

The worker runs three bounded tasks:

- enabled job-match subscriptions create one pending in-app alert per user and
  scan window; delivery is intentionally not attempted;
- expired export registrations and controlled temporary files are removed via
  the existing DownloadService;
- overdue pending orders are changed to `expired` using the established order
  expiry rule.

## Data and API additions

SQLite initialization receives additive migrations, and a new portable
Alembic revision contains the equivalent PostgreSQL-compatible schema. The
new application fields have defaults or are nullable: `contact_info`,
`attachment_ref`, `timeline_json`, and `next_interview_at`. Timeline records
are stored as validated JSON items on the application record, while
`interview_reminder` stores reminder time and status independently. New
application routes list or create timeline events and filter applications by
interview date. No delivery integration is performed for reminders.

`resume_version` stores immutable user-owned snapshots of an existing draft.
Snapshot, list, restore, activate, and shallow changed-field comparison APIs
operate only within the JWT user boundary. Restore copies the stored payload
back to the existing draft; it never deletes a draft. A document-import route
is a clear `501` skeleton and does not claim to parse PDF or Word files.

`career_task` attaches action items to a user and career-profile plan ID. The
API can create suggested tasks from existing 7/30/90-day action-plan data and
supports list, create, update, completion, and deletion. A task may
optionally reference an application or evidence ID without forcing either
record to exist.

## Frontend integration

The application page retains its existing save and local-pending-sync flow.
It gains optional contact and attachment fields, an interview date filter,
timeline entry/list view, reminder input, and an upcoming-interview calendar
section. The resume editor gains a compact version panel for snapshot,
restore, active version, and comparison preview. The career planner gains a
task checklist with due date and optional application/evidence links. New
service methods map only the additive endpoints and preserve existing types.

## Deployment and verification

The compose template adds a `worker` service built from the existing backend
image, configured through the same database environment and sharing controlled
temporary export storage. Environment examples document worker enablement,
interval, and lock lease settings. Deployment documentation explains that a
single worker is recommended unless all worker instances share the same
database and locks.

Tests cover lease behavior, each worker task, new repository/API operations,
and frontend mapping and state utilities. Verification includes the full
backend and frontend suites, H5 build, health/startup check using the current
worktree without terminating the user's existing process on port 8000, and
manual one-cycle worker execution against a disposable SQLite database.
