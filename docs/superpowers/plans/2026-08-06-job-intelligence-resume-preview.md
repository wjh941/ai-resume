# Job Intelligence And Resume Preview Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Return role-specific local job intelligence and let the user create
and preview a safely auto-completed resume.

**Architecture:** FastAPI selects a deterministic mock profile and namespaces
its cache version. A pure frontend utility enriches only blank non-factual
resume fields. The existing Pinia store then drives template selection and
editor preview pages without changing backend payloads.

**Tech Stack:** Python 3.11, FastAPI, Pydantic, pytest, Uni-App Vue 3,
TypeScript, Pinia, Vitest.

## Global Constraints

- Keep FastAPI endpoints, SQLite tables, resume payload shape, export formats,
  and the four existing template IDs unchanged.
- A user-entered value is never overwritten by automatic completion.
- Never generate schools, companies, work history, project history, personal
  identity, phone, email, or city.
- Mock cache uses `mock-v2`; non-mock provider cache keys remain unchanged.
- The primary form action can navigate with missing contact data; manual save
  retains existing validation.
- Do not push, merge, or create a pull request.

---

### Task 1: Role-Specific Mock Job Profiles

**Files:**
- Modify: `resume-backend/app/services/ai_client.py`
- Modify: `resume-backend/app/api/ai.py`
- Modify: `resume-backend/tests/test_job_query_api.py`

**Interfaces:**

```python
MOCK_CACHE_KEY = "mock-v2"

def mock_job_profile(role_name: str) -> JobIntelligence: ...
```

- [ ] **Step 1: Write the failing API test**

Add this behavior test:

```python
def test_mock_profiles_return_distinct_data_for_data_and_frontend_roles(api_client):
    data = assert_success(api_client.post("/api/job/query", json={"role_name": "数据工程师"}))
    frontend = assert_success(api_client.post("/api/job/query", json={"role_name": "前端开发工程师"}))

    assert data["required_skills"] == ["Python", "SQL", "Data warehousing"]
    assert frontend["required_skills"] == ["JavaScript", "TypeScript", "Vue or React"]
    assert data["responsibilities"] != frontend["responsibilities"]
```

- [ ] **Step 2: Run the red test**

Run:

```powershell
resume-backend\.venv\Scripts\python.exe -m pytest resume-backend/tests/test_job_query_api.py::test_mock_profiles_return_distinct_data_for_data_and_frontend_roles -v
```

Expected: FAIL because both roles currently return the data-engineering
profile.

- [ ] **Step 3: Implement deterministic profiles and cache versioning**

Implement `mock_job_profile()` with data, frontend, backend, product, and
generic role keyword matching. `MockAIClient.query_job()` returns that
profile. In `api/ai.py`, use `MOCK_CACHE_KEY` for `mock` only when reading
and writing the job cache.

- [ ] **Step 4: Run focused backend tests**

Run:

```powershell
resume-backend\.venv\Scripts\python.exe -m pytest resume-backend/tests/test_job_query_api.py -v
```

Expected: PASS.

### Task 2: Safe Resume Preparation Utility And Form Flow

**Files:**
- Create: `resume-miniprogram/src/utils/resume-autofill.ts`
- Create: `resume-miniprogram/src/tests/resume-autofill.spec.ts`
- Modify: `resume-miniprogram/src/pages/resume-form/index.vue`

**Interfaces:**

```ts
export function prepareResumeForJob(
  draft: ResumeDraft,
  job: JobIntelligence,
): void
```

- [ ] **Step 1: Write the failing utility tests**

```ts
it("fills only blank non-factual fields from the selected job", () => {
  const draft = createEmptyDraft()
  draft.resume.basic.name = "张三"
  prepareResumeForJob(draft, frontendJob)

  expect(draft.resume.job.targetRole).toBe("前端开发工程师")
  expect(draft.resume.job.expectedSalary).toBe("18k-30k")
  expect(draft.resume.skills.skills).toEqual([
    "JavaScript（待确认）",
    "TypeScript（待确认）",
    "Vue or React（待确认）",
  ])
  expect(draft.resume.basic.name).toBe("张三")
  expect(draft.resume.education).toEqual([])
})

it("does not overwrite fields the user already completed", () => {
  const draft = createEmptyDraft()
  draft.resume.job.expectedSalary = "20k-25k"
  draft.resume.skills.skills = ["Python"]
  draft.resume.selfEvaluation = "已有自我评价"
  prepareResumeForJob(draft, frontendJob)

  expect(draft.resume.job.expectedSalary).toBe("20k-25k")
  expect(draft.resume.skills.skills).toEqual(["Python"])
  expect(draft.resume.selfEvaluation).toBe("已有自我评价")
})
```

- [ ] **Step 2: Run the red test**

Run:

```powershell
cd resume-miniprogram
npm run test:unit -- resume-autofill.spec.ts
```

Expected: FAIL because `prepareResumeForJob` does not exist.

- [ ] **Step 3: Implement the pure preparation utility**

Fill only empty values as specified in Global Constraints. Use
`job.salaryByExperience["1-3_years"]` and fall back to the first salary
range. Use `可协商` for an empty availability field.

- [ ] **Step 4: Connect the primary form action**

Add `prepareAndChooseTemplate()` in the resume form. It calls
`prepareResumeForJob(store.draft, store.activeJob ?? store.draft.jobIntelligence)`,
checkpoints the store, and navigates to `/pages/template-picker/index`.
When no selected job is available, show a non-blocking toast directing the
user to query a role first. Do not call `save()` from this action.

- [ ] **Step 5: Run frontend tests**

Run:

```powershell
npm run test:unit
```

Expected: PASS.

### Task 3: Template Selection And Resume Preview

**Files:**
- Create: `resume-miniprogram/src/components/ResumePreview.vue`
- Create: `resume-miniprogram/src/utils/resume-preview.ts`
- Modify: `resume-miniprogram/src/pages/template-picker/index.vue`
- Modify: `resume-miniprogram/src/pages/resume-editor/index.vue`

**Interfaces:**

```ts
const templates: Array<{ id: TemplateId; name: string; description: string }>

function placeholder(value: string, fallback: string): string
```

- [ ] **Step 1: Write the failing preview-model test**

Create `resume-miniprogram/src/tests/resume-preview.spec.ts` that imports
`previewContact()` from `utils/resume-preview.ts` and verifies missing contact details
render as `待补充` while supplied values remain unchanged:

```ts
expect(previewContact("", "手机待补充")).toBe("手机待补充")
expect(previewContact("13800138000", "手机待补充")).toBe("13800138000")
```

- [ ] **Step 2: Run the red test**

Run:

```powershell
npm run test:unit -- resume-preview.spec.ts
```

Expected: FAIL because `previewContact` does not exist.

- [ ] **Step 3: Implement the preview component**

Render basic information, target job, skills, self-evaluation, education,
employment, and projects. Hide an empty education, employment, or projects
section. Show blank basic values with the explicit `待补充` fallback. Expose
`previewContact()` from a focused TypeScript helper used by the component.

- [ ] **Step 4: Implement selection and editor pages**

Render four cards with the existing IDs and names:

```ts
business: "简约商务版"
technology: "技术开发/测试版"
graduate: "应届生实习简洁版"
analytics: "数据分析/运营精致版"
```

Selecting a card assigns `store.draft.templateId`, checkpoints it, and
navigates to the editor. The editor uses `ResumePreview`, provides `返回填写`
and `保存草稿` actions, and preserves the existing draft-save behavior.

- [ ] **Step 5: Run complete verification**

Run:

```powershell
cd resume-miniprogram
npm run test:unit
npm run build:h5
npm run build:mp-weixin
cd ..
resume-backend\.venv\Scripts\python.exe -m pytest resume-backend/tests -v
```

Expected: all tests and both frontend targets pass; the PDF test may skip
when Chromium is not installed.
