# Career Growth and Match Report Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add structured career growth routes, truthful resume-to-job match reports, explicit risk guidance, and user custom-requirement support to the existing consultation workflow.

**Architecture:** Extend the existing Pydantic response contracts and deterministic consultation service without changing route URLs or existing fields. The mini-program maps the additive response fields and renders them within the existing job-search and resume-review page.

**Tech Stack:** FastAPI, Pydantic v2, Python pytest, Vue 3, Uni-App, Pinia, TypeScript, Vitest.

## Global Constraints

- Preserve all existing job-analysis, identity-plan, resume-review, PDF extraction, resume-draft, and CSV-independent business behavior.
- Never invent employers, schools, dates, projects, certificates, metrics, salaries, or completed user skills.
- Mark unknown resume evidence as `[待确认]`.
- Keep estimated market information labeled as estimates unless a verified live source is available.
- Do not automatically push, merge, rebase, or create a PR.

---

### Task 1: Add consultation contracts and mock-service coverage

**Files:**
- Modify: `resume-backend/app/schemas/consultation.py`
- Modify: `resume-backend/app/services/career_consultation.py`
- Modify: `resume-backend/tests/test_consultation_api.py`

**Interfaces:**
- Produces `CareerGrowthRoute`, `JobMatchReport`, `custom_requirement_notes`.
- Extends `build_job_consultation(job, identity_code, custom_requirement=None)`.
- Extends `build_resume_review(resume_text, identity_code, role_name, custom_requirement=None)`.

- [ ] **Step 1: Write failing API tests**

```python
def test_job_analysis_returns_complete_growth_route_and_custom_requirement_notes(api_client):
    data = assert_success(api_client.post(
        "/api/consultation/job-analysis",
        json={"role_name": "Data Engineer", "identity_code": "2", "custom_requirement": "优先杭州双休岗位"},
    ))
    assert [item["stage"] for item in data["career_growth_route"]["stages"]] == ["初级", "中级", "高级"]
    assert all(item["assessment_criteria"] for item in data["career_growth_route"]["stages"])
    assert "优先杭州双休岗位" in " ".join(data["custom_requirement_notes"])

def test_resume_review_returns_truthful_match_report(api_client):
    data = assert_success(api_client.post(
        "/api/consultation/resume-review",
        json={"resume_text": "负责 SQL 报表整理", "identity_code": "2", "role_name": "Data Engineer"},
    ))
    report = data["job_match_report"]
    assert 0 <= report["score"] <= 100
    assert report["priority_gaps"]
    assert "[待确认]" in data["optimized_resume_text"]
```

- [ ] **Step 2: Run the focused API test module and confirm it fails because the new response fields are absent**

Run: `resume-backend\.venv\Scripts\python.exe -m pytest resume-backend/tests/test_consultation_api.py -v`

- [ ] **Step 3: Add the Pydantic models, optional request fields, growth route, match-report calculation, and risk markers**

```python
class JobMatchReport(BaseModel):
    score: int = Field(ge=0, le=100)
    score_basis: list[str] = Field(min_length=1)
    matching_advantages: list[str] = Field(min_length=1)
    missing_skills: list[str] = Field(min_length=1)
    priority_gaps: list[PrioritySkillGap] = Field(min_length=1)
```

- [ ] **Step 4: Run the focused API test module and confirm it passes**

Run: `resume-backend\.venv\Scripts\python.exe -m pytest resume-backend/tests/test_consultation_api.py -v`

### Task 2: Wire the new fields through API and AI providers

**Files:**
- Modify: `resume-backend/app/api/consultation.py`
- Modify: `resume-backend/app/services/ai_client.py`
- Modify: `resume-backend/tests/test_consultation_ai_client.py`

**Interfaces:**
- API forwards `payload.custom_requirement`.
- `AIClient.build_job_consultation` and `AIClient.review_resume_text` accept the optional requirement.
- OpenAI-compatible prompts request all schema fields and safety constraints.

- [ ] **Step 1: Write a failing prompt-contract test**

```python
assert "career_growth_route" in captured_job_prompt
assert "job_match_report" in captured_resume_prompt
assert "custom_requirement_notes" in captured_resume_prompt
assert "Never invent" in captured_resume_prompt
```

- [ ] **Step 2: Run the AI-client test and confirm the contract test fails**

Run: `resume-backend\.venv\Scripts\python.exe -m pytest resume-backend/tests/test_consultation_ai_client.py -v`

- [ ] **Step 3: Forward the request field and update mock/OpenAI-compatible method signatures and prompts**

```python
async def review_resume_text(
    self,
    resume_text: str,
    identity_code: IdentityCode,
    role_name: str | None,
    custom_requirement: str | None = None,
) -> ResumeReviewResponse: ...
```

- [ ] **Step 4: Re-run the AI-client test and confirm it passes**

Run: `resume-backend\.venv\Scripts\python.exe -m pytest resume-backend/tests/test_consultation_ai_client.py -v`

### Task 3: Render growth routes, reports, risks, and custom requirements

**Files:**
- Modify: `resume-miniprogram/src/types/consultation.ts`
- Modify: `resume-miniprogram/src/services/resume-api.ts`
- Modify: `resume-miniprogram/src/pages/job-search/index.vue`

**Interfaces:**
- `JobConsultation.careerGrowthRoute`, `JobConsultation.customRequirementNotes`.
- `ResumeReview.jobMatchReport`, `ResumeReview.customRequirementNotes`.
- `queryJobConsultation(..., customRequirement?)` and `reviewResumeText(..., customRequirement?)`.

- [ ] **Step 1: Extend the TypeScript API response types before changing the template**

```ts
export interface JobMatchReport {
  score: number
  scoreBasis: string[]
  matchingAdvantages: string[]
  missingSkills: string[]
  priorityGaps: PrioritySkillGap[]
}
```

- [ ] **Step 2: Add request mapping and page state for `customRequirement`**

```ts
const customRequirement = ref("")
resumeReview.value = await reviewResumeText(text, consultation.identityCode, activeRole, customRequirement.value.trim())
```

- [ ] **Step 3: Render the route and report blocks, including visible `【需提升】` and risk markers**

```vue
<text class="result-title">## 职业晋升路线</text>
<view v-for="stage in jobConsultation.careerGrowthRoute.stages" :key="stage.stage" class="growth-stage">
  <text class="block-title">{{ stage.stage }}｜{{ stage.roleTitle }}</text>
  <text class="list-item">- 核心技能：{{ stage.coreSkills.join(" / ") }}</text>
</view>
```

- [ ] **Step 4: Run frontend unit tests and both production builds**

Run: `node node_modules/vitest/vitest.mjs run --pool=threads --poolOptions.threads.singleThread=true`

Run: `npm run build:h5`

Run: `npm run build:mp-weixin`

### Task 4: Full verification and local commit

**Files:**
- Verify all modified files from Tasks 1-3.

- [ ] **Step 1: Run full backend suite**

Run: `resume-backend\.venv\Scripts\python.exe -m pytest resume-backend/tests -v`

- [ ] **Step 2: Run full frontend suite and builds**

Run: `node node_modules/vitest/vitest.mjs run --pool=threads --poolOptions.threads.singleThread=true`

Run: `npm run build:h5`

Run: `npm run build:mp-weixin`

- [ ] **Step 3: Inspect whitespace and working-tree scope**

Run: `git diff --check`

- [ ] **Step 4: Create a local commit without pushing**

```bash
git add resume-backend resume-miniprogram docs/superpowers
git commit -m "feat: add career growth and match report"
```

## Self-Review

- The growth route, match-report score, gaps, learning actions, custom requirements, detailed risk markers, and existing identity plans all have implementation tasks.
- No new route replaces existing endpoints or removes old response fields.
- The score is explicitly a transparent coverage indicator, not an unsupported assessment of employability.
- Unknown user facts are consistently kept as `[待确认]`.
