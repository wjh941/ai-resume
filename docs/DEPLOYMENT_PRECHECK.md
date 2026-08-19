# Deployment Pre-check

Complete every item before setting `APP_ENV=production`. Phase 7 retains
SQLite for development only; database migration, backup automation, monitoring,
and HTTPS server deployment are not included here.

## Authentication

- Set a unique 32+ character `JWT_SECRET` outside source control.
- Set `AUTH_DEMO_MODE=false`; the development code `123456` must never be
  accepted in production.
- Configure `SMS_PROVIDER=http`, `SMS_HTTP_ENDPOINT`, `SMS_ACCESS_KEY`,
  `SMS_ACCESS_SECRET`, `SMS_SIGN_NAME`, and `SMS_TEMPLATE_ID`.
- Verify the provider endpoint accepts the documented JSON request contract and
  returns an HTTP success only after accepting a message for delivery.
- Set practical `AUTH_RATE_LIMIT_*` and `SMS_CODE_*` values for the expected
  traffic. In-memory limits are process-local; use shared storage before a
  multi-instance deployment.

## WeChat Open Platform

- Register an HTTPS redirect domain in WeChat Open Platform before using the
  callback placeholder.
- Configure `WECHAT_OPEN_APP_ID`, `WECHAT_OPEN_APP_SECRET`, and
  `WECHAT_OPEN_REDIRECT_URI` as deployment secrets.
- The callback route intentionally does not exchange authorization codes yet.
  Implement and test provider-specific code exchange, state validation, and
  redirect handling before enabling WeChat login.

## Payments

- Configure merchant/provider secrets outside source control.
- Set `PAYMENT_CALLBACK_SECRET` only for the current HMAC callback skeleton.
- Verify the provider's signed callback specification before replacing the
  placeholder. No payment request initiation or real provider integration is
  enabled in this release.
- Confirm `ORDER_PAYMENT_EXPIRE_MINUTES` with the billing policy.

## Privacy

- Publish the privacy policy referenced in the Account page before release.
- Validate ZIP exports and soft deletion against the retention policy with
  legal/privacy review. Deletion anonymizes resume and career records while
  retaining membership orders for audit.
- Move temporary exports and account data to managed storage before production
  scale; this phase serves the archive directly from memory.
