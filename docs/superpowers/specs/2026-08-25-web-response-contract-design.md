# Web Response Contract Compatibility Design

## Goal

Harden the independent Web frontend's response boundary for high-frequency list
APIs. Existing backend routes, response envelopes, mock data, Chinese copy,
page structure, and business logic remain unchanged.

## Scope

The change covers list-shaped data consumed by these existing Web flows:

- Overview counts: applications, drafts, and career tasks.
- Resume drafts.
- Evidence records.
- Application records and timelines.
- Career tasks.
- Membership packages and orders.

Each adapter may receive either the current `{ items: T[] }` payload or a
legacy/direct `T[]` payload. The compatibility layer must preserve item mapping
and return a typed `T[]` to its caller.

## Design

Add one small shared response helper in the Web API boundary. It accepts a
direct array or an object with an array-valued `items` field. Invalid values
(missing payload, non-array `items`, or unrelated objects) raise the existing
`ApiRequestError` with status `0`, so views reuse their current error notices
instead of crashing during `.map` or `.length`.

The helper does not silently convert malformed responses to an empty list. An
actual empty array remains a valid empty state; an invalid shape remains an
observable integration error.

Existing adapters will call the helper before mapping snake_case backend fields
to their current camelCase domain types. The draft adapter's current direct-array
support will move onto the same helper. No backend endpoint will be changed.

## Error Handling

- `{ items: [] }` and `[]` resolve to `[]`.
- `{ items: [...] }` and `[...]` preserve item order and contents.
- `null`, `undefined`, `{}`, and `{ items: null }` reject with
  `ApiRequestError(status: 0)`.
- Existing HTTP, network, non-JSON, 204, and AbortError behavior in
  `requestApi` remains unchanged.
- Existing page-level loading `finally` blocks and `ErrorNotice` components
  remain responsible for clearing loading and presenting feedback.

## Testing

Add focused unit coverage for the helper's envelope/direct-array/invalid-shape
cases and at least one adapter per affected domain. Preserve existing full Web
unit tests and production build checks. Backend tests are not changed because
the API contract and backend implementation remain untouched.

## Non-goals

- No new business pages, modules, routes, API payloads, backend behavior, or
  mock data.
- No visual redesign or animation changes.
- No broad schema-validation dependency or generated client layer.
