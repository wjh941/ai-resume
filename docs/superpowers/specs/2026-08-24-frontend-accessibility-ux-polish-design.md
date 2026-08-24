# Frontend Accessibility and UX Polish Design

Date: 2026-08-24

## Objective

Improve accessibility, duplicate-action protection, long-text handling, overlay dismissal, and desktop tooltip behavior across the two existing frontends without adding business pages, changing business capabilities, or modifying API behavior.

The implementation starts from the repository's actual baseline commit `0e0d463` on `feature/ai-resume-demo`. The earlier commit `04f521d` remains historical context only.

## Scope Boundaries

### `resume-miniprogram` H5

- Enhance existing pages and components only.
- Add accessible names to core actions and interactive icons.
- Preserve natural form tab order and expose validation state to assistive technology.
- Close duplicate-submission gaps in existing asynchronous handlers.
- Apply a consistent truncation and expand/collapse pattern to job titles, company names, and resume content.
- Harden the existing onboarding overlay's mask-close behavior.
- Do not add a new page, route, API, data model, store, or business capability.

### `web-frontend`

- Preserve every delivered business module and its API behavior.
- Align accessible naming, form semantics, duplicate-action protection, and long-text behavior with H5.
- Keep existing confirmation flows intact and audit custom overlays before changing them.
- Keep desktop tooltip labels within the viewport by using native browser tooltips for icon-only controls instead of introducing a custom positioned tooltip layer.
- Do not replace existing modules with placeholder shells or add a new business module.

## Chosen Approach

Use targeted enhancements around the existing interaction foundation.

- Reuse `AsyncButton`, `useAsyncAction`, H5 loading refs, and current `finally` cleanup.
- Add handler-entry pending guards only where the current code relies solely on the rendered disabled state.
- Add one small `ExpandableText` component and one pure `isExpandableText(text, expandAt)` helper in each frontend because the projects have separate runtimes and styling systems.
- Use native HTML and UniApp accessibility attributes and CSS line clamping.
- Avoid a global click directive, arbitrary debounce timers, third-party tooltip libraries, and a speculative modal framework.

This approach limits the behavioral surface and keeps the business layer unchanged.

## Interaction Contracts

### Accessibility

- Icon-only buttons must have a concise `aria-label`; Web icon buttons also receive the same concise native `title` where tooltip feedback is useful.
- Decorative icons remain `aria-hidden="true"` so accessible names are not duplicated.
- Text buttons whose visible label already describes the action do not receive redundant labels unless surrounding context is required, such as a row-specific delete action.
- Form controls keep source-order keyboard navigation. No positive `tabindex` values are introduced.
- H5 reusable form fields expose `aria-label`, `aria-invalid`, and an error relationship when an inline validation error exists.
- Web inputs remain associated with their visible `<label>` elements; invalid fields expose `aria-invalid` and `aria-describedby` only when an error message is present.
- Expand/collapse controls expose `aria-expanded` and a stable relationship to their content.

### Duplicate-Action Protection

- Every audited asynchronous action uses two layers: a disabled/loading presentation and a synchronous handler-entry pending guard.
- A duplicate tap or click while pending returns immediately and starts no request.
- No time-based debounce or throttle is used. A new request is allowed as soon as the current action reaches its existing `finally` cleanup.
- Existing error, abort, timeout, and success handling remain unchanged.

### Long Text

- Job titles and company names use a one-line collapsed state.
- Resume narrative content uses a four-line collapsed state.
- The expand control appears only when trimmed content exceeds the configured character threshold: 18 characters for job/company identity text and 96 characters for resume narrative text. CSS line clamping still enforces one and four visible lines respectively.
- Expanded content shows the complete original value and offers a collapse action.
- Layout changes remain local to the record; list data, filters, selection, routing, and API payloads do not change.
- Original Chinese data and business copy remain untouched. The interaction labels `展开` and `收起` are controls, not replacements for existing content.

### Overlay Dismissal

- The existing H5 `OnboardingTour` mask closes the overlay when the mask itself is activated.
- The dialog content explicitly stops click/tap propagation so its buttons cannot accidentally close the overlay.
- The close path continues to emit the existing `complete` event; no new navigation or persistence behavior is introduced.
- Web currently uses native `window.confirm` for destructive confirmation and contains no custom modal/drawer mask in the delivered business views. No speculative overlay component is added.

### Tooltip Behavior

- Web icon-only controls use short native `title` text matching `aria-label`.
- Native browser tooltip positioning is retained because it is viewport-aware and does not require custom measurement or a third-party dependency.
- No CSS pseudo-element tooltip is added, avoiding overflow and keyboard/focus inconsistencies.

## Component Boundaries

### H5

- `FormField.vue`: accessible input and inline-error relationships.
- `ExpandableText.vue`: line-clamped text, thresholded expand control, and `aria-expanded` state.
- `utils/expandable-text.ts`: pure threshold predicate used by the component and unit tests.
- `OnboardingTour.vue`: reliable mask/content event separation and accessible action labels.
- Existing business pages: apply contextual labels, `ExpandableText`, and missing pending guards without changing requests.

### Web

- `AsyncButton.vue`: retain native disabled and loading semantics while forwarding accessibility attributes.
- `ExpandableText.vue`: Web line clamping and keyboard-accessible expansion.
- `lib/expandable-text.ts`: pure threshold predicate used by the component and unit tests.
- Existing components and views: add contextual labels, error relationships, native titles, and missing handler guards.
- `base.css`: centralized long-text and focus-visible presentation only; no business-page-specific data behavior.

## Data and Error Flow

The request flow remains unchanged:

1. A user activates an existing action.
2. The handler synchronously checks the action's current pending state.
3. If pending, the handler returns without issuing another request.
4. Otherwise, the existing pending state is set and the original API call runs.
5. Existing success or error behavior executes.
6. Existing `finally` cleanup clears pending state, including failure, abort, and timeout paths.

Long-text expansion is local presentation state and never mutates domain data.

## Testing Strategy

- Write failing tests before implementation.
- Add pure unit tests for `isExpandableText` threshold behavior and static component-contract tests for collapsed/expanded classes, `aria-expanded`, and the existing `展开`/`收起` controls. Do not add a component-mounting dependency.
- Extend static interaction-contract tests for H5 accessibility attributes, pending guards, and overlay event separation.
- Extend Web interaction tests for accessible icon labels, form error relationships, duplicate action guards, and native tooltip usage.
- Run the complete H5 unit suite and `npm run build:h5`.
- Run the complete Web unit suite and `npm run build`.
- Run one final UI static detector pass against changed frontend files.
- Run `git diff --check` and audit changed paths from `0e0d463` to confirm no API, service, store, route, mock, fixture, or dependency-lock change.

## Documentation and Completion

- Append the actual component coverage and verification totals to `docs/interaction-upgrade-changelog.md`.
- Keep the branch on `feature/ai-resume-demo` unless the user requests a different integration action.
- Finish with a clean Git worktree and no arbitrary file deletion.

## Acceptance Criteria

- Core icon-only actions and form errors expose appropriate accessible names and relationships.
- Natural keyboard order remains intact and no positive `tabindex` is added.
- Fast repeated activation starts at most one asynchronous request per action.
- Long job/company/resume text remains readable through a stable expand/collapse interaction without overflowing its container.
- H5 onboarding closes from the mask and never closes because dialog content bubbled to the mask.
- Web tooltips rely on viewport-safe native behavior.
- Existing business logic, APIs, routes, Chinese content, and mock data remain unchanged.
- Both frontend test suites and production builds pass.
- The changelog is updated and the worktree is clean.
