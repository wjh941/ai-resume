# Task 2 Report: Migrate Existing List Adapters

## Files Changed

- `web-frontend/src/lib/drafts.ts`
- `web-frontend/src/lib/dashboard.ts`
- `web-frontend/src/lib/evidence.ts`
- `web-frontend/src/lib/applications.ts`
- `web-frontend/src/lib/career.ts`
- `web-frontend/src/lib/membership.ts`
- `web-frontend/src/tests/domain-api.spec.ts`
- `web-frontend/src/tests/dashboard.spec.ts`

## Implementation

Each migrated list endpoint now types its response as a direct array or an optional `items` envelope, passes the payload through the shared `readItems` helper, and then applies the existing mapping/count logic. This covers drafts, dashboard applications/drafts/tasks, evidence and evidence suggestions, applications and timelines, career tasks, membership packages, and orders. Existing endpoint paths, request payloads, field mappings, public return types, and behavior are unchanged.

## TDD Evidence

1. Added direct-array fixtures for the affected list functions in `domain-api.spec.ts` and dashboard aggregation in `dashboard.spec.ts`, plus a malformed evidence payload assertion for `ApiRequestError` status `0`.
2. Ran the required red test command before adapter changes:

   `npm.cmd test -- src/tests/domain-api.spec.ts src/tests/dashboard.spec.ts`

   Result: 6 failures, all identifying legacy `.items` access (dashboard counts, evidence, applications/timelines, career tasks, and membership lists); 10 existing tests passed.
3. Migrated the adapters to `readItems`.
4. Reran the affected tests:

   `npm.cmd test -- src/tests/domain-api.spec.ts src/tests/dashboard.spec.ts`

   Result: 2 test files passed, 16 tests passed.
5. Ran the production build:

   `npm.cmd run build`

   Result: Vite build completed successfully.

## Concerns

- No known concerns. The repository has no TypeScript project config, so type validation is covered by the successful Vite production build.
