# Web Query Continuity Design

## Goal

Keep a user's job and annual-insight query intent available after a browser refresh, and make request timeouts understandable in the Chinese Web experience.

## Scope

- Persist Jobs query inputs (`roleName`, `reportMode`) in the existing user-scoped `sessionStorage` recovery layer.
- Persist Insights query inputs (`roleName`, `year`, `reportMode`) in the same layer.
- Restore only validated input fields on view setup; query results remain server-fetched and are not cached.
- Map shared request timeouts to a Chinese retryable error while preserving caller-initiated abort semantics.
- Add focused regression tests and keep existing Web tests/build green.

## Non-goals

- No URL query parameters or shareable links.
- No persistence of API results or full resume payloads.
- No backend, mini-program, or dependency changes.
- No motion redesign in this iteration.

## Design

Jobs and Insights read the current authenticated user id once and use the existing `workspace-recovery` helpers. Each view restores a small typed snapshot, watches its input refs, and writes changes to session storage. Invalid snapshots fall back to the existing defaults. The data is scoped by user id and naturally ends with the browser session.

The API layer marks timeout-triggered aborts separately from caller signals. Timeout failures become an `ApiRequestError` with status `0` and the Chinese message `请求超时，请稍后重试`; a caller-provided abort continues to reject with its original abort error.

## Acceptance Criteria

1. Refreshing Jobs restores its role input and selected report mode for the current user.
2. Refreshing Insights restores role, year, and report mode for the current user.
3. Malformed or invalid snapshots do not overwrite defaults.
4. Timeout failures expose the Chinese retryable error; intentional caller cancellation remains unchanged.
5. Existing Web tests, strict TypeScript, production build, detector, and diff checks pass.
