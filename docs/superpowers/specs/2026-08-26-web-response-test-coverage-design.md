# Web Response Contract Test Coverage Design

## Goal

Close the remaining low-priority regression coverage gap for the Web response
compatibility layer without changing production behavior.

## Scope

Add Vitest coverage for `{ items: [...] }` envelopes on the migrated application
and timeline, career-task, membership package/order, and evidence-suggestion
adapters. Add a source contract asserting that CareerView reads tasks through
`listCareerTasks` and renders the adapter's camelCase fields.

## Design

Reuse existing domain and dashboard test files. Each new fixture follows the
current backend snake_case field shapes and asserts the existing camelCase
mapping. Tests continue to mock only `requestApi`, preserving the real
`readItems` implementation. The source contract remains a lightweight static
guard because this project does not install Vue Test Utils.

## Constraints

- No production source changes, API routes, request payloads, mock data,
  Chinese copy, page structure, or business logic changes.
- Keep direct-array and envelope behavior covered; malformed-shape handling
  remains covered by the shared helper and evidence adapter tests.
- Use existing Vitest/Vite tooling only; add no dependencies.

## Verification

Run the affected domain/dashboard/interaction tests, then the full Web suite,
production build, and `git diff --check`. The backend is unchanged.
