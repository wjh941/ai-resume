# Async View Error Boundary Design

## Goal

Keep the Web workbench usable when an on-demand view chunk fails to download.

## Scope

- Add a small shared error component for async view loading failures using the
  existing `ErrorNotice` presentation.
- Configure the existing `defineAsyncComponent` factory with two automatic
  retries, then render the error component instead of leaving a blank stage.
- Preserve the current view map, transition shell, navigation events, API
  requests, H5 behavior, mock data, and business modules.

## Constraints

- Native Vue/Vite behavior only; no dependencies or router changes.
- Keep error text concise and in Simplified Chinese; do not modify existing
  business-view copy.
- Retry only chunk loading; never retry domain API requests from this boundary.

## Acceptance criteria

1. Async views use `AsyncViewError` after bounded loader failure.
2. The loader retries at most twice and then calls `fail`.
3. The error component uses the shared `ErrorNotice` with `role="alert"`.
4. Focused and full Web/H5 tests and builds remain green.
