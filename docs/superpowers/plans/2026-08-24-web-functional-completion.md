# Web Functional Completion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (- [ ]) syntax for tracking.

**Goal:** Complete the independent Web workbench and add the existing backend-backed evidence, membership/order, career assessment, and job comparison workflows without changing H5 or backend contracts.

**Architecture:** Keep App.vue as the authenticated Web shell and WebSidebar as the navigation source. Add typed domain adapters under web-frontend/src/lib, then build view-local state and presentational components on top of requestApi, AsyncButton, LoadingSpinner, and the existing transition/CSS token system. Each vertical slice owns its pending/error/empty state and updates local data only after a successful API response.

**Tech Stack:** Vue 3 script setup, TypeScript, Vite, Vitest, lucide-vue-next, native CSS transitions, existing FastAPI JSON envelopes.

## Global Constraints

- Modify web-frontend only; resume-miniprogram H5 pages, routes, API behavior, and tests remain unchanged.
- Preserve existing API URLs, request methods, payload field names, response shapes, auth/session behavior, and Chinese copy.
- Do not add backend endpoints, real payment provider integration, external job scraping, or mock fallback data.
- Use existing requestApi, AsyncButton, LoadingSpinner, transition names, and CSS variables; do not add an animation library.
- Every async mutation clears its pending state in finally, including rejected, aborted, and expired requests.
- Keep desktop density and make new forms/lists collapse to one column on narrow screens without layout jumps.

---

### Task 1: Add Typed Web Domain Adapters

**Files:**
- Create: web-frontend/src/lib/drafts.ts
- Create: web-frontend/src/lib/applications.ts
- Create: web-frontend/src/lib/evidence.ts
- Create: web-frontend/src/lib/membership.ts
- Create: web-frontend/src/lib/assessment.ts
- Create: web-frontend/src/lib/career.ts
- Test: web-frontend/src/tests/domain-api.spec.ts

**Interfaces:**
- Each adapter imports requestApi from src/lib/api.ts and exports camelCase domain types plus functions.
- drafts.ts exports DraftRecord { id, jobTitle, templateId, resume, jobIntelligence, createdAt, updatedAt }, ResumePayload, and DraftSaveInput.
- applications.ts exports ApplicationRecord, ApplicationInput, ApplicationStatus, ApplicationTimelineEvent, and ApplicationFilters.
- evidence.ts exports EvidenceRecord, EvidenceDraft, EvidenceSuggestion, and ResumeReadinessReport.
- membership.ts exports VipStatus, MembershipPackage, and MembershipOrder.
- assessment.ts exports AssessmentQuestion, AssessmentQuestionSet, SavedAssessment, and AssessmentReport.
- career.ts exports CareerRecommendation, CareerTaskRecord, and CareerComparisonResponse.
- drafts.ts: listDrafts(), getDraft(id), saveDraft(input), copyDraft(id), deleteDraft(id).
- applications.ts: listApplications(filters?), saveApplication(input), listTimeline(id), addTimelineEvent(id, input), saveReminder(id, reminderAt), deleteApplication(id).
- evidence.ts: listEvidence(), saveEvidence(input), deleteEvidence(id), getEvidenceSuggestions(roleName), checkResumeReadiness(resume).
- membership.ts: getVipStatus(), listMembershipPackages(), createMembershipOrder(packageType, autoRenew), completeDemoPayment(orderId), listOrders().
- assessment.ts: getAssessmentQuestions(), loadAssessment(), submitAssessment(answers, reportMode).
- career.ts: loadCareerRecommendations(): Promise<CareerRecommendationResponse>, compareRoles(roleNames: string[]): Promise<CareerComparisonResponse>, listCareerTasks(planId: string): Promise<CareerTaskRecord[]>, saveCareerTask(input): Promise<CareerTaskRecord>, updateCareerTask(taskId, input): Promise<CareerTaskRecord>, and deleteCareerTask(taskId): Promise<void>.

- [ ] **Step 1: Write the failing request-mapping tests**

Mock globalThis.fetch, call one representative function per domain, and assert the exact URL, method, JSON payload, and mapped camelCase result. Include a rejected Response assertion for ApiRequestError propagation.

~~~ts
it("maps evidence list", async () => {
  const fetchMock = vi.fn().mockResolvedValue(
    new Response(JSON.stringify({
      code: "ok",
      data: { items: [{ id: "e-1", client_id: "u-1", kind: "project", title: "Launch", context: "", actions: "Built", outcome: "", proof_note: "", verified: true, created_at: "t1", updated_at: "t2" }] },
    }), { status: 200 }),
  )
  vi.stubGlobal("fetch", fetchMock)
  const result = await listEvidence()
  expect(result[0]).toMatchObject({ id: "e-1", clientId: "u-1", proofNote: "", verified: true })
})
~~~

Run: npm.cmd run test -- src/tests/domain-api.spec.ts
Expected: FAIL because the domain adapter modules do not exist.

- [ ] **Step 2: Implement minimal domain adapters**

Map only snake_case fields defined by the backend schemas. For draft saving, convert Web resume fields to job.target_role, employment_type, expected_salary, nested date fields, and section_visibility; do not send client IDs because Web auth owns identity. For membership, do not mark an order paid until completeDemoPayment returns a paid order and VIP response.

- [ ] **Step 3: Run focused tests**

Run: npm.cmd run test -- src/tests/domain-api.spec.ts
Expected: all domain mapping and error propagation tests pass.

- [ ] **Step 4: Commit**

~~~bash
git add web-frontend/src/lib web-frontend/src/tests/domain-api.spec.ts
git commit -m "feat(web): add typed functional domain adapters"
~~~

### Task 2: Complete Draft Management and Web Resume Editor

**Files:**
- Modify: web-frontend/src/views/ResumeView.vue
- Create: web-frontend/src/views/ResumeEditorView.vue
- Modify: web-frontend/src/App.vue
- Modify: web-frontend/src/components/WebSidebar.vue
- Modify: web-frontend/src/styles/base.css
- Create: web-frontend/src/lib/draft-workflow.ts
- Test: web-frontend/src/tests/resume-workflow.spec.ts

**Interfaces:**
- ResumeView consumes listDrafts, copyDraft, and deleteDraft; it emits open-draft with a draft ID.
- ResumeEditorView receives draftId: string, loads getDraft(draftId), and saves saveDraft({ ...draft, id: draftId }).
- App.vue holds editingDraftId: string | null; when set, it renders ResumeEditorView in the existing transition shell and returns to ResumeView after save/cancel.

- [ ] **Step 1: Write failing workflow tests**

Because this repository has no Vue component test runtime, cover the pure workflow helpers used by the view: Open selection, copy prepending, delete filtering, and save payload preservation. Existing AsyncButton/useAsyncAction tests cover pending cleanup; the production build verifies the SFC wiring.

~~~ts
it("removes only the confirmed draft", () => {
  expect(removeDraftById([{ id: "d-1" }, { id: "d-2" }] as DraftRecord[], "d-1"))
    .toEqual([{ id: "d-2" }])
})
~~~

Run: npm.cmd run test -- src/tests/resume-workflow.spec.ts
Expected: FAIL because the editor view and actions are not wired.

- [ ] **Step 2: Implement draft adapter wiring and editor state**

Implement draft-workflow.ts with removeDraftById, prependDraft, and toDraftSaveInput helpers. Use a local editable DraftRecord, preserve all backend resume sections, and expose add/remove controls for education, employment, projects, skills, and certificates. Keep the first editor version form-based and deterministic; do not introduce a second draft store. Use AsyncButton for save/cancel/open/copy/delete and LoadingSpinner for the stable editor loading block.

- [ ] **Step 3: Add responsive editor styles**

Use the existing inline-form and field tokens. Desktop uses two-column field groups; at the existing mobile breakpoint all groups become one column. Keep the editor min-height equal to its loading skeleton.

- [ ] **Step 4: Run focused tests and build**

Run: npm.cmd run test -- src/tests/resume-workflow.spec.ts and npm.cmd run build
Expected: focused tests and production build pass.

- [ ] **Step 5: Commit**

~~~bash
git add web-frontend/src/views/ResumeView.vue web-frontend/src/views/ResumeEditorView.vue web-frontend/src/App.vue web-frontend/src/components/WebSidebar.vue web-frontend/src/styles/base.css web-frontend/src/lib/draft-workflow.ts web-frontend/src/tests/resume-workflow.spec.ts
git commit -m "feat(web): complete draft management workflow"
~~~

### Task 3: Complete Application Follow-up Workflow

**Files:**
- Modify: web-frontend/src/views/ApplicationsView.vue
- Modify: web-frontend/src/styles/base.css
- Test: web-frontend/src/tests/applications-workflow.spec.ts

**Interfaces:**
- ApplicationsView consumes the Task 1 application adapter.
- Local editingId, timelineId, pendingAction, and form refs are view-local; no global store is added.

- [ ] **Step 1: Write failing workflow tests**

Test edit mode sending the existing record ID through saveApplication, status changes persisting, timeline events appending only after a successful response, reminders using the existing ISO string payload, deletion requiring confirmation, and row-level pending keys clearing after rejection.

- [ ] **Step 2: Implement edit/status/timeline/reminder/delete controls**

Reuse the existing create form for edit mode. Add a compact status selector, timeline disclosure, reminder input, and delete action to each record. Use per-record pending keys so one record remains interactive while another mutation is pending; disable only conflicting controls.

- [ ] **Step 3: Add empty/error/loading and responsive styles**

Keep the existing application list visible during row mutations. Preserve existing status labels and add retry controls to the current error notice. Stack record actions below the body on mobile.

- [ ] **Step 4: Run tests and build**

Run: npm.cmd run test -- src/tests/applications-workflow.spec.ts and npm.cmd run build
Expected: PASS with no API URL or payload changes.

- [ ] **Step 5: Commit**

~~~bash
git add web-frontend/src/views/ApplicationsView.vue web-frontend/src/styles/base.css web-frontend/src/tests/applications-workflow.spec.ts
git commit -m "feat(web): complete application follow-up workflow"
~~~

### Task 4: Add Experience Evidence Workspace

**Files:**
- Create: web-frontend/src/views/EvidenceView.vue
- Create: web-frontend/src/components/EvidenceForm.vue
- Modify: web-frontend/src/App.vue
- Modify: web-frontend/src/components/WebSidebar.vue
- Modify: web-frontend/src/styles/base.css
- Test: web-frontend/src/tests/evidence-workflow.spec.ts

**Interfaces:**
- EvidenceView consumes listEvidence, saveEvidence, deleteEvidence, getEvidenceSuggestions, and checkResumeReadiness.
- EvidenceForm props: modelValue: EvidenceDraft, pending: boolean, editing: boolean; emits update:modelValue, submit, and cancel.
- EvidenceDraft fields exactly match kind, title, context, actions, outcome, proofNote, and verified.

- [ ] **Step 1: Write failing tests**

Cover list rendering, create/edit mapping, delete confirmation, verified toggle, role-based suggestions, readiness blocking/warning groups, API 401/403 error state, and pending cleanup after save failure.

- [ ] **Step 2: Implement the form and list**

Use a select for the five backend evidence kinds, required title/actions validation, bounded textareas, and a checkbox for verified. Keep original text when the API rejects. Use row-level delete pending state and one form pending state.

- [ ] **Step 3: Implement suggestion/readiness panels**

The role input is optional until the user requests suggestions. Suggestions display source title, target section, description, and risk note. Readiness accepts the currently selected draft resume if available; otherwise show an explicit select-a-draft state instead of inventing a resume payload.

- [ ] **Step 4: Add navigation and responsive styles**

Add the sidebar key evidence and active component mapping. Use the existing keyed transition, stable skeleton height, and mobile single-column form layout.

- [ ] **Step 5: Run tests and build**

Run: npm.cmd run test -- src/tests/evidence-workflow.spec.ts and npm.cmd run build
Expected: PASS; no H5 files changed.

- [ ] **Step 6: Commit**

~~~bash
git add web-frontend/src/views/EvidenceView.vue web-frontend/src/components/EvidenceForm.vue web-frontend/src/App.vue web-frontend/src/components/WebSidebar.vue web-frontend/src/styles/base.css web-frontend/src/tests/evidence-workflow.spec.ts
git commit -m "feat(web): add experience evidence workspace"
~~~

### Task 5: Add Membership and Order View

**Files:**
- Create: web-frontend/src/views/MembershipView.vue
- Create: web-frontend/src/components/MembershipPackageCard.vue
- Create: web-frontend/src/components/OrderRow.vue
- Modify: web-frontend/src/App.vue
- Modify: web-frontend/src/components/WebSidebar.vue
- Modify: web-frontend/src/views/AccountView.vue
- Modify: web-frontend/src/styles/base.css
- Test: web-frontend/src/tests/membership-workflow.spec.ts

**Interfaces:**
- MembershipView consumes getVipStatus, listMembershipPackages, createMembershipOrder, completeDemoPayment, and listOrders.
- MembershipPackageCard props: package, currentVip, pending; emits purchase(packageType, autoRenew).
- OrderRow receives a mapped MembershipOrder and renders status without changing it.

- [ ] **Step 1: Write failing tests**

Test package loading, entitlement rendering, order creation, demo payment completion, order list refresh, expired/409 handling, demo-disabled handling, and the invariant that an order remains pending until the callback succeeds.

- [ ] **Step 2: Implement package and entitlement UI**

Load VIP/package/order data in parallel with one block skeleton. Show current level, expiry, auto-renew, package benefits, and only disable the package currently being submitted.

- [ ] **Step 3: Implement order/payment state machine**

Use states idle, creating, awaiting-payment, paying, paid, and error. In demo mode expose the existing demo callback as an explicit action; never infer payment from order creation. Refresh VIP and orders after confirmed payment.

- [ ] **Step 4: Link account and gated notices**

Add a membership entry to AccountView and make upgrade notices in later assessment/comparison views navigate to the membership key through the existing navigate event.

- [ ] **Step 5: Run tests/build and commit**

Run: npm.cmd run test -- src/tests/membership-workflow.spec.ts and npm.cmd run build

~~~bash
git add web-frontend/src/views/MembershipView.vue web-frontend/src/components/MembershipPackageCard.vue web-frontend/src/components/OrderRow.vue web-frontend/src/App.vue web-frontend/src/components/WebSidebar.vue web-frontend/src/views/AccountView.vue web-frontend/src/styles/base.css web-frontend/src/tests/membership-workflow.spec.ts
git commit -m "feat(web): add membership and order visibility"
~~~

### Task 6: Add Career Assessment View

**Files:**
- Create: web-frontend/src/views/AssessmentView.vue
- Create: web-frontend/src/components/AssessmentQuestionCard.vue
- Modify: web-frontend/src/App.vue
- Modify: web-frontend/src/components/WebSidebar.vue
- Modify: web-frontend/src/styles/base.css
- Test: web-frontend/src/tests/assessment-workflow.spec.ts

**Interfaces:**
- AssessmentView consumes getAssessmentQuestions, loadAssessment, and submitAssessment(answers, reportMode).
- AssessmentQuestionCard props: question, modelValue: number | undefined, disabled; emits update:modelValue.
- Answers are Record<string, number> and report mode is simplified or professional.

- [ ] **Step 1: Write failing tests**

Cover question rendering, required answer validation, local answer preservation, submit pending cleanup, saved-result loading, simplified/professional mode selection, disclaimer rendering, and 403 upgrade navigation.

- [ ] **Step 2: Implement question and result states**

Load questions and existing result independently; render answered/total progress; prevent duplicate submit; preserve answers if submission rejects. Render returned top interests, work style, evidence, confidence note, and 7/30/90-day actions only when present.

- [ ] **Step 3: Add membership-aware report handling**

When the API returns an upgrade notice or 403, keep the simplified result visible and add a navigation action to membership. Do not expose hidden professional fields from local state.

- [ ] **Step 4: Add navigation/styles and verify**

Add sidebar key assessment, mobile one-column question cards, stable result skeleton, and reduced-motion-compatible transitions. Run focused tests and npm.cmd run build.

- [ ] **Step 5: Commit**

~~~bash
git add web-frontend/src/views/AssessmentView.vue web-frontend/src/components/AssessmentQuestionCard.vue web-frontend/src/App.vue web-frontend/src/components/WebSidebar.vue web-frontend/src/styles/base.css web-frontend/src/tests/assessment-workflow.spec.ts
git commit -m "feat(web): add career assessment workflow"
~~~

### Task 7: Add Role Comparison Workflow

**Files:**
- Create: web-frontend/src/views/ComparisonView.vue
- Create: web-frontend/src/components/ComparisonRolePicker.vue
- Modify: web-frontend/src/App.vue
- Modify: web-frontend/src/components/WebSidebar.vue
- Modify: web-frontend/src/views/CareerView.vue
- Modify: web-frontend/src/views/JobsView.vue
- Modify: web-frontend/src/styles/base.css
- Test: web-frontend/src/tests/comparison-workflow.spec.ts

**Interfaces:**
- ComparisonView consumes loadCareerRecommendations and compareRoles(roleNames: string[]).
- ComparisonRolePicker props: roles, selected, maxSelectable; emits update:selected and submit.
- Selected roles are unique strings with a minimum of 2 and maximum of 4 before submit.

- [ ] **Step 1: Write failing tests**

Cover minimum/maximum selection, duplicate prevention, comparison response mapping, VIP limit error rendering with membership navigation, pending cleanup, and applications handoff for the selected weekly target.

- [ ] **Step 2: Implement role picker and compare result**

Load available roles from the existing career recommendation endpoint. Show selected count, disable submit outside 2-4 roles, and render score breakdown, strengths, missing skills, risk notice, and each action-plan horizon from /api/career/compare.

- [ ] **Step 3: Wire entry points**

Add a comparison action to CareerView when recommendations exist and a role-selection action to JobsView when a query result can identify a role. Keep the comparison sidebar entry available for direct navigation with an explicit empty state.

- [ ] **Step 4: Add responsive interaction and verify**

Use stable comparison card dimensions, light press/reveal motion only, and a vertical mobile layout. Run focused tests and npm.cmd run build.

- [ ] **Step 5: Commit**

~~~bash
git add web-frontend/src/views/ComparisonView.vue web-frontend/src/components/ComparisonRolePicker.vue web-frontend/src/App.vue web-frontend/src/components/WebSidebar.vue web-frontend/src/views/CareerView.vue web-frontend/src/views/JobsView.vue web-frontend/src/styles/base.css web-frontend/src/tests/comparison-workflow.spec.ts
git commit -m "feat(web): add role comparison workflow"
~~~

### Task 8: Integration Verification and Documentation

**Files:**
- Modify: docs/interaction-upgrade-changelog.md
- Create: docs/web-functional-completion-changelog.md
- Test: web-frontend/src/tests/*.spec.ts (existing plus new focused suites)

**Interfaces:**
- All new views are reachable through WorkspaceView keys and preserve the existing navigate event contract.

- [ ] **Step 1: Run full Web tests**

Run: cd web-frontend; npm.cmd run test
Expected: every existing and new Web test passes with zero failures.

- [ ] **Step 2: Run production builds and H5 regression checks**

Run: cd web-frontend; npm.cmd run build; cd ..\resume-miniprogram; npm.cmd run test:unit; npm.cmd run build:h5
Expected: Web build and unchanged H5 test/build both exit 0.

- [ ] **Step 3: Run static UI checks and diff checks**

Run: node C:\Users\16102\.codex\skills\impeccable\scripts\detect.mjs --json web-frontend/src and git diff --check
Expected: detector returns no findings and diff check has no whitespace errors.

- [ ] **Step 4: Update changelogs**

Record each new Web view, endpoint group, permission/empty/error state, and explicitly note that H5 was not modified and no backend endpoint was added.

- [ ] **Step 5: Commit integration documentation**

~~~bash
git add docs/interaction-upgrade-changelog.md docs/web-functional-completion-changelog.md
git commit -m "docs(web): record functional completion"
~~~

## Execution Order

Complete Tasks 1-3 first so the existing Web workbench is a usable base. Then complete Tasks 4-7 in order because evidence feeds assessment and comparison, while membership/order provides the entitlement state those views must display. Task 8 is required before claiming completion.
