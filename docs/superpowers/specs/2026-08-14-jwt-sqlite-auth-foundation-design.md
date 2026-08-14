# JWT SQLite Auth Foundation Design

## Scope

This transition adds authenticated, multi-user ownership to the existing
FastAPI and `premium-dashboard.html` application. SQLite remains the
development and transition database. Browser local storage and the offline
in-memory Mock renderer remain available for local preview, but are separated
by the authenticated user's identity. Payments, memberships, WeChat OAuth,
real SMS delivery, and cloud database migration are explicitly out of scope.

## Authentication

The public endpoints are `GET /health` and the four `/api/auth/*` endpoints:
`send-code`, `login-phone`, `wx-login`, and `logout`. Every other `/api/*`
route receives a shared `current_user_id` dependency which validates a Bearer
JWT before a repository is reached.

JWTs use HS256 and contain only `sub` (the immutable `user_id`),
`token_version`, and `exp`. `users.token_version` is checked for every
authenticated request. A normal logout carries the current Bearer token and
increments the version, invalidating all previously issued tokens immediately.
The public logout endpoint is intentionally idempotent when no token is sent;
it cannot invalidate a server session without a valid token and never accepts
a user identifier from the client.

`AUTH_DEMO_MODE=true` enables the explicit development-only code `123456`.
When disabled, no configured SMS provider is a configuration error. The SMS
service exposes Alibaba Cloud, Tencent Cloud, and generic HTTP gateway hooks,
but makes no real delivery request in this phase. The WeChat endpoint remains
an explicit configuration placeholder until app credentials and a HTTPS
callback domain are available.

## SQLite Ownership Migration

`users` stores `user_id`, a unique phone, `token_version`, creation time, and
last-login time. The user-owned draft, evidence, application, career profile,
assessment, and download records receive a nullable `user_id` foreign key and
user-oriented indexes. The nullable transition preserves historical rows
without assigning data from a shared machine to a new account.

`db.py` owns an idempotent migration based on `PRAGMA table_info`; an annotated
SQLite script documents the same upgrade for operators. Existing `client_id`
columns remain only for compatibility and must not be accepted as authorization
input. New application code derives the repository `user_id` exclusively from
the validated token. Every repository read, create, update, and delete method
accepts `user_id` explicitly and includes it in its SQL predicate.

## Frontend

An authentication utility owns the JWT-only global session key, safe claim
decoding, user-scoped cache keys, login/logout calls, and authenticated fetch.
The only unscoped persisted item is the JWT. Business cache keys use
`resume-dashboard:<user_id>:<key>`. Legacy unscoped keys remain untouched and
are never auto-imported, which avoids assigning a shared-device cache to the
wrong account.

The existing page header receives a small status area and the existing modal
system renders phone and WeChat tabs. A shared login guard protects all
business operations. The request wrapper adds the Bearer token, applies a
120-second timeout, clears invalid sessions on 401/403, and opens the login
modal. Only an authenticated user facing a network or AI availability error
can see their user-scoped in-memory/local preview fallback; authentication
failure never unlocks business actions.

## AI, Files, and Configuration

Production backend AI no longer has a mock provider. The OpenAI-compatible
client is selected by configuration and maps missing configuration, rate
limits, authentication errors, and insufficient balance to stable API error
codes. Tests inject a fake client at the application boundary instead of
shipping a production mock. The browser may still render its existing temporary
fallback after one of those errors.

Exports and download registrations are bound to `user_id`. A download token
can only be resolved by its owner; unauthorised resolution returns 404. Local
files remain the phase-one store and contain clearly marked OSS/COS extension
points. Configuration documents JWT, demo-auth, SMS, WeChat, AI, object-store,
and `CORS_ORIGINS` settings. The future database migration point is documented
without introducing SQLAlchemy or changing the SQLite runtime.

## Verification

Automated coverage validates public-route behavior, absent/tampered/expired
tokens, logout invalidation, two-user isolation for every mutable resource,
download ownership, demo-login configuration, and AI error mapping. Frontend
contract checks validate Bearer injection, 401 cleanup, login guards, and
user-scoped cache keys. Existing backend and dashboard checks continue to run.
