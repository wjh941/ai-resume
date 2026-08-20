# Public Deployment Readiness Phase 1 Design

## Goal

Make the application safer to run on a public VPS while keeping all third-party
integrations disabled or mocked. Add account-password login as a personal
deployment fallback without changing the existing phone-SMS or JWT contracts.

## Decisions

- Add a `password_account` table that maps a normalized account to a user ID,
  bcrypt password hash, creation time, and last-login time.
- Passwords are accepted as input only. The service validates 10-72 UTF-8
  bytes and hashes with `bcrypt.gensalt(rounds=PASSWORD_BCRYPT_ROUNDS)`.
- Existing `users.phone` remains non-null and unique. Password registration
  creates an ordinary user with an opaque generated `local:{uuid}` phone.
- Add `POST /api/auth/register-password` and `POST /api/auth/login-password`.
  Both return the existing token/user response plus optional account metadata.
- Keep phone-SMS routes unchanged. The global `/api/auth/*` rate limiter covers
  both new public endpoints.
- The H5 login page uses Chinese segmented tabs: “手机号验证码” and “账号密码”.
  The account tab offers registration and login in the current page.
- Public Compose sets `PRODUCTION=true`, `AUTH_DEMO_MODE=false`,
  `SMS_PROVIDER=disabled`, `PUSH_DISPATCHER_MODE=mock`, and
  `WEB_SEARCH_PROVIDER=disabled`.
- Backend health uses `/health`; worker health verifies its main process only,
  because the worker deliberately has no HTTP listener.

## Compatibility and Verification

The new schema is additive in SQLite initialization and an Alembic revision.
Phone authentication, existing JWT claims, and business endpoints remain
unchanged. Tests cover bcrypt registration/login, duplicate and invalid
credentials, SQLite/PostgreSQL-offline migrations, H5 auth requests, Compose
guardrails, full backend pytest, frontend unit tests, and H5 build.
