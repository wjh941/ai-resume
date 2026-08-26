# Capsule + Sidebar Physical Interaction Upgrade Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add all twelve requested physical-feeling interactions to the existing Web capsule/sidebar surfaces and the existing H5 selected-role chips without changing business behavior.

**Architecture:** A reusable `CapsuleMultiSelect` owns tag feedback, inertia progress, and matching skeleton geometry. `ComparisonRolePicker` keeps the current selection/submit contract and supplies the capsule. `WebSidebar` owns drawer, morph, collapsible-group, and liquid-progress presentation. H5 adds a coordinate-capture wrapper around its existing removal handler. Shared CSS variables and reduced-motion rules remain centralized in the existing base/root styles.

**Tech Stack:** Vue 3 + TypeScript, native CSS transitions/keyframes, existing Lucide icons, Vitest source-contract tests, Vite builds.

## Global Constraints

- Existing API interfaces, routes, page structure, stores, mock data, Chinese text, and business logic are unchanged.
- No new business pages or modules are added.
- Native CSS + lightweight Vue/DOM handlers only; no animation dependency.
- Particle burst is limited to the existing comparison submit action.
- Pending controls remain disabled and clear state on resolve/rejection/cancellation through existing handlers.
- All new effects support `prefers-reduced-motion` and avoid layout-driving animation.

---

### Task 1: Lock Interaction Contracts With Tests

**Files:**
- Modify: `web-frontend/src/tests/interaction.spec.ts`
- Modify: `resume-miniprogram/src/tests/interaction.spec.ts`

- [ ] Add failing source-contract assertions for `CapsuleMultiSelect.vue` covering spring press, pointer ripple, check draw, elastic controls, inertia percentage/progress, fixed skeletons, optional flip, and submit particle markup.
- [ ] Add failing assertions for `WebSidebar.vue` covering drawer dwell/reverse, single SVG morph paths, group swipe transition, liquid progress, Escape/mask close.
- [ ] Add a failing H5 assertion for coordinate capture and the role-chip ripple/settle classes.
- [ ] Run focused tests and confirm they fail because the new selectors do not exist.

### Task 2: Build the Reusable Web Capsule

**Files:**
- Create: `web-frontend/src/components/CapsuleMultiSelect.vue`
- Modify: `web-frontend/src/components/ComparisonRolePicker.vue`
- Modify: `web-frontend/src/views/ComparisonView.vue`
- Modify: `web-frontend/src/styles/base.css`

- [ ] Implement props/emits that preserve `ComparisonRolePicker`'s selected-value and submit semantics, using `toggleComparisonRole` for the existing max-four rule.
- [ ] Capture pointer coordinates on pointer-down, trigger per-tag settle classes, render checkmark SVG/dot state, and expose busy/pressed accessibility state.
- [ ] Add select-all/reset elastic controls without changing the parent API; controls mutate only the existing selected role array.
- [ ] Animate the selected percentage and progress width from one inertia value with requestAnimationFrame cleanup on unmount.
- [ ] Render fixed-size capsule skeletons while loading; add optional flip back-face hint.
- [ ] Add the single comparison-submit particle burst and success check state; keep it scoped to the existing button.
- [ ] Run the Web interaction tests and TypeScript/build checks.

### Task 3: Upgrade the Web Sidebar Surface

**Files:**
- Modify: `web-frontend/src/components/WebSidebar.vue`
- Modify: `web-frontend/src/styles/base.css`

- [ ] Add mobile drawer state with mask click and Escape close while retaining every existing `navigate` emission.
- [ ] Replace icon swapping with one SVG containing three morphing line paths and an accessible label.
- [ ] Add collapsible group controls and inward swipe-away leave transitions while keeping underlying groups in document flow.
- [ ] Add liquid workspace progress track and mobile fixed bottom-sheet layout with an 80ms settle dwell.
- [ ] Add desktop/mobile responsive rules, stable z-index/focus behavior, and reduced-motion fallbacks.
- [ ] Run sidebar-focused tests and Web build.

### Task 4: Add Pointer-aware H5 Chip Feedback

**Files:**
- Modify: `resume-miniprogram/src/pages/job-search/index.vue`
- Modify: `resume-miniprogram/src/App.vue`

- [ ] Wrap the existing role removal handler with coordinate capture using H5 `detail.x/y` and DOM rect fallback, while keeping removal/result cleanup unchanged.
- [ ] Bind ripple origin and settle classes to existing role chips and add spring/ripple/check CSS using root tokens.
- [ ] Verify H5 tests/build and confirm no new page/module files were introduced.

### Task 5: Document, Verify, and Integrate

**Files:**
- Modify: `docs/interaction-upgrade-changelog.md`

- [ ] Record all twelve interactions and their exact component scope, including the optional flip and H5 coordinate wrapper.
- [ ] Run Web tests/build, H5 tests/build, backend health/mock smoke checks, `git diff --check`, and Impeccable detector.
- [ ] Review the diff for API/page/business changes, then commit and push the verified iteration.
