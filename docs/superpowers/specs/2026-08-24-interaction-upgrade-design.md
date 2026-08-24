# Frontend Interaction Upgrade Design

## Scope

This iteration has two strictly separated code scopes:

- `resume-miniprogram` H5: enhance existing pages only. No new experience-evidence, career-assessment, job-comparison, membership, or order business pages/modules are added. Existing APIs, page structure, Chinese copy, mock data, and business flows remain unchanged.
- `web-frontend`: upgrade the interaction experience across the existing independent Web shell and views. The interaction foundation must be reusable by future experience-evidence, career-assessment, job-comparison, membership, and order modules, but those business modules are explicitly out of scope for this iteration.

Both scopes must preserve current API contracts and must not introduce a third-party animation library. The existing CSS-token architecture remains the source of truth: Web keeps its `base.css` custom properties and H5 keeps the Uni-App global variables in `src/App.vue`.

## Interaction Direction

Use one interaction contract with platform-specific thin implementations. Both frontends expose the same conceptual states: idle, pending, success, error, and cancelled. Async handlers keep their current request functions and data mutations; only their view state and cleanup are enhanced. Every pending state is cleared in `finally`, including rejected requests and abort/cancel paths.

Selected interactions:

- Press-bounce on high-frequency primary buttons and action cards.
- Unified CSS spinner inside async buttons and in block/page loading states.
- Page/module transitions with stable containers so content does not jump.
- Skeleton settle states with fixed or minimum dimensions.
- Web overview metric number transition for changing counts.
- Existing success messages gain a restrained checkmark draw treatment.
- H5 role-comparison cards receive a light flip transition because the page already presents comparison cards.
- H5 job-collection switches receive a small elastic state transition.

Skipped interactions: particle burst, liquid slider, hamburger morph, swipe-away deletion, and bottom-sheet drawer. No current high-frequency component requires them, and adding them would increase motion without improving task completion.

## Web Implementation

Create reusable presentation primitives under `web-frontend/src/components`:

- `LoadingSpinner.vue`: CSS-only spinner with size and accessible label props; usable inline, in buttons, and in block overlays.
- `AsyncButton.vue`: preserves native button behavior and slot content while rendering the spinner, `disabled`, `aria-busy`, and a stable content width during pending state.

Wrap the dynamic view in `App.vue` with a keyed Vue transition using `mode="out-in"`. Keep the stage min-height and skeleton dimensions stable. The transition must be disabled or reduced under `prefers-reduced-motion: reduce`.

Update existing views only where async actions already exist:

- Login and verification actions.
- Overview, resume, career, and application refresh/actions.
- Job query and favorite.
- Annual insight query.
- Account consent, export preparation, and deletion request.

Each button uses the existing loading/saving state or a narrowly scoped new pending state. No request URL, payload, response shape, or business mutation changes. Success feedback keeps the existing Chinese text and adds a CSS checkmark animation through the existing success notice class.

Extend `base.css` with shared motion/loading variables, press states, spinner styles, reduced-motion fallbacks, and metric transition styles. Do not add broad `transition: all`; animate transform, opacity, color, background, border, and box-shadow only where needed.

## H5 Implementation

Create a Uni-App-compatible `LoadingSpinner.vue` under `resume-miniprogram/src/components`. It uses `view` elements and CSS variables only, so it works in H5 and does not require a browser-only API. Existing native button `:loading` props remain valid; the component is used for block/page loading and for high-frequency custom button states where native loading is not currently visible enough.

Extend the global styles in `resume-miniprogram/src/App.vue` with shared motion/loading variables, stable press-bounce behavior, spinner/keyframes, and reduced-motion fallbacks. Add a mount transition to the existing page-root classes so route changes feel continuous without changing route APIs or page structure.

Apply the component and interaction classes to existing high-frequency pages only, prioritizing login, account, job collection, career planner, resume editor, applications, drafts, and existing role comparison. Keep existing skeletons and add spinner/settle behavior without changing their content or API flow. Audit each touched async handler so error and cancellation paths always clear its loading flag.

## State and Error Handling

Pending state is view-local and cannot alter API behavior. Buttons are disabled while their own request is pending, preventing duplicate submissions. All new pending flags are reset in `finally`; if a request is aborted or rejected, the existing error path remains unchanged and the button returns to idle.

Loading indicators must be announced with existing `aria-live`/accessible labels where the platform supports them. The Web spinner must not replace the existing Chinese button labels; it appears alongside them or in a stable inline slot.

## Verification

- Add focused Web unit coverage for async button state cleanup and metric transition input behavior where pure helpers are introduced.
- Add focused H5 utility coverage for any new loading-state helper; existing page/API tests remain unchanged.
- Run Web `npm.cmd run test` and `npm.cmd run build`.
- Run H5 `npm.cmd run test:unit` and `npm.cmd run build:h5`.
- Run the existing standalone dashboard verifier if affected by shared public assets.
- Run the Impeccable detector against changed Web sources.
- Record all selected and skipped interactions, touched components, and loading/error guarantees in `docs/interaction-upgrade-changelog.md`.
