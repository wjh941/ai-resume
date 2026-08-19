# Phase 6 Changelog

## Completed

- Added phone-number and mock verification-code login for local development.
- Persisted the JWT session on the miniprogram client and attach a Bearer token
  to protected API calls.
- Added a single re-login prompt for expired or revoked tokens and a logout
  action that clears the local session.
- Added an Account page with current-user details and privacy data-scope,
  export-request, and deletion-request controls.
- Added protected placeholder APIs for account data scope, data export, and
  account deletion requests. They acknowledge requests only and do not delete
  user data.
- Added user-scoped favourite-job and match-subscription tables plus protected
  API skeletons.
- Added Favourite Jobs, Membership, and Orders pages. Membership checkout uses
  the existing demo payment callback only.
- Added focused tests for JWT login/session behaviour, token revocation,
  account lifecycle acknowledgements, job collections, and frontend API
  adapters.

## Local development topology

The H5/miniprogram development server remains at `http://127.0.0.1:5186` and
proxies API calls to the FastAPI backend at `http://127.0.0.1:8000`. This keeps
the existing port assignment intact while allowing the client to call `/api/*`
without a cross-origin configuration change.

## Deferred TODOs

- Replace mock SMS verification with a real, rate-limited SMS provider only
  after provider credentials and abuse controls are approved.
- Do not add WeChat OAuth in this phase.
- Implement reviewed, auditable account export and deletion workflows; no real
  deletion is performed yet.
- Connect job subscriptions to an approved external job source and notification
  provider; no external polling or alert delivery is enabled.
- Integrate a real payment provider and validate signed callbacks; demo payment
  remains intentionally local.
- Leave MySQL/PostgreSQL migration, deployment operations, delivery reminders,
  resume-version management, administration, and team collaboration to later
  phases.
