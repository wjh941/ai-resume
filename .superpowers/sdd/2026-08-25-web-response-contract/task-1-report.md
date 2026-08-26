# Task 1 Implementation Report

## Result

Implemented the shared strict list-response boundary as `readItems<T>` in
`web-frontend/src/lib/api.ts`.

- Direct arrays are returned unchanged.
- `{ items: T[] }` envelopes return their `items` array unchanged.
- `null`, `undefined`, `{}`, and `{ items: null }` throw `ApiRequestError` with
  `status === 0`.
- Existing `requestApi` behavior and public request paths were not changed.

## Changed Files

- `web-frontend/src/lib/api.ts`: exported the minimal generic `readItems`
  runtime boundary beside `requestApi`.
- `web-frontend/src/tests/response-contract.spec.ts`: added focused Vitest
  coverage for direct arrays, envelopes, and malformed payloads.

## TDD Evidence

Initial focused run before implementation:

```text
npm.cmd test -- src/tests/response-contract.spec.ts
6 tests failed: readItems is not a function
```

Focused run after implementation:

```text
npm.cmd test -- src/tests/response-contract.spec.ts
Test Files  1 passed (1)
Tests       6 passed (6)
```

## Concerns

None. Adapter migrations and unrelated API behavior remain intentionally
outside this task.
