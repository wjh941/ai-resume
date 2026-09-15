# Phase 9 Changelog

## Implemented

- Added a standalone APScheduler worker entry point with database-backed task
  leases. The web process stays independent from scheduled maintenance.
- Added worker jobs for in-app pending job-match alerts, temporary export
  cleanup, and automatic expiry of unpaid membership orders.
- Added compatible application fields for contact information, attachment
  references, timeline events, upcoming interview time, and reminder records.
- Added owned resume-version snapshots with notes, restore, and structured
  comparison data. The active draft contract remains unchanged.
- Added user-owned career tasks with generated 7/30/90-day actions, CRUD, due
  dates, completion state, and optional application/evidence references.
- Added H5 surfaces for application timelines and interview schedules, resume
  versions, and career task checklists. All new visible user-facing text is
  Simplified Chinese.
- Added Phase 9 SQLite schema initialization, a portable Alembic migration,
  worker configuration examples, Compose worker service, and deployment notes.

## Deferred

- Job subscription notifications are stored for later delivery only; no SMS,
  WeChat subscription message, or other push gateway is invoked.
- PDF and Word resume parsing remain a placeholder interface. Users continue
  to enter resume content manually.
- Multi-worker monitoring, distributed scheduling, and alert delivery
  observability require later production operations work.
- Admin functions, team collaboration, application calendar reminders, and
  external job-source synchronization remain outside Phase 9.
