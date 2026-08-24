# Frontend Robustness Polish Design

Date: 2026-08-24
Branch: `feature/ai-resume-demo`
Baseline: `04f521d`

## Objective

Polish the existing interaction layer in `resume-miniprogram` H5 and the independent `web-frontend`. The work is limited to error-feedback consistency, motion and theme-transition robustness, disabled-state consistency, responsive edge cases, and long-list rendering performance.

All existing business pages, API contracts, request payloads, routes, stores, mock data, and Chinese UI copy remain unchanged. No business module or third-party animation/virtualization dependency is added.

## Existing Worktree Context

The working tree already contains the previous robustness pass: H5 global error and disabled-state tokens, the Web `ErrorNotice` component, theme-transition handling, responsive rules, tests, and changelog updates. This iteration extends those changes in place and must not revert or duplicate them.

## Design Decisions

### 1. H5 error feedback

H5 uses two presentation channels with one semantic specification:

- `ui-error-tip` remains the persistent inline error surface for page-load failures, permission denial, invalid parameters, and timeout/network errors that need to remain visible.
- A small `showErrorToast(message)` utility wraps `uni.showToast` for transient failures and validation feedback. It standardizes `icon: "none"`, duration, and mask behavior while preserving every existing message string.

Only existing error-shaped toast calls are migrated. Success, neutral information, clipboard confirmation, and offline-save status toasts keep their current behavior. Request functions, exception handling, and error-message generation remain unchanged.

### 2. H5 motion and disabled controls

Motion continues to use the centralized tokens in `resume-miniprogram/src/App.vue`. The non-overshooting easing, smaller press scale, `translate3d` page entry, and reduced-motion fallback remain the global contract. Any page-local transition still using generic `ease` is aligned to the shared motion token when it is part of a high-frequency interaction.

Native `button:disabled`, attribute-disabled buttons, and `.is-disabled` controls share opacity, color, border, shadow, filter, and transform rules. Page-specific color declarations may define enabled appearance but must not override the disabled contract.

### 3. Long-list rendering performance

The implementation uses native CSS containment instead of JavaScript virtualization:

- H5 long-list items in job results, application history, saved jobs, and evidence lists receive a shared long-item class.
- Web application, evidence, resume, task, and order list items reuse a shared selector.
- Supported H5/Web browsers apply `content-visibility: auto`, `contain: layout paint style`, and a conservative `contain-intrinsic-size` to avoid rendering off-screen items and reduce layout recalculation.
- Unsupported clients ignore these declarations and render exactly as before.

No list is paginated differently, truncated, reordered, memoized through custom business code, or replaced with a virtual-scroller dependency.

### 4. Web error and dark-mode feedback

All existing Web business errors continue to render through globally registered `ErrorNotice`. The component owns alert semantics, compact presentation, and optional action slots. Existing messages and retry handlers stay at their current call sites.

Theme animation runs only during the short `theme-switching` window. Initial page load updates `data-theme` without animation. During an intentional toggle, common foreground, background, border, fill, stroke, and shadow changes transition from the same token. Reduced-motion users receive an immediate theme change. The cleanup timer is always replaced on repeated toggles, so the transition class cannot remain stuck.

### 5. Responsive boundaries

Existing breakpoints remain authoritative. The polish pass verifies and adjusts only edge cases:

- At 1600px and wider, content remains centered with a bounded readable workspace.
- At 540px and below, workspace and topbar padding remain stable.
- At 380px and below, icon buttons retain a stable hit area, account text truncates, and topbar controls do not overlap.

No desktop page is redesigned and no mobile navigation pattern is replaced.

## Testing Strategy

Use test-driven static contracts and one focused utility behavior test:

- H5 tests verify `showErrorToast` options, inline error tokens, disabled selectors, and long-list containment hooks.
- Web tests verify `ErrorNotice` use, the transient theme-switch contract, reduced-motion handling, responsive breakpoints, and list containment hooks.
- Existing async cleanup tests continue to verify failure and abort recovery.
- Run complete Web and H5 unit suites and both production builds.
- Run `git diff --check` and confirm no modified path under API, services, stores, routes, or dependency lock files.
- Run the Impeccable detector once on the changed UI targets after implementation.

## Acceptance Criteria

- Network, permission, invalid-parameter, and timeout feedback follows the same H5/Web visual specification without changing its Chinese content.
- No disabled button shows hover/press movement or an enabled-looking shadow.
- Low-end motion uses transform/opacity paths and respects reduced motion.
- Off-screen long-list entries can skip rendering work where the browser supports CSS containment.
- Dark/light switching has no persistent transition class and no partial surface flash.
- Ultra-wide and 320-380px layouts remain usable without horizontal overlap.
- Mock mode and backend API docking compile and retain their existing configuration paths.
- All frontend tests and builds pass, the changelog is appended, and the final worktree is clean after the implementation commit.
