# Web Error Recovery Design

## Goal

Make recoverable Web read and query failures actionable without risking duplicate writes.

## Scope

- Add one shared API error-to-copy mapper for timeout, network, session expiry, permission, and generic failures.
- Add retry actions to page reads and idempotent queries in Overview, Career, Evidence, Membership, Account, Jobs, and Insights.
- Keep each page's existing input state when a query fails.
- Keep save, delete, payment, and other side-effect failures manual; never replay them automatically.
- Add focused tests for error mapping and source-level retry contracts.

## Non-goals

- No automatic retry loops or backoff.
- No global error event bus.
- No backend, mini-program, dependency, or payment changes.
- No persistence of API results.

## Design

`src/lib/api-error.ts` will expose `getApiErrorMessage(reason, fallback)` and classify the existing `ApiTimeoutError` / `ApiRequestError` statuses. The helper returns stable Chinese copy for timeout, offline/network failures, expired sessions, forbidden capabilities, and unknown failures.

Each affected view keeps its current request function and error state. Read/query catches call the shared mapper and render an `ErrorNotice` action that invokes the same idempotent refresh/query function. The retry action is only rendered for the page-read/query error state; mutation errors keep their existing message without a replay button.

## Acceptance criteria

1. Shared mapper returns the expected copy for timeout, 401, 403, network errors, and fallback errors.
2. Every scoped read/query error notice exposes a retry action wired to the original read/query function.
3. Mutation failures do not expose an automatic replay action.
4. Jobs and Insights retain query inputs after a failed query and retry with the same inputs.
5. Existing Web tests, strict TypeScript, production build, detector, and diff checks pass.
