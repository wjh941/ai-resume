# Web Visual Reframe Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reframe the independent Web frontend as a bright cobalt-led job-search workspace without changing product capability, requests, routes, mock data, or existing Chinese business copy.

**Architecture:** Retain the Vue 3 view tree and the existing CSS-token layer. Establish semantic light/dark tokens and shell styling first, then add small presentational classes to existing analytical and operational view boundaries. Existing API adapters, emitted events, source-authoritative lists, local checkpoints, loading/pending states, and keyboard guards stay intact.

**Tech Stack:** Vue 3, TypeScript, Vite, Vitest, Lucide Vue, and native CSS custom properties.

## Global Constraints

- Modify only `web-frontend/` and the related documentation under `docs/`; do not touch H5, backend, services, APIs, routers, mocks, fixtures, or lockfiles.
- Preserve all routes, emitted events, request payloads, mock records, Chinese business strings, async state cleanup, and source-array mutation paths.
- Keep the existing CSS-token architecture; add no dependency, third-party UI kit, external asset, decorative gradient, glass panel, or animation library.
- Use warm-white/blue-gray surfaces, graphite text, cobalt as the sole general action color, coral only for attention or destructive emphasis, and semantic success/warning/danger tokens.
- Keep 8px-or-smaller operational radii, focus visibility, reduced motion, disabled/loading/error states, dark mode, progressive lists, wide-table scrolling, and mobile stacked layouts.
- Presentation-only CSS and additive markup hooks use browser visual QA rather than source-text assertions, by explicit user decision. Existing API/domain/workflow tests remain mandatory regression evidence.
- Before handoff run `npm.cmd test -- --reporter=dot`, `npm.cmd run build`, `git diff --check`, and one bounded browser review at 1440px, 1024px, and 390px.

---

## File Map

| File | Responsibility |
| --- | --- |
| `web-frontend/src/styles/base.css` | Semantic palette, shell, records, forms, feedback, dark mode, and responsive rules. |
| `web-frontend/src/components/WebSidebar.vue` | Existing navigation receives non-textual visual hooks only. |
| `web-frontend/src/components/WebTopbar.vue` | Existing utility strip receives non-textual visual hooks only. |
| `web-frontend/src/views/OverviewView.vue` | Existing KPI/action composition receives bounded hierarchy hooks. |
| `web-frontend/src/views/{Career,Assessment,Comparison,Insights,Membership}View.vue` | Existing analytical and entitlement sections receive decision-surface hooks. |
| `web-frontend/src/views/{Resume,ResumeEditor,Jobs,Applications,Evidence,Account}View.vue` | Existing editor, form, and record groups receive workbench hooks. |
| `web-frontend/src/components/{AsyncButton,ErrorNotice,LoadingSpinner,MembershipPackageCard,OrderRow,AssessmentQuestionCard,FutureCapabilityShell,EvidenceForm}.vue` | Shared components consume only presentational selectors already supported by their public contracts. |
| `docs/interaction-upgrade-changelog.md` | Records scope and final verification evidence. |

---

### Task 1: Establish Semantic Cobalt Tokens and a Light Workspace Shell

**Files:**
- Modify: `web-frontend/src/styles/base.css`
- Modify: `web-frontend/src/components/WebSidebar.vue`
- Modify: `web-frontend/src/components/WebTopbar.vue`

**Interfaces:**
- Consumes: existing CSS variable consumers, `WorkspaceView`, `SessionUser`, and existing navigation/logout/theme events unchanged.
- Produces: `--primary`, `--primary-strong`, `--primary-tint`, `--accent`, `--success`, and `--warning` tokens in both themes. No TypeScript public interface changes.

- [ ] **Step 1: Capture the current shell baseline in the browser**

Use the existing Vite server at `http://127.0.0.1:5174/` and record the
current shell at 1440px and 390px in both themes. The baseline must cover
sidebar, topbar, keyboard focus, disabled button, and a view transition. This
is visual reference only; no CSS source-text test is added.

- [ ] **Step 2: Implement the semantic light/dark palette**

In the existing root token blocks, retain all current motion/loading/size
variables and add this semantic baseline:

```css
:root {
  --ink: #171a24;
  --muted: #667085;
  --line: #dfe5ef;
  --canvas: #f6f8fc;
  --surface: #ffffff;
  --surface-raised: #ffffff;
  --surface-muted: #f0f4fa;
  --primary: #2563eb;
  --primary-strong: #1d4ed8;
  --primary-tint: #e8efff;
  --accent: #e96b4c;
  --success: #16866a;
  --warning: #b7791f;
  --danger: #bf3f3a;
}

:root[data-theme="dark"] {
  --ink: #edf2ff;
  --muted: #aab6cb;
  --line: #2b3850;
  --canvas: #111827;
  --surface: #172033;
  --surface-raised: #1c2940;
  --surface-muted: #24314a;
  --primary: #7da2ff;
  --primary-strong: #a9c1ff;
  --primary-tint: #223966;
  --accent: #ff9a82;
  --success: #71d3b5;
  --warning: #f0c66a;
  --danger: #ffaaa5;
}
```

Update existing action, focus, selected-navigation, checkbox, active-tab,
spinner, and success selectors to consume semantic tokens. Keep existing CSS
class names and `data-theme` behavior.

- [ ] **Step 3: Reframe shell presentation with existing markup**

Use the current desktop grid and mobile behavior. Make `.web-sidebar` a light
surface with a right separator; make the active item cobalt-tinted with an
inset rail; make `.web-topbar` a quiet utility strip. The core rules should
read as follows:

```css
.web-sidebar { color: var(--ink); border-right: 1px solid var(--line); background: var(--surface); }
.brand-symbol { color: #fff; background: var(--primary); }
.navigation-item { color: var(--muted); }
.navigation-item:hover { color: var(--ink); background: var(--surface-muted); }
.navigation-item.is-active { color: var(--primary-strong); background: var(--primary-tint); box-shadow: inset 1px 0 0 var(--primary); }
.web-topbar { background: color-mix(in srgb, var(--surface) 94%, transparent); }
```

Add an extra class only if a current element cannot be selected. Do not alter
navigation labels, order, click handlers, emits, titles, or ARIA attributes.

- [ ] **Step 4: Check the shell in the browser**

Start the existing Vite server and inspect light/dark shell behavior at 1440px,
1024px, and 390px. Confirm that navigation, account utilities, theme toggle,
and logout remain visible/clickable; the transition produces no white or old
forest-green flash.

- [ ] **Step 5: Commit Task 1**

```powershell
git add web-frontend/src/styles/base.css web-frontend/src/components/WebSidebar.vue web-frontend/src/components/WebTopbar.vue
git commit -m "style(web): establish bright workspace shell"
```

---

### Task 2: Clarify Overview, Analysis, Membership, and Shared Feedback Surfaces

**Files:**
- Modify: `web-frontend/src/styles/base.css`
- Modify: `web-frontend/src/views/OverviewView.vue`
- Modify: `web-frontend/src/views/CareerView.vue`
- Modify: `web-frontend/src/views/AssessmentView.vue`
- Modify: `web-frontend/src/views/ComparisonView.vue`
- Modify: `web-frontend/src/views/InsightsView.vue`
- Modify: `web-frontend/src/views/MembershipView.vue`
- Modify: `web-frontend/src/components/MembershipPackageCard.vue`
- Modify: `web-frontend/src/components/OrderRow.vue`
- Modify: `web-frontend/src/components/AsyncButton.vue`
- Modify: `web-frontend/src/components/ErrorNotice.vue`
- Modify: `web-frontend/src/components/LoadingSpinner.vue`
- Modify: `web-frontend/src/components/AssessmentQuestionCard.vue`
- Modify: `web-frontend/src/components/FutureCapabilityShell.vue`

**Interfaces:**
- Consumes: Task 1 tokens and each view's existing refs, request functions,
  props, events, loading branches, result branches, and membership workflows.
- Produces: CSS-only `decision-surface` hooks; no new state, prop, event,
  route, request, or membership capability.

- [ ] **Step 1: Add only additive hooks at existing decision boundaries**

Use `decision-surface` on existing panels/results, never on a new wrapper or
new branch:

```vue
<section class="assessment-panel decision-surface">
  <!-- existing question content and submit handler unchanged -->
</section>
<section v-if="result" class="comparison-result decision-surface">
  <!-- existing result content and navigation action unchanged -->
</section>
```

Add the same class to existing career, insight, and membership decision
containers. Do not change conditions, text, imports, requests, emits, or
membership-gating behavior.

- [ ] **Step 2: Style only overview as an asymmetric KPI composition**

Keep the existing three values/skeletons and style them without a new data
source or chart:

```css
.overview-strip { grid-template-columns: minmax(0, 1.4fr) minmax(180px, .8fr) minmax(180px, .8fr); gap: 12px; background: transparent; }
.metric-block { border: 1px solid var(--line); border-radius: var(--radius); box-shadow: none; }
.metric-block:first-child { color: var(--primary-strong); background: var(--primary-tint); }
.metric-block:first-child .metric-icon { color: #fff; background: var(--primary); }
.decision-surface { border-top-color: color-mix(in srgb, var(--primary) 30%, var(--line)); }
```

At the current mobile breakpoint restore a one-column metric stack. Do not
apply this asymmetry to lists, forms, or every analytical section.

- [ ] **Step 3: Apply semantic analysis, membership, and feedback styling**

Keep question invalid state on `--danger`; make score and selected report-mode
states cobalt; make `.membership-package.is-current` cobalt-tinted; keep other
packages neutral. Orders remain dense rows. Style existing `aria-busy`,
disabled, error, success, spinner, and empty-state classes with semantic
tokens. Keep all existing loading cleanup, error roles, ARIA labels, and
component public props/emits unchanged. Keep `FutureCapabilityShell` neutral
and dashed without adding text, links, routes, or actions.

- [ ] **Step 4: Run existing focused workflows and inspect decision surfaces**

Run:

```powershell
cd web-frontend
npm.cmd test -- src/tests/assessment-workflow.spec.ts src/tests/comparison-workflow.spec.ts src/tests/membership-workflow.spec.ts src/tests/interaction-state.spec.ts --reporter=dot
```

Expected: PASS. Inspect overview, career, assessment, comparison, insights,
and membership in light/dark modes. Confirm report-mode, submit, purchase,
loading, error, and empty branches still work without clipped text.

- [ ] **Step 5: Commit Task 2**

```powershell
git add web-frontend/src/styles/base.css web-frontend/src/views/OverviewView.vue web-frontend/src/views/CareerView.vue web-frontend/src/views/AssessmentView.vue web-frontend/src/views/ComparisonView.vue web-frontend/src/views/InsightsView.vue web-frontend/src/views/MembershipView.vue web-frontend/src/components/MembershipPackageCard.vue web-frontend/src/components/OrderRow.vue web-frontend/src/components/AsyncButton.vue web-frontend/src/components/ErrorNotice.vue web-frontend/src/components/LoadingSpinner.vue web-frontend/src/components/AssessmentQuestionCard.vue web-frontend/src/components/FutureCapabilityShell.vue
git commit -m "style(web): clarify decision and membership surfaces"
```

---

### Task 3: Refine Operational Editors, Forms, Records, and Account Tools

**Files:**
- Modify: `web-frontend/src/styles/base.css`
- Modify: `web-frontend/src/views/ResumeView.vue`
- Modify: `web-frontend/src/views/ResumeEditorView.vue`
- Modify: `web-frontend/src/views/JobsView.vue`
- Modify: `web-frontend/src/views/ApplicationsView.vue`
- Modify: `web-frontend/src/views/EvidenceView.vue`
- Modify: `web-frontend/src/views/AccountView.vue`
- Modify: `web-frontend/src/components/EvidenceForm.vue`

**Interfaces:**
- Consumes: Task 1 tokens and existing form validation, local checkpoint,
  keyboard shortcut, progressive-list, wide-table, and source-array behavior.
- Produces: CSS-only `workbench-form` and `record-surface` hooks. No request
  or event contract changes.

- [ ] **Step 1: Attach hooks only to existing form and record boundaries**

Use additive markup such as:

```vue
<form class="editor-form workbench-form" novalidate @submit.prevent="save">
  <!-- existing fields, validation, and save path unchanged -->
</form>
<div v-else-if="items.length" class="application-table record-surface">
  <!-- existing renderedApplications loop unchanged -->
</div>
```

Apply the corresponding hooks to existing resume, job, evidence, and account
containers. Do not move fields, change IDs, remove ARIA bindings, alter
`@submit`, modify pending guards, or touch checkpoint/validation functions.

- [ ] **Step 2: Implement flat scan-friendly operational styling**

Add CSS shaped like:

```css
.workbench-form { padding: 22px; border: 0; border-radius: var(--radius); background: var(--surface); box-shadow: 0 10px 28px rgb(22 34 56 / 7%); }
.workbench-form :is(input, select, textarea):focus { border-color: var(--primary); box-shadow: 0 0 0 3px color-mix(in srgb, var(--primary) 18%, transparent); }
.record-surface { border: 1px solid var(--line); border-radius: var(--radius); background: var(--surface); box-shadow: none; }
.record-row:hover, .task-row:hover, .application-row:hover { background: var(--primary-tint); }
.status-tag, .record-tag { color: var(--primary-strong); background: var(--primary-tint); }
```

Keep `content-visibility`, intrinsic sizes, `application-row` minimum width,
horizontal scroll, and the existing `max-width: 840px` stacked table rules.
Each surface uses one elevation cue: soft shadow for an editor/form tool and a
fine border for records. Danger/error/disabled states stay semantic exceptions
and do not become blue.

- [ ] **Step 3: Reduce nested-panel weight without changing tools**

Use separators and one elevated tool surface for the existing evidence form,
suggestion/readiness sections, and account privacy actions. Keep the existing
evidence two-column layout, selects, buttons, and handler functions. Keep the
account consent/export/deletion operations and ARIA behavior unchanged.

- [ ] **Step 4: Run focused workflows and inspect key paths**

Run:

```powershell
cd web-frontend
npm.cmd test -- src/tests/resume-workflow.spec.ts src/tests/resume-editor-orchestration.spec.ts src/tests/applications-workflow.spec.ts src/tests/evidence-workflow.spec.ts --reporter=dot
```

Expected: PASS. In the browser verify editor save/error focus, job query error,
application create/edit/timeline, evidence create/delete/suggestions, and
account destructive action states at all required widths.

- [ ] **Step 5: Commit Task 3**

```powershell
git add web-frontend/src/styles/base.css web-frontend/src/views/ResumeView.vue web-frontend/src/views/ResumeEditorView.vue web-frontend/src/views/JobsView.vue web-frontend/src/views/ApplicationsView.vue web-frontend/src/views/EvidenceView.vue web-frontend/src/views/AccountView.vue web-frontend/src/components/EvidenceForm.vue
git commit -m "style(web): refine operational workbench surfaces"
```

---

### Task 4: Verify Responsive Polish, Record the Reframe, and Audit Scope

**Files:**
- Modify: `docs/interaction-upgrade-changelog.md`

**Interfaces:**
- Consumes: semantic tokens and additive classes from Tasks 1-3.
- Produces: verification evidence and changelog documentation only; no production capability.

- [ ] **Step 1: Run the complete Web regression suite**

Run:

```powershell
cd web-frontend
npm.cmd test -- --reporter=dot
```

Expected: all API, domain, workflow, interaction, checkpoint, keyboard, and
tests pass.

- [ ] **Step 2: Run the production build**

Run:

```powershell
cd web-frontend
npm.cmd run build
```

Expected: Vite exits 0 without adding a new dependency.

- [ ] **Step 3: Run one bounded visual QA batch**

Inspect the local Web app using the existing session/mock path:

```text
1440px light: shell, overview, application wide table, membership.
1024px dark: editor, evidence workspace, comparison, insights.
390px light and dark: navigation, action clusters, forms, empty states,
assessment questions, application stacked rows, disabled and loading actions.
```

Fix the complete observed batch once with existing CSS/classes, then repeat
this exact checklist once. Confirm no clipped text, overlapping controls,
body horizontal overflow, low-contrast focus/disabled state, layout jitter,
or theme flash.

- [ ] **Step 4: Audit scope and append verified changelog evidence**

Run:

```powershell
git diff --check
git diff --name-only 98cb6c6..HEAD
git status --short
```

Confirm changed paths are limited to `web-frontend/` and this iteration's
documentation under `docs/`; existing view imports still point to the
original domain/API/workflow modules; and no Chinese business string or mock
fixture changed. Append a dated entry
to `docs/interaction-upgrade-changelog.md` recording the cobalt/warm-white
reframe, charcoal/navy dark mode, shell/KPI/record hierarchy, exact Web test
count, build result, visual QA widths/themes, and frontend-only path audit.

- [ ] **Step 5: Commit Task 4**

```powershell
git add docs/interaction-upgrade-changelog.md
git commit -m "docs: record web visual reframe"
```

---

## Plan Self-Review

### Spec coverage

- Semantic warm-white, cobalt, coral, graphite, and charcoal/navy dark mode: Task 1.
- Light navigation rail and quiet utility topbar: Task 1.
- Bounded KPI/decision hierarchy inspired by dashboard composition rather than copied UI: Task 2.
- Membership, feedback, loading, empty, disabled, and analytical state hierarchy: Task 2.
- Editor, jobs, applications, evidence, account, long-list, and wide-table polish: Task 3.
- Responsive visual QA, full test/build, scope audit, and changelog: Task 4.
- Business/API/H5/mock/Chinese-copy/dependency constraints: Global Constraints and Task 4 audit.

### Placeholder scan

Every task has exact files, implementation boundaries, verification commands, browser acceptance criteria, and a commit command. The user explicitly chose real-browser visual QA over source-text presentation tests; existing behavioral suites continue to protect the unchanged business layer.

### Type and contract consistency

`decision-surface`, `workbench-form`, and `record-surface` are CSS-only class
names introduced in Tasks 2-3. No TypeScript signatures, props, events,
routes, or API types change.
