# Web Workbench Visual Depth Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make the existing Web workbench feel layered, refined, and comfortable through a shared visual system without changing business behavior.

**Architecture:** Keep all presentation rules in `web-frontend/src/styles/base.css`, reusing the existing semantic tokens and component class hooks. Add only a focused source contract in the existing Web interaction suite; Vue views, APIs, routes, mock data, and H5 remain untouched.

**Tech Stack:** Vue 3, Vite, native CSS custom properties/transitions, Vitest.

## Global Constraints

- Keep every existing route, view, API call, request payload, mock dataset, Chinese UI string, loading/error state, and business workflow unchanged.
- Keep the H5 implementation untouched.
- Use native CSS transitions and existing Vue/Lucide components; add no UI or animation dependency.
- Hover-only rules must not run on coarse pointers; reduced-motion users keep the same hierarchy with transitions disabled.

---

### Task 1: Lock the visual contract

**Files:**
- Modify: `web-frontend/src/tests/interaction.spec.ts`
- Test: `web-frontend/src/tests/interaction.spec.ts`

**Interfaces:**
- Consumes: existing `base.css` source contract patterns.
- Produces: one failing test that requires the shared hover token and scoped surface selectors.

- [x] **Step 1: Write the failing test**

Add a test that reads `../styles/base.css` and expects `--shadow-hover`, a hover/pointer media query, selectors for metric/comparison/membership/assessment surfaces, the `:not(.is-invalid)` guard, and `translateY(-2px)`.

- [x] **Step 2: Run the focused test and confirm it fails**

Run `npm.cmd test -- src/tests/interaction.spec.ts` from `web-frontend`.
Expected: the new contract fails because the shared token/selectors do not exist yet.

### Task 2: Implement the layered workbench surface system

**Files:**
- Modify: `web-frontend/src/styles/base.css`

**Interfaces:**
- Consumes: existing semantic tokens and classes `.metric-block`, `.comparison-card`, `.membership-package`, `.assessment-question`, `.web-sidebar`, and `.view-heading`.
- Produces: light/dark hover elevation, balanced heading wrapping, and shell depth with no markup or behavior changes.

- [x] **Step 1: Add light and dark `--shadow-hover` values beside existing shadow tokens.**
- [x] **Step 2: Add a subtle sidebar shadow and `text-wrap: balance` for view headings.**
- [x] **Step 3: Add pointer-only transitions and hover lift for valid high-value surfaces; keep invalid assessment cards excluded.**
- [x] **Step 4: Extend the reduced-motion block to disable the new surface transitions.**
- [x] **Step 5: Re-run `npm.cmd test -- src/tests/interaction.spec.ts` and confirm the contract passes.**

### Task 3: Document, verify, and ship

**Files:**
- Modify: `docs/interaction-upgrade-changelog.md`

**Interfaces:**
- Consumes: the completed visual-system changes and verification output.
- Produces: a dated changelog entry documenting scope and preserved behavior.

- [x] **Step 1: Append the Web workspace visual polish entry without changing product copy.**
- [x] **Step 2: Run `npm.cmd test` and `npm.cmd run build` from `web-frontend`.**
- [x] **Step 3: Run `npm.cmd run test:unit` and `npm.cmd run build:h5` from `resume-miniprogram`.**
- [x] **Step 4: Run `git diff --check` and the Impeccable detector over changed UI targets.**
- [x] **Step 5: Start Web on an available port and verify the served title/script identify this project.**
- [x] **Step 6: Commit the implementation and changelog, push the branch, and deploy the Web frontend to Vercel production.**
