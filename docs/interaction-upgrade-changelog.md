# Front-end interaction upgrade changelog

Date: 2026-08-24

## Scope

- `resume-miniprogram`: H5 interaction enhancement only. Existing pages, routes, API interfaces, mock data, Chinese copy, and business flows are unchanged. No new experience-evidence, career-assessment, job-compare, member, or order business modules were added.
- `web-frontend`: interaction foundation and full existing-view feedback upgrade. Missing business capabilities remain reserved for later work and are not implemented here.

## Shared interaction foundation

- Added CSS-only loading spinner components for both frontends.
- Added unified motion/loading variables and reduced-motion handling.
- Added async state helpers that always clear pending state in `finally`, including rejected and cancelled requests.
- Added fixed-height block loading surfaces and route/view transition shells to prevent content jumps.

## `web-frontend`

- `AsyncButton`: reusable pending button with disabled click protection, `aria-busy`, and inline spinner.
- `useAsyncAction`: duplicate-submit guard with guaranteed pending cleanup.
- `AnimatedNumber`: lightweight keyed number transition for overview metrics.
- `App` and topbar: out-in view transition and logout loading state.
- Existing login, overview, resume, career, jobs, applications, insights, and account controls now expose request loading states; skeleton blocks include a spinner overlay.
- Success notices use a restrained checkmark draw animation.
- High-frequency action buttons use native press depth/ripple-compatible transitions; no heavy animation dependency was introduced.
- Existing view headings now provide stable `aria-labelledby` targets for the transition shell.

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

- Web unit tests and production build passed.
- H5 unit tests: 36 files, 83 tests passed.
- H5 build passed with `npm run build:h5`.
