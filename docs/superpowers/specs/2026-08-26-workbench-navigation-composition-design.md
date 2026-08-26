# Web Workbench Navigation Composition Design

Date: 2026-08-26

## Intent

Make the existing Web workbench easier to understand by grouping related
tasks and turning the missing-career-profile response into a clear next step.
The experience should feel like a focused operating desk rather than a flat
list of modules.

## Scope

- Preserve all existing routes, view keys, API calls, request payloads, mock
  data, Chinese copy, and business logic.
- Keep every finished module intact: resume, career, jobs, applications,
  evidence, assessment, comparison, membership, insights, and account.
- Add only navigation composition and recoverable presentation for a missing
  career profile; do not add a new profile editor or business capability.
- Keep the existing `/api/job/query` contract and restore its deterministic
  development-only fallback when local AI credentials are absent; production
  remains explicitly unconfigured until real credentials are supplied.
- Keep H5 source untouched.

## Direction

Reading this as a job-seeker operating workspace: calm, premium, and task-led.
The selected composition is four navigation groups: preparation, decisions,
execution, and review/account. Existing labels remain the visible source of
truth; group labels provide orientation without changing destination behavior.

### Considered approaches

1. Replace the sidebar with a new router or dashboard: rejected because it
   risks route and business regressions.
2. **Grouped existing navigation (selected):** preserve each destination,
   add semantic group wrappers and restrained separators, and keep the active
   state obvious on desktop and mobile.
3. Add a new career-profile business page: rejected because this iteration is
   presentation-only and the existing H5 planner remains the profile owner.

## Missing-profile behavior

When recommendations fail with the existing 404 profile-not-found contract,
the comparison view will show an inline empty state that explains the required
precondition and links to the existing career-planning view. Other failures
retain the shared error notice. Loading and request contracts remain unchanged.

## Local job-query behavior

The local development environment may intentionally omit AI credentials. In
that mode the existing `DevelopmentAIClient` returns compact deterministic role
intelligence so the core岗位查询 workflow remains testable and visible. These
profiles are clearly framed by the existing structured-role report notice and
are never selected for production.

## Verification

- Add source contracts for grouped navigation and missing-profile branching.
- Run Web and H5 unit suites, both builds, `git diff --check`, and the
  Impeccable detector over changed UI targets.
- Verify the local Web document and production alias still serve this project.
