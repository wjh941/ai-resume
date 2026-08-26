# Web Workbench Navigation Composition Implementation Plan

**Goal:** Clarify existing Web modules through grouped navigation and make the
missing career-profile response actionable without changing business behavior.

**Architecture:** Keep destination keys and API adapters unchanged. Add
presentation metadata in `WebSidebar.vue`, shared group styling in
`base.css`, and a narrow missing-profile branch in `ComparisonView.vue`.

## Global Constraints

- Preserve routes, API contracts, mock data, Chinese copy, and existing modules.
- Do not add a career-profile editor or any new business capability.
- Keep H5 untouched and use native CSS only.

### Task 1: Lock the presentation contract

**Files:** `web-frontend/src/tests/interaction.spec.ts`

- [x] Add failing source checks for grouped navigation and the profile-missing
  branch.
- [x] Run the focused test and confirm it fails before implementation.

### Task 2: Implement grouped navigation and recoverable profile state

**Files:** `web-frontend/src/components/WebSidebar.vue`,
`web-frontend/src/views/ComparisonView.vue`,
`web-frontend/src/styles/base.css`

- [x] Group existing buttons by preparation, decisions, execution, and
  review/account while preserving every key and label.
- [x] Detect the existing 404 `Career profile not found` contract and show an
  actionable empty state linking to the existing career-planning view.
- [x] Style groups responsively; keep mobile navigation horizontal and avoid
  extra animation.
- [x] Restore deterministic development-only job intelligence when local AI
  credentials are absent, preserving the existing `/api/job/query` contract.

### Task 3: Document, verify, and ship

**Files:** `docs/interaction-upgrade-changelog.md`

- [x] Append this iteration's navigation and missing-profile changes.
- [x] Run Web/H5 tests and builds, `git diff --check`, and Impeccable checks.
- [x] Verify local Web and Vercel production responses.
- [x] Commit and push the branch.
