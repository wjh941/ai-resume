# Front-end interaction upgrade changelog

Date: 2026-08-24

## Scope

- `resume-miniprogram`: H5 interaction enhancement only. Existing pages, routes, API interfaces, mock data, Chinese copy, and business flows are unchanged. No new experience-evidence, career-assessment, job-compare, member, or order business modules were added.
- `web-frontend`: interaction foundation plus the independent functional workbench modules listed below. H5 business pages remain unchanged.

## Shared interaction foundation

- Added CSS-only loading spinner components for both frontends.
- Added unified motion/loading variables and reduced-motion handling.
- Added async state helpers that always clear pending state in `finally`, including rejected and cancelled requests.
- Added fixed-height block loading surfaces and route/view transition shells to prevent content jumps.

## 2026-08-24 next interaction iteration

The following changes are interaction-only and preserve existing APIs, routes, page structure, mock data, Chinese UI copy, and business logic.

### `web-frontend`

- `AsyncButton` now exposes a stable `is-loading` hook while retaining native disabled behavior, `aria-busy`, and the shared inline spinner.
- Primary action buttons use a restrained CSS ripple/press response; the base motion and loading variables remain centralized and reduced-motion aware.
- View transition shells and skeleton blocks keep their layout stable during route/module swaps.
- `ComparisonRolePicker` locks role chips and the compare action while the existing comparison request is pending, preventing duplicate submissions without changing the comparison API.
- Added `FutureCapabilityShell` as a presentation-only slot for future capability surfaces. It contains no request, routing, or business logic and does not replace any delivered module.

### `resume-miniprogram` H5

- Existing `App.vue` page-enter and loading-block styles now expose semantic motion/spinner aliases and a stable loading-block minimum height.
- `resume-form` clears suggestion and draft-save pending state in `finally`; save taps are guarded/disabled and suggestion loading uses the shared spinner.
- `template-picker` guards the existing readiness check, clears the selected-template loading state on success, failure, abort, or warning cancellation, and disables competing template actions while pending.
- `evidence` adds shared list loading feedback, guards save/delete taps, and always clears row delete loading in `finally`.
- `knowledgebase` separates data-source loading from the existing initialization request, disables duplicate initialization taps, and clears source loading on all outcomes.
- No new H5 business page or module was added; experience evidence, assessment, comparison, membership, and order routes remain existing capabilities only.

### Pending-control audit follow-up

- Web `CareerView` task toggles now reject duplicate updates and lock all task checks while one status request is pending.
- Web `ApplicationsView` locks row follow-up, reminder, status, edit, and delete controls during an active request; filter changes cannot start a second refresh.
- Web `AccountView` prevents consent, export, and deletion requests from overwriting one another; all account actions share one disabled pending surface.
- Web Jobs, Insights, and Assessment mode switches are disabled while their current query or submit request is running.
- H5 applications now expose separate syncing, timeline, reminder, and delete loading states with `finally` cleanup; career-planner task toggles show a fixed-slot spinner to avoid row jitter.
- H5 career assessment, membership, operator knowledgebase, job search, job collection, privacy backup, and resume editor async controls now pair native loading feedback with disabled guards.
- H5 operator knowledgebase version reads/restores and application timeline/reminder/delete flows clear state on failure or cancellation; no request payload or route changed.

### Final pending-control hardening

- H5 login now mutually disables verification-code and phone-login actions while either request is pending, with function-level duplicate guards for password login/register as well.
- H5 resume-editor version comparison and restore actions use independent inline loading states keyed by version id, clear them in `finally`, and lock competing save/import/export/version actions without changing version API calls.
- H5 job collection save/remove and subscription switch/filter requests reject cross-action duplicates while retaining the existing native switch pending treatment.

## `web-frontend`

- `AsyncButton`: reusable pending button with disabled click protection, `aria-busy`, and inline spinner.
- `useAsyncAction`: duplicate-submit guard with guaranteed pending cleanup.
- `AnimatedNumber`: lightweight keyed number transition for overview metrics.
- `App` and topbar: out-in view transition and logout loading state.
- Existing login, overview, resume, career, jobs, applications, insights, and account controls now expose request loading states; skeleton blocks include a spinner overlay.
- Success notices use a restrained checkmark draw animation.
- High-frequency action buttons use native press depth/ripple-compatible transitions; no heavy animation dependency was introduced.
- Existing view headings now provide stable `aria-labelledby` targets for the transition shell.

## Web functional completion

- Resume drafts: `ResumeView` now supports open, copy, delete, and stable pending states; `ResumeEditorView` edits basic data, job target, education, employment, projects, skills, certificates, and self-evaluation through the existing draft API.
- Applications: `ApplicationsView` adds edit mode, row-level status updates, timeline disclosure and append, reminders, deletion confirmation, filters, and per-record loading cleanup.
- Experience evidence: `EvidenceView` and `EvidenceForm` support five evidence kinds, verified state, edit/delete, role-based suggestions, and readiness checks against a selected real draft.
- Membership and orders: `MembershipView`, `MembershipPackageCard`, and `OrderRow` show entitlement, packages, pending orders, demo payment confirmation, and order history. VIP state changes only after the payment callback succeeds.
- Career assessment: `AssessmentView` and `AssessmentQuestionCard` support answer progress, saved-answer restoration, simplified/professional report modes, result action plans, and membership navigation for upgrade notices.
- Role comparison: `ComparisonView` and `ComparisonRolePicker` load recommendation roles, enforce unique 2–4 role selection, render comparison score/strength/gap/risk/action data, and retain selections on request failure.
- Navigation: Web sidebar entries now expose evidence, membership, assessment, and comparison; Career, Jobs, Account, Assessment, and Comparison views provide handoff actions without changing backend interfaces.
- Loading and failure behavior: every new async action uses `AsyncButton` or a block skeleton/spinner, disables duplicate clicks, and clears pending state in `finally`; failed saves preserve local form values.
- Tests: Web workflow helper tests cover drafts, applications, evidence, membership, assessment, and comparison state transitions. Existing H5 files and interfaces were not modified in this iteration.

## `resume-miniprogram` H5

- Added `LoadingSpinner` and `runWithLoading` primitives.
- Global page enter, skeleton settling, button press, spinner, and reduced-motion styles are defined in `App.vue`.
- Account: privacy consent, export, deletion, and sign-out buttons show pending state and clear it on failure/finalization.
- Job collection: save/remove actions, alert switch, and filter save expose pending state; the switch receives a restrained elastic/pending treatment.
- Applications: save flow now clears its button loading state even when the store request rejects; loading block retains its original text and gains a spinner.
- Drafts: refresh/open/copy/delete actions are protected against duplicate taps and clear pending state in `finally`.
- Career planner: existing recommendation/task loading states gain a stable skeleton surface and spinner; existing tier transition remains lightweight.
- Resume editor: draft save/import/export/version actions expose pending state; export skeleton keeps a stable minimum height and adds a spinner.
- Role comparison: existing reveal animation is retained, with a small press-depth/card interaction and loading spinner.
- Login page existing native loading states were preserved rather than replaced.

## Deliberately not enabled

Particle bursts, global card flips, swipe-away deletion, bottom-sheet drawers, and animations on low-frequency controls were skipped because the current page structure does not need them and they would add motion without improving the primary H5 workflows.

## Verification

- Web unit tests: 38 tests passed across 12 files; production build passed.
- H5 unit tests: 36 files, 86 tests passed.
- H5 build passed with `npm run build:h5`.
