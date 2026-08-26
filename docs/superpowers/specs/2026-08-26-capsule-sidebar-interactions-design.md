# Capsule + Sidebar Physical Interaction Upgrade

Date: 2026-08-26

## Scope

This iteration changes interaction presentation only. Existing routes, page structure, API adapters, request payloads, stores, mock data, Chinese copy, and business rules remain unchanged. No business page or module is added.

`web-frontend` owns the reusable capsule tag and sidebar interaction surfaces. `resume-miniprogram` keeps its existing H5 pages and adds pointer-aware feedback to the existing selected-role chips; it has no new sidebar business surface.

## Capsule Multi-select Contract

`CapsuleMultiSelect` accepts the existing role option list, selected values, maximum count, and pending state, then emits the same selected-value update used by `ComparisonRolePicker`. It owns only visual selection feedback:

1. Tag press uses `scale(.92)` on press and a 1.04 overshoot before settling at 1 with a spring cubic-bezier.
2. Pointer-down coordinates are written to CSS variables so the ripple starts at the tap/click point and remains clipped by the capsule.
3. Selected tags reveal a check icon with a stroked draw and spring dot entrance; unselect fades and scales it down.
4. Select-all and reset controls use a short horizontal stretch/compress interaction.
5. Selected-count percentage is animated by an inertia/deceleration loop; the progress fill reads the same animated value.
6. Loading renders fixed-size capsule skeletons based on the final tag rhythm, then fades into real tags without changing layout height.

The comparison submit button keeps the existing `submit` event and receives a lightweight particle burst only after a successful comparison. No other tag or button emits particles.

## Sidebar Contract

`WebSidebar` retains the `navigate` event and all existing navigation keys. It adds a mobile drawer state, an Escape/mask close path, a single three-path SVG hamburger morph, collapsible groups with inward swipe-away leave motion, a liquid progress track for workspace completion, and a fixed bottom-sheet layout on narrow screens. The drawer enter animation has an 80ms settle dwell and closes with the reverse easing.

The optional tag hover preview is implemented in the capsule component as a mild 3D flip with an occluded back face. All effects use native CSS transitions/keyframes and Vue event handlers; no animation dependency is introduced.

## H5 Contract

The existing `job-search` selected-role removal button captures the H5 event coordinates (with DOM `currentTarget` fallback), writes the ripple origin variables, and keeps the existing `removeSelectedRole` business path. Existing role text and API calls are untouched.

## Motion and Accessibility

Animation and loading tokens live in `web-frontend/src/styles/base.css` and existing H5 root variables. Motion uses transform/opacity and compositor-friendly properties, includes `prefers-reduced-motion`, preserves focus outlines, and marks pending controls busy/disabled. Skeletons reserve their final block height to prevent layout jitter.

## Verification

- Add source-contract tests for all 12 interactions and the H5 pointer handler.
- Run Web tests/build and H5 unit tests/build.
- Run `git diff --check`, the Impeccable detector, and smoke-check the local Web server and backend health/mock API path.
