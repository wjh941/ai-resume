# Career Consultation V2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver a persistent, identity-aware career consultation system with
nine job-analysis sections, safe resume review, PDF text extraction, and
standalone career-advice tools.

**Architecture:** Extend the existing consultation namespace instead of changing
the established job/draft/export contracts. Keep content assembly in
`career_consultation.py`, preserve state in a dedicated Pinia store, and render
consultation, review, and advice as separate mobile panels on the existing job
search page.

**Tech Stack:** FastAPI, Pydantic, `pypdf`, Vue 3, Uni-App, Pinia, Vitest,
pytest.

## Global Constraints

- Keep `/api/job/query`, `/api/resume/ai-rewrite`, drafts, templates, and
  export contracts unchanged.
- Preserve user identity locally across restart and reuse it for new roles.
- Never fabricate candidate facts or numeric results; use `[待确认]`.
- Default mock market content must be labeled as an estimate, not live data.
- Do not create a PR or merge branches; push only `feature/ai-resume-demo`.

---

### Task 1: Consultation Models and Backend Content

**Files:**
- Modify: `resume-backend/app/schemas/consultation.py`
- Modify: `resume-backend/app/services/career_consultation.py`
- Modify: `resume-backend/app/services/ai_client.py`
- Test: `resume-backend/tests/test_consultation_api.py`

**Interfaces:**
- Produces `JobConsultationResponse` with nine sections and `market_notice`.
- Produces `ResumeReviewResponse` with `optimized_resume_text` and
  `interview_intro`.
- Produces `CareerAdviceResponse` from an `AdviceRequest`.

- [ ] **Step 1: Write failing API tests**

```python
assert len(data["job_analysis_sections"]) == 9
assert data["job_analysis_sections"][8]["title"] == "岗位避雷点"
assert "[待确认]" in data["optimized_resume_text"]
assert data["interview_intro"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `resume-backend\.venv\Scripts\python.exe -m pytest resume-backend/tests/test_consultation_api.py -v`

- [ ] **Step 3: Add models and deterministic mock content**

```python
class AdviceRequest(BaseModel):
    identity_code: IdentityCode
    topic: AdviceTopic
    role_name: str | None = None
    question: str | None = None
```

- [ ] **Step 4: Run backend tests**

Run: `resume-backend\.venv\Scripts\python.exe -m pytest resume-backend/tests/test_consultation_api.py -v`

### Task 2: Advice and PDF APIs

**Files:**
- Modify: `resume-backend/app/api/consultation.py`
- Modify: `resume-backend/requirements.txt`
- Test: `resume-backend/tests/test_consultation_api.py`

**Interfaces:**
- `POST /api/consultation/advice`
- `POST /api/consultation/resume-pdf-extract`

- [ ] **Step 1: Write failing tests**

```python
response = api_client.post("/api/consultation/advice", json={"identity_code": "3", "topic": "salary_negotiation"})
assert response.status_code == 200
assert api_client.post("/api/consultation/resume-pdf-extract", files={"file": ("resume.txt", b"x")}).status_code == 422
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `resume-backend\.venv\Scripts\python.exe -m pytest resume-backend/tests/test_consultation_api.py -v`

- [ ] **Step 3: Implement routes and extraction guard**

```python
if uploaded.content_type != "application/pdf":
    raise HTTPException(status_code=422, detail="Only PDF files are supported")
```

- [ ] **Step 4: Run backend tests**

Run: `resume-backend\.venv\Scripts\python.exe -m pytest resume-backend/tests/test_consultation_api.py -v`

### Task 3: Persistent Frontend Session and API Types

**Files:**
- Modify: `resume-miniprogram/src/types/consultation.ts`
- Modify: `resume-miniprogram/src/stores/consultation.ts`
- Modify: `resume-miniprogram/src/services/resume-api.ts`
- Test: `resume-miniprogram/src/tests/consultation-flow.spec.ts`

**Interfaces:**
- `beginRoleConsultation(roleName): "identity-selection" | "reuse-identity"`
- `queryCareerAdvice()` and `extractResumePdf()`

- [ ] **Step 1: Write failing store tests**

```ts
store.selectIdentity("3")
expect(store.beginRoleConsultation("数据工程师")).toBe("reuse-identity")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node node_modules/vitest/vitest.mjs run src/tests/consultation-flow.spec.ts --pool=threads --poolOptions.threads.singleThread=true`

- [ ] **Step 3: Implement identity reuse and API mappings**

```ts
beginRoleConsultation(roleName: string): "identity-selection" | "reuse-identity" {
  this.pendingRoleName = roleName.trim()
  return this.identityCode ? "reuse-identity" : "identity-selection"
}
```

- [ ] **Step 4: Run frontend state tests**

Run: `node node_modules/vitest/vitest.mjs run src/tests/consultation-flow.spec.ts --pool=threads --poolOptions.threads.singleThread=true`

### Task 4: Mobile Panels and Runtime Regression

**Files:**
- Modify: `resume-miniprogram/src/pages/job-search/index.vue`
- Test: `resume-miniprogram/src/tests/consultation-flow.spec.ts`

**Interfaces:**
- Identity picker with change-identity action.
- Resume paste/PDF extraction entry.
- Advice topic picker and structured output.

- [ ] **Step 1: Add a failing API proxy regression test script**

```powershell
Invoke-WebRequest http://127.0.0.1:5173/api/consultation/job-analysis -Method Post
```

- [ ] **Step 2: Implement compact panels**

```vue
<picker :range="adviceTopics" range-key="label" @change="selectAdviceTopic" />
```

- [ ] **Step 3: Verify builds and proxy**

Run: `npm run build:h5`, `npm run build:mp-weixin`, then POST the identity
payload through `http://127.0.0.1:5173/api/consultation/job-analysis`.

### Task 5: Full Verification, Commit, Push, and Safe Cleanup

**Files:**
- Verify: all changed files

- [ ] **Step 1: Run full backend tests**

Run: `resume-backend\.venv\Scripts\python.exe -m pytest resume-backend/tests -v`

- [ ] **Step 2: Run full frontend tests**

Run: `node node_modules/vitest/vitest.mjs run --pool=threads --poolOptions.threads.singleThread=true`

- [ ] **Step 3: Build H5 and WeChat**

Run: `npm run build:h5` and `npm run build:mp-weixin`

- [ ] **Step 4: Commit and push**

```bash
git commit -m "feat: expand career consultation workflow"
git -c http.version=HTTP/1.1 push -u origin feature/ai-resume-demo
```

- [ ] **Step 5: Safely clean generated project artifacts**

Delete only `resume-miniprogram/dist`, `.pytest_cache`, and temporary test
exports after successful builds; do not delete source, `.git`, virtual
environments, database files, or user documents.
