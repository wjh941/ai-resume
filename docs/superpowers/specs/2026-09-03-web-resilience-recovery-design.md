# Web Resilience And Recovery Design

## Goal

Prevent avoidable work loss and dead-end states in the Web workbench while keeping the implementation dependency-free and scoped to existing Vue and Fetch patterns.

## Scope

- End the local session immediately after a successful account deletion request.
- Preserve unsaved assessment answers and role-comparison selections for the current browser session, scoped to the authenticated user.
- Add an inline retry action when the account data-scope request fails.
- Add a shared request timeout that preserves caller-provided abort signals.
- Replace the static connection claim in the topbar with neutral workspace-ready copy.

## Non-goals

- No backend API changes.
- No new npm dependencies.
- No persistence of full resume payloads in the new recovery layer.
- No redesign of the existing motion system in this iteration.

## Design

Account deletion emits a semantic `deleted` event from `AccountView`. `App` handles the event through the same local session cleanup path used by logout, then shows the existing login surface with a deletion-complete notice.

Assessment answers and comparison selections use small session-storage helpers keyed by the authenticated user id and feature name. Writes happen on user input/selection; successful submit or explicit completion clears the corresponding snapshot. Invalid or malformed snapshots are ignored.

The account error notice gets an existing `AsyncButton` retry action that calls its existing `refresh` function. Shared API requests use a bounded timeout via `AbortController`; if a caller supplies a signal, the request is aborted when either signal aborts, and timeout errors remain distinguishable from HTTP errors.

The topbar status becomes a neutral static readiness statement so it cannot claim a live connection it does not observe.

## Acceptance Criteria

1. Successful deletion clears the browser session and renders the login surface without waiting for another API call.
2. Refreshing the browser restores current-user assessment answers and comparison selections; another user cannot read the previous user's snapshots.
3. Account data-scope failures expose a visible retry button.
4. Requests that do not settle before the default timeout reject and stop loading states.
5. The topbar does not state that user data is connected unless a live status is actually supplied.
6. Existing Web tests and build remain green.
