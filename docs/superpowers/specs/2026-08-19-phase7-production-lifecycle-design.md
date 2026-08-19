# Phase 7 Production Lifecycle Design

## Scope

Phase 7 activates production-safe authentication branches and completes the
local SQLite privacy, membership, and job-subscription lifecycles without
changing existing API paths or response fields.

## Decisions

- Development keeps the current mock SMS code (`123456`). Production sends a
  generated one-time code through an HTTPS JSON gateway configured entirely by
  environment variables. The provider was not specified, so the gateway
  contract is explicit rather than hard-coding an Alibaba or Tencent SDK.
- One-time codes are held only in process memory, hashed, single-use, and
  short-lived. Existing auth rate limiting stays in place; phone-specific
  throttling is added inside the SMS service.
- Existing `POST /api/account/data-export` remains JSON-compatible and returns
  a download URL. A new authenticated `GET /api/account/data-export` streams a
  ZIP archive containing user-owned JSON records.
- Account deletion invalidates tokens, anonymizes personally identifying resume
  and career fields, and soft-deletes the user. Membership orders remain as
  audit records but no longer expose a usable phone identity.
- Payment callbacks remain non-gateway calls. The callback verifies a
  configured HMAC payload for non-demo channels, is idempotent, and refuses
  expired pending orders. Real provider request/callback canonicalization is
  deliberately deferred.
- Job subscriptions gain a saved filter and last-notified timestamp; no worker,
  polling loop, external job source, or notification delivery is introduced.

## Compatibility

SQLite initialization adds columns with idempotent `ALTER TABLE` checks so old
project databases remain readable. Existing routes, fields, and mock payment
requests remain accepted. New response fields are additive.

## Verification

Backend tests cover development SMS login, the production SMS gateway branch,
soft deletion and ZIP export, subscription persistence, and idempotent/expired
orders. Frontend tests cover added service payload mappings. Smoke checks cover
mock login, production configuration rejection, deletion, and order status.
