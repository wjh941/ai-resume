# Frontend Quality-of-Life and Form Robustness Design

Date: 2026-08-24

## Baseline

- Branch: `feature/ai-resume-demo`
- Actual implementation baseline: `18afb5a`
- The requested `04f521d` reference is stale and is not used as the edit baseline.
- The worktree is clean at design time.

## Goal

Improve form feedback, local draft resilience, empty states, long-list rendering, desktop keyboard workflows, and wide-record layout without adding business pages, changing API contracts, changing mock data, or altering completed business modules.

## Scope Boundaries

### `resume-miniprogram` H5

- Enhance only existing resume form/editor, job search, career assessment, drafts, applications, evidence, job collection, and native modal interactions.
- Do not add routes, business capabilities, API calls, request fields, or backend pagination.
- Preserve manual remote draft saving as the only action that calls the draft save API.

### `web-frontend`

- Preserve login/session, dashboard, resume, jobs, career, applications, evidence, assessment, comparison, membership/orders, insights, account/privacy, responsive layout, and all corresponding API logic.
- Add only local checkpoint behavior, validation feedback, progressive list rendering, scoped shortcuts, empty-state enhancements, and stable wide-record layout.
- Do not create placeholder replacements or a generic table/modal framework.

## Resolved Requirement Conflicts

### Auto-save semantics

The current H5 resume form writes a local Pinia checkpoint on every deep change; neither frontend automatically calls the remote save API. This iteration optimizes local checkpoint persistence only:

- Debounce local persistence by 800ms.
- Keep manual save as the only remote save trigger.
- Show local saving/saved status.
- Flush a pending local checkpoint before leaving the editor.

This preserves API and business behavior while reducing synchronous storage writes. It does not claim to reduce a remote call path that does not currently exist.

### Empty-state copy

Existing Chinese UI strings remain byte-for-byte unchanged. Target empty states may add one short helper line and an action that navigates to an already delivered capability. Existing headings and descriptions are not rewritten.

### Virtual scrolling

The repository has no virtual-list dependency or backend pagination. The implementation will use bounded progressive rendering on top of the existing arrays and CSS containment:

- H5 initial limit: 20 records; increment: 20.
- Web initial limit: 40 records; increment: 40.
- Reloading or changing a filter resets the limit.
- Original arrays, ordering, filtering, mutations, and API responses remain unchanged.

No third-party virtualization library or backend API change is allowed.

### Career assessment validation

H5 questions remain optional, as stated by the current UI and business behavior. A fully unanswered step receives a non-blocking inline hint and may still advance or submit. Web retains its existing completeness rule and only improves field/question-level feedback.

### Tables and modal behavior

The Web workbench has no generic table component and uses CSS grid records. The application record grid is the wide table-like surface in scope. It receives explicit column tracks and a stable horizontal scroll container.

Web destructive confirmations remain native `window.confirm`, including browser-managed Escape and focus behavior. H5 native `uni.showModal` calls receive H5-only focus restoration around existing callbacks; modal contents and actions remain unchanged.

## Architecture

Use small native helpers and existing component patterns. H5 and Web follow the same interaction contract but do not share source files across packages.

### H5 units

- Extend existing resume validation mapping rather than adding a form framework.
- Keep the resume form's debounce timer and local save status page-local because it has one consumer.
- Add a small focus-restoration utility for existing H5 modal callers.
- Add `useIncrementalList` under H5 composables and reuse it in the scoped long-list pages.
- Reuse `FormField`, `ui-error-tip`, `LoadingSpinner`, Pinia checkpoint, and native `scroll-view` events.

### Web units

- Add a focused local draft checkpoint helper with parse, freshness, save, and clear operations.
- Add a focused resume validation helper aligned to H5 name, phone, email, and target-role rules, plus the existing Web draft-title requirement.
- Add a scoped keyboard listener in `ResumeEditorView`; add Escape handling only to views with a real closable edit/expanded state.
- Add `useIncrementalList` under Web composables and reuse it in the scoped record views.
- Reuse `ErrorNotice`, existing label/input markup, Lucide icons, CSS variables, and native `localStorage`/`IntersectionObserver` where available.

## Detailed Interaction Design

### H5 resume validation and local checkpoint

1. A save attempt builds `fieldErrors` from `validateResume`.
2. Relevant `FormField` instances receive their individual error strings.
3. Once validation is activated, subsequent input recomputes the map so corrected fields clear immediately.
4. The existing validation summary remains, and the duplicate unreachable validation branch in the current save handler is removed.
5. Deep draft changes set local status to saving and schedule one checkpoint after 800ms.
6. A later input replaces the timer; only the latest snapshot is written.
7. A successful checkpoint sets status to saved and exposes it through an `aria-live` surface.
8. Before unmount/hide, a pending checkpoint is flushed.
9. Manual save flushes/cancels the local timer, then runs the existing API call and loading cleanup unchanged.

Local status labels are additive interaction copy. Existing save button and toast strings remain unchanged.

### Web resume validation and local checkpoint

1. Load the existing server draft through the current API.
2. Read the local checkpoint for the same draft ID.
3. Restore it only when its `savedAt` timestamp is valid and newer than the server `updatedAt` timestamp.
4. Ignore malformed, mismatched, stale, or unsupported checkpoint data.
5. Once hydration completes, deep draft changes schedule an 800ms `localStorage` write.
6. Show saving/saved/failure status through a compact live region.
7. Manual save uses the existing API and payload mapper. On success, clear the checkpoint and emit the existing `saved` event.
8. Validation activates on save and updates inline while the user corrects fields.

### Job search validation

- H5 and Web role inputs keep their current submission and API flow.
- An empty submitted query sets a field-specific inline error, `aria-invalid`, and `aria-describedby`.
- Typing a valid non-empty value clears the field error.
- Network/API errors continue to use the existing global error surface and are not presented as field errors.

### Career assessment validation

- H5 tracks whether the current step has any answer.
- Attempting to advance from a fully unanswered step displays a non-blocking inline hint near the step controls, then continues using the existing navigation/submit behavior.
- Selecting an answer clears the hint.
- Web retains its current completion requirement and marks unanswered question cards/summary state without changing submit eligibility.

### Empty states

Target surfaces:

- H5: resume drafts, applications/delivery records, and job-search no-result state.
- Web: resume drafts, applications, and job-search no-result state.

Each target retains its current heading and description, then gains:

- A refined existing CSS illustration or existing Lucide icon treatment.
- One supplemental helper line.
- At most one action to an existing route/view where an obvious next step exists.

No new illustration dependency, bitmap asset, route, or business action is introduced.

### Progressive list rendering

Apply only to collections that may grow materially: drafts, applications, evidence, job favorites, and orders where present.

- The rendered view is `items.slice(0, limit)`.
- H5 `scroll-view` raises the limit on `scrolltolower`.
- Web uses an `IntersectionObserver` sentinel when supported and retains an accessible show-more command as a fallback.
- Filter and refresh operations reset the limit before rendering the new result.
- Delete/edit/status operations continue to mutate the original source array.
- Existing `content-visibility`, containment, and reduced-motion behavior stay enabled; intrinsic row sizes are adjusted per row family to reduce scroll correction.

### Desktop keyboard shortcuts

- `Ctrl+S` / `Cmd+S`: invoke the existing resume save handler and prevent the browser save dialog.
- `Alt+ArrowLeft`: invoke the existing resume-editor cancel/back event.
- `Escape`: close the current Applications edit state or expanded timeline when one exists. Native confirmations remain untouched.
- Ignore shortcuts while an IME composition is active.
- Reuse existing pending guards so shortcuts cannot duplicate requests.
- Register listeners on mount and remove them on unmount.

### H5 modal focus restoration

- Before an existing `uni.showModal` call, capture the active H5 DOM element when `document` exists.
- After cancel or completion, restore focus only when the element remains connected and exposes `focus()`.
- Do not access DOM globals in MiniProgram builds.
- Do not prevent the modal from taking focus while open.

### Wide application record layout

- Define all five application-row columns explicitly: icon, role/company, status, next action, actions.
- Give the wide row a stable minimum width and keep the existing responsive stacked layout below its breakpoint.
- Put horizontal overflow on the table/list wrapper, with touch-friendly momentum behavior and stable scrollbar gutter where supported.
- Do not calculate widths in JavaScript and do not add resize listeners.

## Error and Lifecycle Handling

- All timers are cleared on unmount; pending local writes are flushed once.
- Storage exceptions produce an inline local-save failure hint and never change API error state.
- A manual save cannot be started twice by a button or shortcut.
- Local save status cannot overwrite a remote pending/error surface.
- Fresh server content wins over stale local content.
- Focus restoration is best-effort and guarded for removed elements, unsupported environments, and modal-triggered navigation.
- Progressive rendering exposes all records eventually and never changes API data.

## Testing Strategy

Implementation follows red-green-refactor cycles.

### Unit and contract tests

- 800ms debounce coalesces rapid changes into one checkpoint.
- Flush writes the latest value once and timer cleanup prevents later writes.
- Web checkpoint freshness accepts newer valid data and rejects stale, mismatched, and malformed data.
- Resume validation returns field-specific messages for empty/invalid values and clears corrected fields.
- Job search empty input is field-invalid while API failures remain global.
- H5 assessment unanswered-step hint is non-blocking.
- Incremental limits start at 20/40, increase by their step, cap at list length, and reset on refresh/filter.
- Keyboard save/back/close commands ignore IME composition and respect pending state.
- Modal focus helper is a no-op outside H5 DOM and restores connected elements.
- Application grid exposes five explicit columns and horizontal overflow.

### Full verification

- `resume-miniprogram`: full unit suite and `npm run build:h5`.
- `web-frontend`: full unit suite and `npm run build`.
- Run the Impeccable UI detector once after UI changes are complete.
- Review desktop, narrow Web, and mobile H5 layout in one bounded visual pass when the local environment supports it.
- Run `git diff --check`.
- Audit changed paths against the implementation baseline and confirm no backend API, route, mock-data, or lockfile change.
- Existing frontend API tests remain the mock/backend docking contract for this frontend-only iteration.

## Changelog

Append a dated entry to `docs/interaction-upgrade-changelog.md` listing:

- Validation surfaces enhanced.
- Local checkpoint behavior and exact debounce interval.
- Empty states and existing navigation actions enhanced.
- Lists using progressive rendering and their thresholds.
- Keyboard shortcuts and wide-grid behavior.
- Modal focus restoration scope.
- Final test/build counts and scope audit result.

## Explicit Non-Goals

- No new H5 or Web business page.
- No remote auto-save.
- No backend pagination or API schema change.
- No third-party form, keyboard, table, or virtual-list dependency.
- No rewrite of existing Chinese UI strings.
- No generic table/modal framework.
- No changes to mock records or completed business modules.
