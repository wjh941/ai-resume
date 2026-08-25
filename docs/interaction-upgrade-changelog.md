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

## 2026-08-24 polish and robustness pass

This pass keeps all existing routes, API contracts, mock data, Chinese UI copy, and business modules intact. It only refines feedback, motion, and responsive behavior.

### `resume-miniprogram` H5

- Added shared `ui-error-tip` tokens in `App.vue` and applied them to existing network, permission, validation, and parameter-error surfaces across login, account, jobs, applications, drafts, assessment, planner, knowledgebase, membership, orders, comparison, and editor-related pages.
- Added one disabled-state contract for native disabled buttons and `.is-disabled` controls, including consistent opacity, muted color/border, no press transform, and no shadow.
- Tuned the shared easing curve to a non-overshooting curve, reduced press scale, and switched page-entry translation to `translate3d` to reduce low-end mobile jitter.
- Kept `FormField` validation inline while reusing the same semantic error color system.

### `web-frontend`

- Added globally registered `ErrorNotice` and migrated existing business-view error states and login validation errors without changing their messages, retry actions, or request logic.
- Added a short `theme-switching` transition window with initial-render protection, `color-scheme`, and shared surface transitions to prevent partial dark/light flashes.
- Unified disabled button feedback and motion easing tokens; removed the global box-shadow transition that caused unnecessary repaint work.
- Added responsive guards for ultra-wide workspaces and 540px/380px windows, including topbar action spacing, user-chip truncation, and stable workspace padding.

### Verification for this pass

- Web unit tests: 40 passed across 12 files; production build passed.
- H5 unit tests: 87 passed across 36 files; `npm run build:h5` passed.

## 2026-08-24 robustness edge-case follow-up

This follow-up preserves every existing page, route, API contract, request payload, mock record, Chinese UI string, and business workflow. The changes remain limited to shared interaction feedback and rendering behavior.

### `resume-miniprogram` H5

- Added the shared `showErrorToast` helper for transient network, permission, invalid-parameter, and timeout errors while keeping existing inline validation messages and success/neutral toasts unchanged.
- Strengthened the global disabled-button contract so native disabled attributes cannot be overridden by page-level button backgrounds; disabled controls also suppress press transforms and shadows.
- Reused the centralized non-overshooting motion curves and GPU-friendly transforms on frequent planner, job-search, and comparison interactions, with reduced-motion fallbacks intact.
- Added `content-visibility` containment to existing application, evidence, collection, and job-search list records so off-screen content can skip rendering without changing list data or actions.

### `web-frontend`

- Standardized all existing business-view and login errors on the shared `ErrorNotice` component, including consistent semantic icon treatment and unchanged retry behavior.
- Limited color/surface transitions to the explicit `theme-switching` window, skipped the initial render, cleared repeated-toggle timers, and disabled theme motion under reduced-motion preferences to avoid light/dark flash.
- Retained the ultra-wide and narrow-window layout guards and applied off-screen rendering containment to application, evidence, record, task, and order rows.
- Kept all long-list data sources, API calls, routing, module ownership, and completed business capabilities unchanged.

### Verification for this follow-up

- Web unit tests: 41 passed across 12 files; production build passed.
- H5 unit tests: 89 passed across 37 files; `npm run build:h5` passed.

## 2026-08-24 accessibility and UX polish

This iteration preserves every existing route, API contract, request payload, mock record, Chinese business string, and completed business module. Changes are limited to accessibility semantics, duplicate-action guards, and read-only text presentation.

### `resume-miniprogram` H5

- Added accessible labels, validation relationships, keyboard semantics, and expanded-state metadata to existing form fields, job-search suggestions, market-source rows, analysis rows, application actions, and onboarding controls.
- Changed the onboarding mask to close only when the mask itself is tapped; taps inside the content panel stop propagation. Existing native `uni.showModal` confirmations remain unchanged.
- Added function-level pending guards to high-frequency application, assessment, job-search, membership, checkout, upload, and analysis actions so rapid taps cannot start duplicate requests. Existing `finally` cleanup remains responsible for clearing all pending states after success, failure, cancellation, or timeout.
- Added a lightweight `ExpandableText` component to existing application, collection, job-search, and resume-preview content. Long role/company names use one-line truncation; resume descriptions use four-line truncation with keyboard-accessible expand/collapse controls.

### `web-frontend`

- Added form error relationships, invalid-field state, pressed-state metadata, and contextual action labels across login, topbar, applications, jobs, insights, and resume management without changing submissions or navigation.
- Added function-level pending guards to logout, login/code delivery, career task creation, evidence readiness, insights, job search, and job favorite actions. Buttons and mode tabs remain disabled while the corresponding request is active.
- Added the same lightweight `ExpandableText` contract to application role/company rows, job result titles and summaries, resume draft titles, and evidence action descriptions. Editor textareas continue to expose full content.
- The Web workbench has no custom tooltip, modal, drawer, or mask implementation. Existing native `title` tooltips retain browser-managed viewport positioning, and destructive actions continue to use native `window.confirm` behavior.

### Verification for this iteration

- Web unit tests: 44 passed across 13 files; production build passed.
- H5 unit tests: 92 passed across 38 files; `npm run build:h5` passed.

## 2026-08-24 quality-of-life and form robustness

This iteration keeps all existing routes, API contracts, request payloads, mock data, Chinese business copy, and completed modules intact. It adds form resilience and bounded rendering only; no business page, remote autosave request, dependency, or backend capability was introduced.

### `resume-miniprogram` H5

- Resume-form validation now surfaces inline feedback for name, phone, email, and target role. Job search reports its missing-role error beside the input, and career assessment shows unanswered-step guidance while preserving the existing non-blocking next-step and final-submit navigation.
- Local resume checkpoints use an 800 ms debounce, flush on hide/unmount and before manual save, and expose local saving/saved/error status. Draft changes never call the remote API; the existing save button remains the only remote-save entry point and retains its pending guard.
- Native import-preview and version-restore modals restore the prior connected focus target after close. Existing modal success callbacks, confirmation behavior, and business effects are unchanged.
- Drafts, applications, evidence, and saved jobs render progressively at 20 initial records and 20 records per increment, while the original source arrays remain authoritative and all records remain reachable.
- The three additive H5 empty-state helper sentences are exactly: “本机填写中的内容也会自动保留。”, “可先查询岗位，再回到这里记录进度。”, and “暂未找到匹配岗位，可换一个更具体的岗位名称。”. Their “前往填写简历” and “查询岗位” actions navigate only to the existing resume-form and job-search routes; no route or page was added.

### `web-frontend`

- Resume-editor validation now reports draft name, name, phone, email, and target-role errors inline. Job search uses field-specific role feedback, and assessment identifies unanswered questions while continuing to block incomplete or duplicate submission before the existing API call.
- Local draft checkpoints use the same 800 ms debounce, reject malformed/stale/unsupported records, isolate storage failures from remote errors, preserve edits made during an in-flight save, and clear only after a successful unchanged manual save. No remote autosave was added.
- Desktop shortcuts are `Ctrl/Cmd+S` for manual draft save, `Alt+ArrowLeft` for editor back, and scoped `Escape` for applications edit/timeline close. Exact modifiers, repeat/IME suppression, and the same pending guards used by manual actions prevent duplicate or conflicting operations.
- Resume drafts, filtered applications, evidence records, and membership orders render progressively at 40 initial records and 40 records per increment. Source objects remain authoritative, refreshed/filtered lists reset their window, and every source record remains reachable.
- The three additive Web empty-state helper sentences are exactly: “本机编辑内容会自动保留，手动保存后同步到服务端。”, “可直接使用上方表单新增第一条记录。”, and “输入具体岗位名称后开始整理能力要求。”. Existing empty-state copy remains present.
- Application records retain all five desktop columns (icon, role/company, status, next action, actions), use stable widths and horizontal scrolling on wide layouts, and return to the existing stacked layout at `840px` and below.

### Verification for this iteration

- Impeccable UI detector: the single run over the command's listed target set returned `[]`; no detector remediation was required. The command did not include the changed H5 `App.vue`, H5 `pages/resume-editor/index.vue`, or Web `AssessmentQuestionCard.vue`. Scoped static interaction contracts cover the H5 progressive-scroll/containment rules, both resume-editor modal focus-restoration hooks, and the Web assessment-card invalid-state wiring; task code review covered all three files. This is alternative evidence, not detector coverage.
- H5 unit tests: 115 passed across 42 files, including the existing API and phase-service contract suites. `npm.cmd run build:h5` completed with `DONE  Build complete.`
- Web unit tests: 83 passed across 19 files, including `api.spec.ts` and `domain-api.spec.ts`. The production build transformed 1800 modules and completed successfully.
- Scope audit against the authoritative execution base `69e26d86fe1613b3b8be0bcf5684852735ff092f` and the plan reference `b0dbe20` found no changes under backend, service, API, router, mock, or fixture paths and no lockfile changes. `git diff --check` passed for both ranges and the working tree.
- Existing Chinese business strings were preserved or moved unchanged into focused helpers. The exact lists above are limited to the three empty-state helper sentences per frontend; local-save status, assessment inline guidance, progressive-list fallback, validation, and the two existing-route action labels are additional interaction copy and are not presented as an exhaustive string inventory. API contract tests are green for mock/request mapping; no live-backend smoke result is claimed by this frontend-only verification.

### Final review robustness fixes

- H5 resume-form mutations now have one local persistence owner: ordinary add and suggestion actions use the caught 800 ms orchestrator debounce, while template navigation awaits the draft watcher and flushes the same caught local-only path. A storage failure sets the existing local error state and cannot block navigation or leave a second delayed write.
- Web resume saves that fail validation now expose the first existing field error through a form-level `role="alert"`, then focus and center the first invalid control in form order. After feedback is active, correcting that field advances the summary to the next current error and correcting all fields clears it; no errors are announced before the first save attempt. Button, form-submit, and `Ctrl/Cmd+S` paths continue to call the same manual-save function; no remote autosave was added.
- Visible resume back and application edit-cancel controls now share the same function-level pending guards as their keyboard paths. Native disabled and `aria-disabled` state uses the existing global button contract during load, create, update, delete, and related pending application actions.
- Final focused verification passed: H5 26/26 tests and Web 39/39 tests. Final full verification passed: H5 117/117 tests across 42 files plus the H5 production build; Web 88/88 tests across 20 files plus the Web production build.
- These final-review UI fixes were made after the iteration's single Impeccable detector run. The detector was intentionally not rerun, so no detector coverage is claimed for these fixes; focused and full automated tests, both production builds, diff/scope checks, and scoped final code review provide the validation evidence.

## 2026-08-25 Web brand expression

This iteration strengthens the Web workspace's 求职成长 identity without
adding business capability or changing any API, route, mock data, request,
Chinese copy, state, prop, emit, or handler contract.

### `web-frontend`

- Overview now presents the existing KPI and action route as a clearer growth
  narrative through a compact stage marker, cobalt route cue, and restrained
  surface hierarchy. Existing KPI values, skeleton dimensions, refresh/retry
  states, and navigation actions remain unchanged.
- Resume editor chapters use existing section boundaries to create a stronger
  progression. Career tasks, assessment, comparison, and annual-insights
  results use a restrained cobalt decision band while record rows and cards keep
  their border-only elevation.
- Native transitions, dark mode, keyboard focus, disabled states, responsive
  wrapping, and reduced-motion rules remain in the shared CSS system.
- Browser QA passed for reachable career, assessment-invalid, comparison
  result/gate, and insights branches across light/dark 1440px and 390px states,
  including long-content clipping and elevation checks. Resume editor QA is
  blocked by the pre-existing `/api/draft/list` response-shape mismatch, and
  assessment-result QA is blocked by the pre-existing unconfigured AI service;
  neither blocker changed production code in this visual iteration.

### Verification

- Task 1 focused interaction test: 2/2 passed; build and browser QA passed.
- Task 2 focused workflows: 19/19 passed; build, detector, and scoped browser
  QA passed for all reachable branches.
- Final shell verification also covered 1920px and 390px without horizontal
  overflow, 44px navigation/theme targets, 3px keyboard focus, disabled button
  opacity/cursor/transform behavior, reduced-motion zero-duration animation,
  and the normal 180ms theme transition. The existing draft-list response-shape
  mismatch and unconfigured AI service remain documented external blockers for
  the unreachable editor/result branches.

## 2026-08-25 Web-backend integration robustness

This follow-up keeps the existing Web/H5 pages, routes, APIs, mock data, Chinese
copy, and business workflows intact while fixing two real development-mode
integration blockers found during browser QA.

### `web-frontend`

- `listDrafts()` now accepts both the documented `{ items: [...] }` envelope and
  the current backend `/api/draft/list` direct-array payload, preserving the
  existing camelCase mapping and all list actions.
- Added a domain regression case for direct-array draft responses.

### `resume-backend`

- Added a deterministic `DevelopmentAIClient` fallback for missing AI
  credentials in non-production environments. Career assessment submissions now
  use the existing `score_assessment` rules and persist/render a result during
  local demo and mock-mode use.
- Production and explicitly configured AI environments retain the existing
  real-client selection and explicit `ai_not_configured` failure behavior.
- Added backend coverage for development fallback selection/result shape while
  retaining production unconfigured-client coverage.

### Verification

- Web unit tests: 89 passed; production build passed.
- Backend tests: 195 passed, 1 skipped.
- Temporary SQLite integration smoke: login, draft save/list, and complete
  assessment submission all returned HTTP 200; draft list returned an array and
  assessment returned persisted result data.
