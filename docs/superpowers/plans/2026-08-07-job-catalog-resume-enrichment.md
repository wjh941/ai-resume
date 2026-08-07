# Job Catalog and Resume Enrichment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add persistent related-role suggestions, explicit multi-role resume targeting, detailed fact-safe resume enrichment, and fuller career-toolkit guidance.

**Architecture:** A SQLite role catalog supplies local type-ahead suggestions through a new read-only API route. The existing job-query and consultation APIs remain the source of independent role intelligence. The Uni-App search page keeps selected roles and their consultation results locally, while resume enrichment uses typed helpers that clearly mark every unknown fact.

**Tech Stack:** FastAPI, Pydantic, SQLite, Vue 3, Pinia, Uni-App, Vitest, pytest.

## Global Constraints

- Do not change existing CSV import/export, draft/export payloads, or file-generation behavior.
- Do not invent employers, schools, dates, certificates, project facts, or metrics.
- Mark missing factual information as `[待确认]`.
- Keep the current identity consultation flow and persistence behavior compatible.
- Keep changes local on `feature/ai-resume-demo`; do not push, merge, or create a PR automatically.

---

### Task 1: Persistent Job Catalog and Suggestions API

**Files:**
- Modify: `resume-backend/app/db.py`
- Create: `resume-backend/app/services/job_catalog.py`
- Modify: `resume-backend/app/schemas/job.py`
- Modify: `resume-backend/app/api/ai.py`
- Test: `resume-backend/tests/test_job_query_api.py`

**Interfaces:**
- Produces `JobSuggestion(role_name: str, category: str)`.
- Produces `JobCatalog.search(query: str, limit: int = 8) -> list[JobSuggestion]`.
- Produces `GET /api/job/suggestions?q=<query>`.

- [ ] **Step 1: Write the failing API tests**

```python
def test_engineer_suggestions_return_distinct_catalog_roles(api_client):
    response = api_client.get("/api/job/suggestions", params={"q": "工程师"})

    assert_success(response)
    names = [item["role_name"] for item in response.json()["data"]["items"]]
    assert "数据工程师" in names
    assert "AI Agent工程师" in names


def test_blank_suggestion_query_returns_no_items(api_client):
    response = api_client.get("/api/job/suggestions", params={"q": "   "})

    assert_success(response)
    assert response.json()["data"] == {"items": []}
```

- [ ] **Step 2: Run the focused test to verify it fails**

Run: `resume-backend\.venv\Scripts\python.exe -m pytest resume-backend/tests/test_job_query_api.py -v`

Expected: FAIL because `/api/job/suggestions` is not registered.

- [ ] **Step 3: Add catalog storage and search**

```python
class JobSuggestion(BaseModel):
    role_name: str
    category: str


class JobCatalog:
    def search(self, query: str, limit: int = 8) -> list[JobSuggestion]:
        normalized = normalize_role_name(query)
        if not normalized:
            return []
        # Score canonical name prefix matches before aliases and substring matches.
```

- [ ] **Step 4: Seed catalog data and register the route**

Add `job_catalog` table creation and `INSERT OR IGNORE` seed data in
`initialize_database`. Include data engineering, AI Agent engineering,
frontend, backend, testing, algorithm, machine learning, data analysis,
product, operations, DevOps, and security roles. Register a `GET` route that
returns `success({"items": [...]})`.

- [ ] **Step 5: Run focused tests**

Run: `resume-backend\.venv\Scripts\python.exe -m pytest resume-backend/tests/test_job_query_api.py -v`

Expected: PASS.

- [ ] **Step 6: Commit locally**

```bash
git add resume-backend/app/db.py resume-backend/app/services/job_catalog.py \
  resume-backend/app/schemas/job.py resume-backend/app/api/ai.py \
  resume-backend/tests/test_job_query_api.py
git commit -m "feat: add persistent job catalog suggestions"
```

### Task 2: Multi-role Search and Explicit Resume Target Selection

**Files:**
- Modify: `resume-miniprogram/src/types/consultation.ts`
- Modify: `resume-miniprogram/src/services/resume-api.ts`
- Modify: `resume-miniprogram/src/pages/job-search/index.vue`
- Test: `resume-miniprogram/src/tests/consultation-api.spec.ts`

**Interfaces:**
- Produces `JobSuggestion { roleName: string; category: string }`.
- Produces `queryJobSuggestions(query: string): Promise<JobSuggestion[]>`.
- The job-search page keeps `selectedRoles`, `jobConsultations`, and an active
  result index; it opens a target-role confirmation panel before navigation.

- [ ] **Step 1: Write the failing frontend API mapper test**

```typescript
it("maps job catalog suggestions from the backend", async () => {
  const suggestions = await queryJobSuggestions("工程师")

  expect(suggestions).toEqual([
    { roleName: "数据工程师", category: "数据与平台" },
    { roleName: "AI Agent工程师", category: "人工智能" },
  ])
  expect(calls[0].url).toContain("/api/job/suggestions?q=")
})
```

- [ ] **Step 2: Run the focused test to verify it fails**

Run: `npm.cmd run test:unit -- consultation-api.spec.ts`

Expected: FAIL because `queryJobSuggestions` is not exported.

- [ ] **Step 3: Add API mapping and search-page selection state**

Implement `queryJobSuggestions`. In the search page, query suggestions from
role input, allow selecting up to three canonical roles, and prevent duplicate
chips. Selecting an item changes only local selection state.

- [ ] **Step 4: Load and display independent analyses**

When an identity is available, call `queryJobConsultation` once per selected
role with `Promise.all`. Keep the full results in `jobConsultations`. Render
role tabs and set the active tab's job intelligence in `useResumeStore`.

- [ ] **Step 5: Require a target-role confirmation**

Replace direct template navigation with a visible target-role picker. Its
click handler calls `prepareResumeForJob` only for the selected consultation
result, checkpoints the draft, and then calls the existing template-picker
navigation.

- [ ] **Step 6: Run focused frontend tests**

Run: `npm.cmd run test:unit -- consultation-api.spec.ts consultation-flow.spec.ts`

Expected: PASS.

- [ ] **Step 7: Commit locally**

```bash
git add resume-miniprogram/src/types/consultation.ts \
  resume-miniprogram/src/services/resume-api.ts \
  resume-miniprogram/src/pages/job-search/index.vue \
  resume-miniprogram/src/tests/consultation-api.spec.ts
git commit -m "feat: support multi-role job consultation"
```

### Task 3: Fact-safe Experience Enrichment

**Files:**
- Modify: `resume-miniprogram/src/utils/resume-autofill.ts`
- Modify: `resume-miniprogram/src/pages/resume-form/index.vue`
- Test: `resume-miniprogram/src/tests/resume-autofill.spec.ts`

**Interfaces:**
- Produces `createRoleBasedProjectDraft(job: JobIntelligence)`.
- Produces `createRoleBasedInternshipDraft(job: JobIntelligence)`.
- `prepareResumeForJob(draft, job)` creates one practice project only when
  `draft.resume.projects` is empty.

- [ ] **Step 1: Write failing safety and enrichment tests**

```typescript
it("adds a detailed marked practice project but never fabricates employment", () => {
  const draft = createEmptyDraft()

  prepareResumeForJob(draft, frontendJob)

  expect(draft.resume.employment).toEqual([])
  expect(draft.resume.projects).toHaveLength(1)
  expect(draft.resume.projects[0].name).toContain("[待确认]")
  expect(draft.resume.projects[0].description).toContain("TypeScript")
})

it("creates an optional internship draft with explicit unknown company and dates", () => {
  const item = createRoleBasedInternshipDraft(frontendJob)

  expect(item.company).toContain("[待确认]")
  expect(item.startDate).toContain("[待确认]")
  expect(item.description).toContain("Vue or React")
})
```

- [ ] **Step 2: Run the focused test to verify it fails**

Run: `npm.cmd run test:unit -- resume-autofill.spec.ts`

Expected: FAIL because the draft helper does not exist and no project is added.

- [ ] **Step 3: Implement role-specific draft helpers**

Build multi-line, editable description text from `requiredSkills`,
`responsibilities`, and a `[待确认]` evidence placeholder. Do not add an
internship entry automatically.

- [ ] **Step 4: Add explicit enrichment controls to the resume form**

Render an “AI 补全草案” panel only when an active job is present. A user can
append an internship draft or a project draft with an explicit button. Show a
short warning that the user must replace `[待确认]` with real facts.

- [ ] **Step 5: Run focused tests**

Run: `npm.cmd run test:unit -- resume-autofill.spec.ts`

Expected: PASS.

- [ ] **Step 6: Commit locally**

```bash
git add resume-miniprogram/src/utils/resume-autofill.ts \
  resume-miniprogram/src/pages/resume-form/index.vue \
  resume-miniprogram/src/tests/resume-autofill.spec.ts
git commit -m "feat: enrich resume drafts safely by target role"
```

### Task 4: Detailed Career Toolkit Responses

**Files:**
- Modify: `resume-backend/app/services/career_consultation.py`
- Test: `resume-backend/tests/test_consultation_api.py`

**Interfaces:**
- `build_career_advice(...) -> CareerAdviceResponse` returns at least five
  sections for each existing `AdviceTopic`.

- [ ] **Step 1: Write the failing depth test**

```python
def test_advice_adds_identity_aware_actions_templates_and_risk_checks(api_client):
    data = assert_success(
        api_client.post(
            "/api/consultation/advice",
            json={"identity_code": "2", "role_name": "数据工程师", "topic": "simulation_interview"},
        )
    )

    titles = [section["title"] for section in data["sections"]]
    assert len(data["sections"]) >= 5
    assert "落地行动清单" in titles
    assert "可复制表达" in titles
    assert "验证与避坑" in titles
```

- [ ] **Step 2: Run the focused test to verify it fails**

Run: `resume-backend\.venv\Scripts\python.exe -m pytest resume-backend/tests/test_consultation_api.py -v`

Expected: FAIL because responses currently contain two topic sections.

- [ ] **Step 3: Add shared identity-aware detailed sections**

After topic-specific content is built, append:

```python
sections.extend(
    [
        ("落地行动清单", _advice_action_items(identity_code, role, topic)),
        ("可复制表达", _advice_template_items(role, topic)),
        ("验证与避坑", _advice_risk_items(topic)),
    ]
)
```

Each helper returns at least two concise action items and preserves the
existing user question as a context item.

- [ ] **Step 4: Run focused tests**

Run: `resume-backend\.venv\Scripts\python.exe -m pytest resume-backend/tests/test_consultation_api.py -v`

Expected: PASS.

- [ ] **Step 5: Commit locally**

```bash
git add resume-backend/app/services/career_consultation.py \
  resume-backend/tests/test_consultation_api.py
git commit -m "feat: expand detailed career toolkit guidance"
```

### Task 5: Full Verification

**Files:**
- Verify only; do not make unrelated edits.

- [ ] **Step 1: Run backend test suite**

Run: `resume-backend\.venv\Scripts\python.exe -m pytest resume-backend/tests -v`

Expected: all tests pass.

- [ ] **Step 2: Run frontend unit suite**

Run: `npm.cmd run test:unit`

Expected: all tests pass.

- [ ] **Step 3: Build both frontend targets**

Run:

```bash
cd resume-miniprogram
npm.cmd run build:h5
npm.cmd run build:mp-weixin
```

Expected: both builds succeed.

- [ ] **Step 4: Check source changes**

Run:

```bash
git diff --check
git status --short --branch
```

Expected: no whitespace errors; only intended local commits or artifacts.

## Self-Review

- Persistent catalog, multiple selected roles, explicit resume target choice,
  safe enrichment, and detailed toolkit output are each covered by one task.
- Existing CSV and export interfaces are untouched because no task changes
  payload schemas or export modules.
- The plan has no deferred implementation placeholders; all new interfaces and
  testable outcomes are named above.
