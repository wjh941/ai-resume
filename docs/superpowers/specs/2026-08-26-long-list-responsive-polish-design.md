# Long-list and Responsive Polish Design

## Goal

Reduce scroll-time layout work and prevent unrelated page regions from
participating in long-list reflow on the H5 and Web workbenches.

## Scope

- Apply the existing H5 `ui-long-list-item` containment contract to resume
  draft rows.
- Add a shared Web list-surface containment contract to the existing draft,
  evidence, application, task, and order lists.
- Preserve list ordering, incremental thresholds, API calls, routes, copy,
  mock data, and all business handlers.

## Constraints

- Native CSS containment/content-visibility only; no dependency or runtime
  virtualization library.
- No new pages, modules, API endpoints, request payloads, or business logic.
- Keep current responsive table overflow behavior and reduced-motion rules.
- Validate with H5 and Web unit tests, both production builds, and diff checks.

## Acceptance criteria

1. H5 draft rows carry the same `ui-long-list-item` class as other progressive
   lists and therefore use the existing intrinsic-size reservation.
2. Web list surfaces isolate layout/style work without changing their visible
   rows or horizontal table scrolling.
3. Existing H5/Web tests and builds remain green; no tracked backend changes.
