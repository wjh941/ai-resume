# Job Opportunity Result Depth Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans (inline execution is authorized for this session). Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the existing Web 岗位机会 response materially more precise and actionable without changing its API or business workflow.

**Architecture:** Keep `JobsView` as the result owner. Add small typed computed projections for complete returned fields and deterministic interview/evidence prompts, then render them in a progressive-disclosure layout using existing `ExpandableText`, `AsyncButton`, and report-tier fields. Extend only the existing Web interaction contract tests and changelog.

**Tech Stack:** Vue 3 + TypeScript, existing CSS tokens/components, Vitest source-contract tests, FastAPI test suite for API compatibility.

## Global Constraints

- Existing `/api/job/query` path, request payload, response field semantics, routes, mock data, and business handlers remain unchanged.
- Do not invent real-time salary, vacancy, hiring probability, candidate facts, or external evidence.
- Preserve original Chinese labels and existing actions; added guidance must be deterministic and clearly scoped as preparation guidance.
- Keep responsive layout, loading/error handling, accessibility semantics, and professional-member gating intact.

---

### Task 1: Lock the Depth Contract With Tests

**Files:**
- Modify: `web-frontend/src/tests/interaction.spec.ts`

- [ ] Add source assertions that `JobsView` renders hard requirements, required/bonus skills, full responsibilities, career route, report evidence/actions, and a verification notice.
- [ ] Assert that arbitrary `slice(0, 4)`/`slice(0, 8)` truncation is absent from the job result.
- [ ] Run the focused Web interaction test and confirm the new assertions fail before implementation.

### Task 2: Add Typed Result Projections

**Files:**
- Modify: `web-frontend/src/views/JobsView.vue`

- [ ] Extend the local `JobResult.report` type with existing optional `mode`, `evidence`, and `upgrade_notice` fields.
- [ ] Add computed de-duplicated skills, full returned lists, deterministic interview checks, and stable fallback text for older responses.
- [ ] Keep `queryRole`, `favorite`, loading guards, API URL, and payload unchanged.

### Task 3: Render a Professional, Actionable Result

**Files:**
- Modify: `web-frontend/src/views/JobsView.vue`
- Modify: `web-frontend/src/styles/base.css`

- [ ] Replace the truncated three-column result with a hierarchy of role verdict, decision grid, salary verification, career route, interview checklist, and report actions/evidence.
- [ ] Use existing `ExpandableText`/`details` disclosure for long lists and provide explicit empty-state text for absent optional arrays.
- [ ] Keep report mode/upgrade notice visible and distinguish structured reference data from live market facts.
- [ ] Add responsive grid/list rules using existing tokens; avoid layout-driving animation and preserve reduced-motion behavior.

### Task 4: Verify, Document, and Integrate

**Files:**
- Modify: `docs/interaction-upgrade-changelog.md`

- [ ] Run Web full tests/build, backend job-query tests, `git diff --check`, detector over changed UI files, and local Web/backend HTTP smoke checks.
- [ ] Review the diff for unchanged API paths/payloads and no new business modules.
- [ ] Append the result-depth entry, commit, and push the branch.
