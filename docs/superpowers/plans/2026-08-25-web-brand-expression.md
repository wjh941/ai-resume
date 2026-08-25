# Web Brand Expression Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give the Web workspace a stronger, recognisable 求职成长 brand expression while preserving all business behavior.

**Architecture:** Reuse the existing semantic CSS token system and presentational Vue containers. Add narrowly scoped `growth-stage` and `decision-emphasis` hooks only to existing sections, then style them through `base.css`; no state, API, route, or event interface changes are permitted.

**Tech Stack:** Vue 3, TypeScript, Tailwind-compatible project CSS architecture, native CSS transitions, Vitest, Vite.

## Global Constraints

- Change only `web-frontend/`, `docs/interaction-upgrade-changelog.md`, and this plan's supporting docs.
- Preserve all Chinese UI text, route keys, requests, APIs, mock data, state branches, props, emits, handlers, and keyboard behavior.
- Add no dependencies, pages, modules, charts, APIs, routes, gradients, glass effects, or nested cards.
- Keep records border-only and tools/forms shadow-only; semantic danger, warning, disabled, and error states do not become cobalt.
- Keep dark mode, 390px mobile, ultra-wide desktop, keyboard focus, 44px shell targets, reduced motion, loading cleanup, and horizontal table scrolling working.
- Use browser visual QA for presentation behavior; retain existing workflow tests for business regression coverage.

---

### Task 1: Shape the Overview Growth Narrative

**Files:**
- Modify: `web-frontend/src/styles/base.css`
- Modify: `web-frontend/src/views/OverviewView.vue`

**Interfaces:**
- Consumes: existing `overview`, `loading`, `error`, `refresh`, KPI values, and existing navigation actions.
- Produces: additive `growth-stage` and `growth-route` class hooks; no new reactive state or event.

- [ ] **Step 1: Add hooks to existing stage and action boundaries**

Add classes only to the existing overview heading/action route elements:

```vue
<div class="view-heading growth-stage">
  <!-- existing heading and refresh action unchanged -->
</div>
<section class="action-route growth-route">
  <!-- existing action content and navigation unchanged -->
</section>
```

- [ ] **Step 2: Implement the visual treatment in `base.css`**

Use existing tokens to make the stage marker and sequential action route clear:

```css
.growth-stage { position: relative; padding-bottom: 6px; }
.growth-stage::after { width: 56px; height: 2px; content: ""; background: var(--primary); }
.growth-route { border-color: color-mix(in srgb, var(--primary) 26%, var(--line)); background: var(--surface-muted); }
```

Use dividers, typography, and existing primary tint only. Do not change the current asymmetric KPI grid or its skeleton dimensions.

- [ ] **Step 3: Browser verify the existing overview states**

Run the Web app and inspect desktop light/dark plus 390px. Verify KPIs, skeleton, error/retry, refresh loading, and existing action buttons retain their branches and do not cause overflow.

- [ ] **Step 4: Run focused regression tests**

Run: `npm.cmd test -- src/tests/interaction-state.spec.ts --reporter=dot` in `web-frontend`.

Expected: PASS without changing the test source.

- [ ] **Step 5: Commit**

```powershell
git add web-frontend/src/styles/base.css web-frontend/src/views/OverviewView.vue
git commit -m "style(web): add overview growth narrative"
```

### Task 2: Emphasize Editor Chapters and Analysis Decisions

**Files:**
- Modify: `web-frontend/src/styles/base.css`
- Modify: `web-frontend/src/views/ResumeEditorView.vue`
- Modify: `web-frontend/src/views/CareerView.vue`
- Modify: `web-frontend/src/views/AssessmentView.vue`
- Modify: `web-frontend/src/views/ComparisonView.vue`
- Modify: `web-frontend/src/views/InsightsView.vue`

**Interfaces:**
- Consumes: existing editor save/checkpoint flow, career tasks, assessment result, comparison result, insight report, loading/error branches.
- Produces: additive `chapter-stage` and `decision-emphasis` classes only.

- [ ] **Step 1: Attach additive existing-result hooks**

Apply the classes to existing section headings/results without changing contents:

```vue
<section class="editor-section chapter-stage">
  <!-- existing inputs and actions unchanged -->
</section>
<section v-if="result" class="comparison-result decision-surface decision-emphasis">
  <!-- existing result and action unchanged -->
</section>
```

- [ ] **Step 2: Style hierarchy without changing tool elevation rules**

Create chapter dividers and a restrained cobalt result emphasis using the current CSS variables. Do not add shadows to `.record-surface`, `.comparison-card`, or list rows. Keep input focus outlines and invalid states unchanged.

- [ ] **Step 3: Verify business workflows**

Run in `web-frontend`:

```powershell
npm.cmd test -- src/tests/resume-editor-orchestration.spec.ts src/tests/assessment-workflow.spec.ts src/tests/comparison-workflow.spec.ts --reporter=dot
```

Expected: PASS without editing tests.

- [ ] **Step 4: Browser inspect editor and results**

Inspect editor save/error focus, career task interaction, assessment invalid/result state, comparison result/gated branch, and insights result in light/dark. Confirm long text, buttons, and mobile layout remain uncropped.

- [ ] **Step 5: Commit**

```powershell
git add web-frontend/src/styles/base.css web-frontend/src/views/ResumeEditorView.vue web-frontend/src/views/CareerView.vue web-frontend/src/views/AssessmentView.vue web-frontend/src/views/ComparisonView.vue web-frontend/src/views/InsightsView.vue
git commit -m "style(web): emphasize growth decisions"
```

### Task 3: Final QA, Changelog, and Scope Audit

**Files:**
- Modify: `docs/interaction-upgrade-changelog.md`
- Verify: `web-frontend/src/styles/base.css` and all Task 1-2 files

**Interfaces:**
- Consumes: completed presentational commits and existing Web test/build commands.
- Produces: a documented, verified iteration with no public interface change.

- [x] **Step 1: Add a concise changelog entry**

Document the overview growth narrative, editor/decision emphasis, retained operational record treatment, browser QA coverage, and no-business-change boundary. Do not rewrite older entries.

- [x] **Step 2: Run full Web verification**

```powershell
cd web-frontend
npm.cmd test
npm.cmd run build
```

Expected: all tests and production build pass.

- [x] **Step 3: Perform final browser and scope checks**

Inspect 1440px light/dark, 1920px light/dark, and 390px mobile; exercise focus, disabled, reduced-motion, overview, editor, decision result, record list, and theme transition. Run `git diff --check` and audit the final range for out-of-scope H5/backend/API/router/mock/lockfile changes.

- [x] **Step 4: Commit**

```powershell
git add docs/interaction-upgrade-changelog.md
git commit -m "docs: record web brand expression iteration"
```
