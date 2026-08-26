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

## Round 1 Fix: CareerView Adapter Contract

### Files Changed

- `web-frontend/src/views/CareerView.vue`
- `web-frontend/src/tests/interaction.spec.ts`

### Implementation

`CareerView.vue` now loads tasks through `listCareerTasks(planId)`, so direct-array and `{ items }` responses are normalized by the shared adapter. The view uses `CareerTaskRecord` camelCase fields, including `dueDate`. POST and PATCH calls remain on `requestApi` with their original endpoint paths and request payloads; their snake_case responses are normalized locally before updating the list.

### TDD Evidence

1. Added a source-contract assertion proving the adapter import/use and camelCase due-date field.
2. Ran the regression before the implementation:

   `npm.cmd test -- src/tests/interaction.spec.ts`

   Result: 1 failed, 17 passed. The new assertion failed because CareerView still imported `requestApi` for the list and used the legacy shape.
3. Implemented the adapter-based read flow and camelCase task mapping.
4. Reran covering tests:

   `npm.cmd test -- src/tests/interaction.spec.ts`

   Result: 1 test file passed, 18 tests passed.

   `npm.cmd test -- src/tests/domain-api.spec.ts src/tests/dashboard.spec.ts src/tests/interaction.spec.ts`

   Result: 3 test files passed, 34 tests passed.
5. Ran the production build:

   `npm.cmd run build`

   Result: Vite 5.2.8 transformed 1801 modules and completed successfully (`dist/index.html`, CSS, and JS emitted).

### Concerns

- `requestApi` remains intentionally used for CareerView POST/PATCH operations to preserve their exact existing request payloads; only list reads use `listCareerTasks`.
