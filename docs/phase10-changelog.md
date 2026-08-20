# Phase 10 Changelog

## Implemented

- Added persistent user roles. New users default to `user`; a phone listed in
  `OPERATOR_PHONE_ALLOWLIST` is assigned `operator` during login. The role is
  carried in JWT and verified again by backend operator-only APIs.
- Added a lightweight operator knowledge-base surface with create, edit,
  offline, invalid-content marking, version history, and restore endpoints.
- Added the unified push-dispatch framework and persistent send logs. Mock mode
  is the development default; job subscription alerts, interview reminders,
  and order changes can create traceable dispatch records.
- Added protected PDF/Word resume upload, file type and size checks, private
  temporary storage, mock structured preview, and manual confirmation before
  applying parsed fields to a resume.
- Added structured backend application logging with request ID and user
  context, H5 global error recovery/reporting, and health hints for database,
  worker, and push-dispatch status.
- Added Phase10 Alembic/SQLite compatibility schema work and regression tests
  for RBAC, push logging, resume import, operator knowledge APIs, and runtime
  observability.
- Updated the H5 user-facing text touched in this phase to Simplified Chinese.

## Phase 1-10 Roadmap Summary

| Phase | Delivered focus |
| --- | --- |
| 1-4 | Resume editing, job guidance, export, local privacy and workflow foundations |
| 5 | Rate limiting, request IDs, backup/restore, loading and validation polish |
| 6 | Phone-login flow, account/privacy, favorites, subscriptions, membership UI skeletons |
| 7 | Configurable SMS path, privacy lifecycle, order state checks, favorites and subscriptions |
| 8 | PostgreSQL/Alembic readiness, production hardening, backups and Compose deployment |
| 9 | APScheduler worker, delivery timeline, resume versions and career tasks |
| 10 | Push dispatch framework, resume-import preview, operator RBAC, observability and final launch guidance |

## Deferred

- Real WeChat subscription-message and SMS provider HTTP calls remain TODO;
  `PUSH_DISPATCHER_MODE=real` deliberately does not send messages yet.
- PDF/Word parsing and malware scanning are interfaces only. The backend returns
  a mock preview and requires user confirmation before applying any fields.
- Real-world job-source synchronization, crawlers, and scheduled notification
  delivery remain out of scope.
- Team collaboration, mentor comments, shared resumes, and a full admin system
  remain future roadmap work.
