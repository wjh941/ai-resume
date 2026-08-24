# Front-end Interaction Layer Next Iteration Design

Date: 2026-08-24

## Scope Boundary

### `resume-miniprogram`

This iteration only improves interaction feedback on existing H5 pages. It does not add pages, modules, API endpoints, mock data, or business capabilities. Existing page structure, Chinese copy, request payloads, stores, and business rules remain unchanged.

### `web-frontend`

All previously delivered business modules remain intact: experience evidence, career assessment, role comparison, membership, and orders. Their API adapters, request payloads, data mapping, and user workflows are not replaced or downgraded. This iteration changes only interaction behavior and may add neutral future-capability shell primitives that are not connected to business APIs.

## Interaction System

Both frontends keep native CSS animation and transition primitives. Motion and loading tokens are centralized at the application root. The shared contract is:

- A pending async action disables its trigger, exposes an inline spinner, and clears pending state on resolve, rejection, or cancellation.
- A route or view switch uses an out-in opacity/transform transition while preserving a stable content block height.
- Skeleton blocks reserve the final content rhythm and can show a spinner without shifting surrounding layout.
- Reduced-motion users retain visible state changes while authored motion is removed or shortened.

## Selective Interactions

- Primary submit/save/generate controls: press depth plus a restrained ripple treatment, with success check feedback where an existing success notice is already present.
- Frequent filter/mode switches: elastic scale on the active control only.
- High-value numeric metrics already using `AnimatedNumber`: retain the number transition; do not animate every text value.
- Existing list rows and cards: use hover/press transform only; no global flip, particle burst, swipe-away, or bottom-sheet behavior unless a current component already has that interaction need.
- Existing H5 hamburger/menu and drawers remain unchanged unless the page already exposes the corresponding control.

## Web Integration

- Extend the current `AsyncButton`, `LoadingSpinner`, `App` transition shell, and base CSS tokens rather than adding an animation dependency.
- Audit existing delivered Web views for missing `finally` cleanup, error retry state, and stable loading surfaces.
- Keep future capability reservation limited to reusable shell classes/slots or a neutral placeholder component; do not add new API calls or business workflows.

## H5 Integration

- Reuse `LoadingSpinner`, `runWithLoading`, root CSS variables, and existing page transition hooks.
- Audit page-level and button-level async handlers for `finally` cleanup, including rejection and abort paths.
- Add only content transition classes and interaction classes to existing templates; no page navigation or API behavior changes.

## Verification

- Add focused tests for pending cleanup, reduced-motion-safe interaction helpers, and transition state selection where pure helpers exist.
- Run all Web tests and build.
- Run all H5 unit tests and `build:h5`.
- Confirm no new H5 business page/module files and no API contract changes.
- Run `git diff --check` and keep the worktree clean before handoff.
