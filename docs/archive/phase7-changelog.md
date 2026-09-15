# Phase 7 Changelog

## Implemented

- Development phone login still uses mock code `123456`; production mode now
  issues single-use, hashed, expiring codes through an environment-configured
  HTTPS SMS gateway.
- Added explicit SMS credentials, signature/template metadata, code TTL, and
  cooldown configuration. Existing in-memory auth rate limiting remains active.
- Added a WeChat login button and a configured callback placeholder that states
  the HTTPS redirect-domain requirement.
- Added SQLite user lifecycle fields: `is_deleted`, `deleted_at`, and
  `privacy_consent_at`.
- Added a protected ZIP JSON data export and real soft deletion that invalidates
  tokens and anonymizes resume, career, application, and evidence records.
- Added privacy policy acknowledgement UI and a clear destructive-delete
  confirmation.
- Added pending-order expiry, idempotent payment fulfillment, provider
  transaction tracking, and HMAC callback verification for configured
  non-demo callback channels.
- Added job subscription `match_filter` and `last_notify_at` fields while
  preserving favourite CRUD and the existing enabled flag.
- Added membership expiry, auto-renew preference, recent order history, and
  job-subscription filter controls in the miniprogram UI.

## Deferred TODOs

- Implement the actual WeChat Open Platform code exchange after an HTTPS domain
  is whitelisted and callback state handling is designed.
- Replace the generic SMS HTTP gateway contract with a provider-specific client
  only when the selected vendor is confirmed.
- Replace the HMAC payment callback skeleton with the provider's canonical
  signed callback verification and real payment request initiation.
- Add shared rate-limit/code storage for multi-instance deployments.
- Add scheduled job matching/notification workers and an external job source.
- Defer MySQL/PostgreSQL migration, backup automation, monitoring, HTTPS
  deployment, application reminders, resume versions, administration, and team
  collaboration to later phases.
