# Web Activation Loop Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task with review checkpoints.

**Goal:** Let a new user create and save a first resume entirely in the Web workbench, while making the first three actions obvious from the overview.

**Architecture:** Reuse the existing `POST /api/draft/save` contract and `ResumeEditorView`. Add a small pure factory for a valid empty draft, keep creation state local to `ResumeView`, and derive the overview starter steps from the existing `OverviewState` without adding a new store or backend endpoint.

**Tech Stack:** Vue 3 `<script setup>`, TypeScript, Vitest, Vue Test Utils, existing `AsyncButton` and design tokens.

## Global Constraints

- Preserve existing API and backend schema compatibility.
- Do not expose PDF/DOCX import while the backend import endpoint returns 501.
- Keep all new user-facing copy in Simplified Chinese.
- Preserve existing local autosave, navigation guards, keyboard focus, and membership limits.
- Write tests first and run the focused test before implementation.

---

### Task 1: Empty Draft Factory

**Files:**
- Create: `web-frontend/src/lib/resume-draft.ts`
- Test: `web-frontend/src/tests/resume-draft.spec.ts`

**Interfaces:**
- Produces `createEmptyDraftInput(jobTitle: string, templateId: TemplateId): DraftSaveInput`.
- The returned `id` is an empty string so the existing backend treats it as a create operation.

- [ ] **Step 1: Write the failing test**

```ts
it("creates a complete empty draft with the selected title and template", () => {
  const draft = createEmptyDraftInput("数据分析师", "analytics")
  expect(draft).toMatchObject({ id: "", jobTitle: "数据分析师", templateId: "analytics" })
  expect(draft.resume.basic).toEqual({ name: "", phone: "", email: "", city: "" })
  expect(draft.resume.job).toEqual({ targetRole: "数据分析师", expectedSalary: "", employmentType: "" })
  expect(draft.resume.education).toEqual([])
  expect(draft.resume.employment).toEqual([])
  expect(draft.resume.projects).toEqual([])
  expect(draft.resume.skills).toEqual({ skills: [], certificates: [] })
  expect(draft.resume.sectionVisibility).toEqual({ basic: true, job: true, education: true, employment: true, projects: true, skills: true, selfEvaluation: true })
})

it("normalizes a blank title without changing the selected template", () => {
  const draft = createEmptyDraftInput("  ", "business")
  expect(draft.jobTitle).toBe("未命名简历")
  expect(draft.resume.job.targetRole).toBe("")
})
```

- [ ] **Step 2: Run the focused test and verify it fails**

Run: `npm.cmd exec vitest run src/tests/resume-draft.spec.ts`

Expected: FAIL because `resume-draft.ts` and `createEmptyDraftInput` do not exist.

- [ ] **Step 3: Implement the minimal factory**

Create the exact payload shape required by `DraftSaveInput`, trim `jobTitle`, use `未命名简历` when blank, and copy the trimmed title into `resume.job.targetRole` only when non-blank.

- [ ] **Step 4: Run the focused test and verify it passes**

Run: `npm.cmd exec vitest run src/tests/resume-draft.spec.ts`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add web-frontend/src/lib/resume-draft.ts web-frontend/src/tests/resume-draft.spec.ts
git commit -m "feat(web): add empty resume draft factory"
```

### Task 2: Web Resume Creation Flow

**Files:**
- Modify: `web-frontend/src/views/ResumeView.vue`
- Modify: `web-frontend/src/styles/base.css`
- Test: `web-frontend/src/tests/resume-view.spec.ts`

**Interfaces:**
- Consumes `createEmptyDraftInput` and existing `saveDraft`.
- Emits the existing `open-draft` event with the created draft ID.

- [ ] **Step 1: Write the failing component tests**

```ts
it("shows a new resume action instead of directing users to the mini-program", async () => {
  const wrapper = mount(ResumeView, { global: { stubs: { AsyncButton: true, ExpandableText: true, LoadingSpinner: true, ProgressiveListSentinel: true, ErrorNotice: true } } })
  await flushPromises()
  expect(wrapper.text()).toContain("新建简历")
  expect(wrapper.text()).not.toContain("请先在小程序")
})

it("creates a draft and emits its id", async () => {
  saveDraftMock.mockResolvedValue({ id: "draft-1", jobTitle: "数据分析师" })
  const wrapper = mount(ResumeView, { global: { stubs: { AsyncButton: false, ExpandableText: true, LoadingSpinner: true, ProgressiveListSentinel: true, ErrorNotice: true } } })
  await flushPromises()
  await wrapper.get("button[data-action='new-resume']").trigger("click")
  await wrapper.get("input[name='new-job-title']").setValue("数据分析师")
  await wrapper.get("button[data-action='create-resume']").trigger("click")
  await flushPromises()
  expect(saveDraftMock).toHaveBeenCalled()
  expect(wrapper.emitted("open-draft")?.[0]).toEqual(["draft-1"])
})
```

Mock `listDrafts` to return an empty list and mock `saveDraft` through the module boundary. The first test must fail because the current empty state contains neither the action nor the form; the second must fail because no create handler exists.

- [ ] **Step 2: Run the focused tests and verify they fail**

Run: `npm.cmd exec vitest run src/tests/resume-view.spec.ts`

Expected: FAIL on the missing action/form and missing `open-draft` emission.

- [ ] **Step 3: Implement the minimal creation UI**

Add a compact form toggled by `新建简历`, with a required job/title input and the four existing template IDs. Disable duplicate submits, preserve entered values on errors, map API errors to `ErrorNotice`, and offer a membership navigation action when the backend reports the free-draft limit. On success emit `open-draft` with the returned ID and refresh the list only after returning from the editor.

- [ ] **Step 4: Add focused styles**

Use existing `workbench-form`, `decision-surface`, `primary-button`, and spacing tokens. Keep the empty state as an unframed page section; do not add a new card hierarchy or import affordance.

- [ ] **Step 5: Run focused tests and verify they pass**

Run: `npm.cmd exec vitest run src/tests/resume-draft.spec.ts src/tests/resume-view.spec.ts`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add web-frontend/src/views/ResumeView.vue web-frontend/src/styles/base.css web-frontend/src/tests/resume-view.spec.ts
git commit -m "feat(web): create resumes from the web workbench"
```

### Task 3: First-Session Activation Steps

**Files:**
- Create: `web-frontend/src/lib/activation.ts`
- Modify: `web-frontend/src/views/OverviewView.vue`
- Modify: `web-frontend/src/styles/base.css`
- Test: `web-frontend/src/tests/activation.spec.ts`

**Interfaces:**
- Produces `getActivationSteps(state: OverviewState): ActivationStep[]` with `label`, `target`, and `state` fields.
- Uses only existing overview counts and navigation targets.

- [ ] **Step 1: Write the failing test**

```ts
it("returns ordered activation steps for a new account", () => {
  expect(getActivationSteps(emptyOverview)).toEqual([
    { label: "创建第一份简历", target: "resume", state: "current" },
    { label: "制定一项职业行动", target: "career", state: "next" },
    { label: "记录第一条投递", target: "applications", state: "next" },
  ])
})

it("marks completed work without hiding the remaining steps", () => {
  const state = { ...emptyOverview, draftCount: 1, openTaskCount: 1, applicationCount: 0, hasWorkspaceData: true }
  expect(getActivationSteps(state).map((step) => step.state)).toEqual(["done", "current", "next"])
})
```

- [ ] **Step 2: Run the focused test and verify it fails**

Run: `npm.cmd exec vitest run src/tests/activation.spec.ts`

Expected: FAIL because `activation.ts` does not exist.

- [ ] **Step 3: Implement the pure step selector**

Return the fixed order resume → career → applications. Mark a step `done` when its corresponding count is complete, `current` as the first incomplete step, and `next` for later incomplete steps.

- [ ] **Step 4: Render the guide in the existing overview starter section**

Replace the three generic starter cards shown when `hasWorkspaceData` is false with a titled “开始使用” sequence and one action per step. Keep the guide inline, keyboard accessible, and removable once workspace data exists. The resume action now opens the Web creation form.

- [ ] **Step 5: Run focused tests and verify they pass**

Run: `npm.cmd exec vitest run src/tests/activation.spec.ts src/tests/dashboard.spec.ts`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add web-frontend/src/lib/activation.ts web-frontend/src/views/OverviewView.vue web-frontend/src/styles/base.css web-frontend/src/tests/activation.spec.ts
git commit -m "feat(web): add first-session activation guide"
```

### Task 4: Full Verification

**Files:** None.

- [ ] **Step 1: Run all Web tests**

Run: `npm.cmd run test`

Expected: all existing and new tests pass.

- [ ] **Step 2: Run the production build**

Run: `npm.cmd run build`

Expected: Vite exits with code 0 and writes `web-frontend/dist`.

- [ ] **Step 3: Run the UI detector once over changed markup**

Run: `node C:\Users\16102\.codex\skills\impeccable\scripts\detect.mjs --json web-frontend/src/views/ResumeView.vue web-frontend/src/views/OverviewView.vue`

Expected: inspect any findings and report whether they are actionable or false positives.

