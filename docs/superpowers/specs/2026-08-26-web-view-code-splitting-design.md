# Web View Code-Splitting Design

## Goal

Reduce the initial Web JavaScript payload by loading business views on demand
while preserving the existing workspace navigation, transitions, loading state,
API calls, and page behavior.

## Scope

- Keep the authenticated shell, sidebar, topbar, login panel, and existing
  `Transition name="view-swap" mode="out-in"` behavior in the initial chunk.
- Convert existing Web business views, including the resume editor, to Vue
  async components backed by native Vite dynamic imports.
- Reuse `LoadingSpinner` as the async component loading state; keep async-load
  errors visible through Vue's existing error boundary behavior without changing
  request error handling.
- Do not change H5 page loading, API routes, request payloads, mock data, copy,
  or business modules.

## Constraints

- No new dependencies and no router replacement.
- Keep `WorkspaceView` keys, `editingDraftId`, emitted events, and active-view
  mapping unchanged.
- Avoid eager imports of business views from `App.vue` after conversion.
- Preserve reduced-motion CSS and existing stable transition-shell height.

## Acceptance criteria

1. `App.vue` uses `defineAsyncComponent` and dynamic imports for all existing
   Web business views.
2. Loading views render through the shared `LoadingSpinner` component.
3. Focused source-contract tests fail before implementation and pass after it.
4. Web unit tests/build and H5 unit tests/build remain green.
5. Production build emits view chunks and reduces the entry JS asset below the
   192.66 kB baseline measured before this iteration.
