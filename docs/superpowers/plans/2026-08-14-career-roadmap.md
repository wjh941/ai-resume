# Interactive Career Roadmap Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add structured AI job planning, interactive dual-track promotion roadmaps, and user-scoped competency comparisons to the existing three-tier dashboard cards.

**Architecture:** Keep `career.py` as the career-planning API owner and add a single JWT-protected `/api/job/plan` contract. The route builds a user context from repositories keyed by the JWT `sub`, asks the configured AI client for a validated plan, and truncates paid-only detail according to `VipStatus`. The dashboard normalizes this payload into existing three-tier cards and keeps per-user interaction state through its scoped local-storage helper.

**Tech Stack:** FastAPI, Pydantic, existing AI client protocol, SQLite repositories, pytest, vanilla HTML/CSS/JavaScript, existing dashboard verifier.

## Global Constraints

- Retain JWT authentication, SQLite multi-user isolation, existing membership/payment logic, resume/export flows, deliveries, and evidence CRUD without destructive changes.
- The backend receives user identity only from `current_user_id`; no career-plan request body contains `user_id` or `client_id`.
- `expand_detail` is server-controlled cost reduction: Free is concise, Basic/Premium can receive detailed report and complete roadmap data.
- Use only native CSS and vanilla JavaScript. Do not add a chart CDN, a dependency, a stylesheet file, or a new visual system.
- Keep Sprint / Safe / Backup cards and current local Mock / Vite development behavior intact.
- Local interactive state must use the existing `resume-dashboard:{jwt-sub}:{business-key}` namespace and never claim legacy unscoped data.

---

### Task 1: Typed Job-Plan Contract and AI Client

**Files:**

- Modify: `resume-backend/app/schemas/career.py`
- Modify: `resume-backend/app/services/ai_client.py`
- Modify: `resume-backend/tests/test_support.py`
- Test: `resume-backend/tests/test_job_plan_api.py`

**Interfaces:**

- Produces `JobPlanRequest(role_name: str, expand_detail: bool)`.
- Produces `JobPlanResponse` with six named sections, `comparison_items`, `promotion_tracks`, and `action_plan`.
- Extends `AIClient.build_job_plan(role_name, profile, evidence, resume, assessment, expand_detail) -> JobPlanResponse`.

- [ ] **Step 1: Write the failing contract test**

```python
def test_job_plan_requires_bearer_auth(api_client):
    response = api_client.post("/api/job/plan", json={"role_name": "Data Engineer"})
    assert response.status_code == 401
```

- [ ] **Step 2: Run test to verify it fails**

Run: `resume-backend/.venv/Scripts/python.exe -m pytest tests/test_job_plan_api.py::test_job_plan_requires_bearer_auth -q`

Expected: FAIL because `/api/job/plan` is not registered.

- [ ] **Step 3: Add the models and AI protocol method**

```python
class JobPlanRequest(BaseModel):
    role_name: str = Field(min_length=1, max_length=120)
    expand_detail: bool = False

class JobPlanResponse(BaseModel):
    role_name: str
    report_scope: Literal["brief", "detailed"]
    sections: list[JobPlanSection] = Field(min_length=6, max_length=6)
    comparison_items: list[CareerPlanComparisonItem]
    promotion_tracks: list[PromotionTrack]
    action_plan: ComparisonActionPlan
```

Make `TestAIClient.build_job_plan` return deterministic six sections, two tracks, comparison items, and three action arrays so endpoint tests do not contact an LLM.

- [ ] **Step 4: Validate the typed fixture in isolation**

Run: `resume-backend/.venv/Scripts/python.exe -m pytest tests/test_job_plan_api.py -q`

Expected: route assertions still fail, but import and fixture construction succeed without model validation errors.

- [ ] **Step 5: Commit the contract layer**

```bash
git add resume-backend/app/schemas/career.py resume-backend/app/services/ai_client.py resume-backend/tests/test_support.py resume-backend/tests/test_job_plan_api.py
git commit -m "feat: add structured job plan contract"
```

### Task 2: JWT-Owned Plan Generation and Tier Projection

**Files:**

- Modify: `resume-backend/app/api/career.py`
- Modify: `resume-backend/app/services/ai_client.py`
- Modify: `resume-backend/tests/test_job_plan_api.py`

**Interfaces:**

- `POST /api/job/plan` accepts `JobPlanRequest`, injects `current_user_id` and `VipStatus`, and returns `success(JobPlanResponse.model_dump())`.
- `project_job_plan_for_vip(plan, vip)` returns the same shape and limits only paid content for Free users.

- [ ] **Step 1: Expand failing endpoint coverage**

```python
def test_free_job_plan_is_forced_to_brief_and_owned_by_jwt(api_client, auth_headers):
    response = api_client.post(
        "/api/job/plan",
        headers=auth_headers("13800000001"),
        json={"role_name": "Data Engineer", "expand_detail": True},
    )
    data = assert_success(response)
    assert data["report_scope"] == "brief"
    assert len(data["promotion_tracks"][0]["nodes"]) == 2

def test_basic_job_plan_gets_detailed_report(api_client, auth_headers, make_basic_member):
    make_basic_member("13800000002")
    response = api_client.post(
        "/api/job/plan",
        headers=auth_headers("13800000002"),
        json={"role_name": "Data Engineer", "expand_detail": True},
    )
    assert assert_success(response)["report_scope"] == "detailed"
```

- [ ] **Step 2: Run the endpoint tests to verify failure**

Run: `resume-backend/.venv/Scripts/python.exe -m pytest tests/test_job_plan_api.py -q`

Expected: FAIL because the route and tier projection do not exist.

- [ ] **Step 3: Implement user-owned context gathering and projection**

```python
@router.post("/api/job/plan")
async def job_plan(payload: JobPlanRequest, request: Request,
                   user_id: str = Depends(current_user_id),
                   vip: VipStatus = Depends(get_current_vip)):
    profile = request.app.state.career_profile_repository.get(user_id)
    evidence = request.app.state.evidence_repository.list(user_id)
    plan = await request.app.state.ai_client.build_job_plan(
        payload.role_name, profile.model_dump(),
        [item.model_dump() for item in evidence if item.verified],
        latest_resume_payload(request, user_id), assessment_result(request, user_id),
        payload.expand_detail and vip.allows("full_job_report"),
    )
    return success(project_job_plan_for_vip(plan, vip).model_dump())
```

Use repository calls with the JWT-derived `user_id` only. Catch absent assessment/draft as `None`; do not make an unrelated user profile or evidence record visible.

- [ ] **Step 4: Implement OpenAI-compatible structured generation**

```python
content = await self._chat_completion(
    "Return only valid JSON matching JobPlanResponse. Use supplied evidence only; do not invent candidate facts.",
    json.dumps(context, ensure_ascii=False),
)
return JobPlanResponse.model_validate_json(content)
```

Map invalid JSON through existing `AIServiceError("ai_invalid_response", ...)` so `main.py` retains the friendly structured failure response.

- [ ] **Step 5: Run focused tests to verify pass**

Run: `resume-backend/.venv/Scripts/python.exe -m pytest tests/test_job_plan_api.py tests/test_career_comparison.py -q`

Expected: PASS, including JWT rejection, Free concise projection, Basic detail, and user ownership.

- [ ] **Step 6: Commit the API**

```bash
git add resume-backend/app/api/career.py resume-backend/app/services/ai_client.py resume-backend/tests/test_job_plan_api.py
git commit -m "feat: add authenticated job planning api"
```

### Task 3: Dashboard Plan State and Testable Helpers

**Files:**

- Modify: `premium-dashboard.html`
- Modify: `scripts/verify-premium-dashboard.mjs`

**Interfaces:**

- Adds local keys `resume-dashboard-career-plan-cache`, `resume-dashboard-career-plan-progress`, and `resume-dashboard-career-plan-history`.
- Adds pure helpers `normalizeCareerPlan`, `calculatePlanProgress`, `buildGapEvidenceDraft`, and `careerPlanText`.
- Adds `requestCareerPlan(roleName, expandDetail)` through the existing authenticated `apiOrMock` wrapper.

- [ ] **Step 1: Add failing verifier assertions**

```javascript
assert.equal(sandbox.normalizeCareerPlan({ role_name: 'Role' }).sections.length, 6);
assert.equal(sandbox.calculatePlanProgress([{ done: true }, { done: false }]), 50);
assert.match(sandbox.buildGapEvidenceDraft('SQL').title, /待确认/);
assert.match(html, /\/api\/job\/plan/);
```

- [ ] **Step 2: Run verifier to verify failure**

Run: `node scripts/verify-premium-dashboard.mjs`

Expected: FAIL because plan helpers and endpoint binding are absent.

- [ ] **Step 3: Implement scoped state and mock normalization**

```javascript
function requestCareerPlan(roleName, expandDetail) {
  return apiOrMock('/api/job/plan', {
    method: 'POST', body: JSON.stringify({ role_name: roleName, expand_detail: expandDetail })
  }, buildMockCareerPlan(roleName, expandDetail), 'career plan');
}
```

Use `saveLocal` and `loadLocal` exclusively so the existing JWT namespace remains the only persistent location for interactive records.

- [ ] **Step 4: Run verifier to verify pass**

Run: `node scripts/verify-premium-dashboard.mjs`

Expected: PASS with deterministic helper assertions and no additional dashboard scripts.

- [ ] **Step 5: Commit state plumbing**

```bash
git add premium-dashboard.html scripts/verify-premium-dashboard.mjs
git commit -m "feat: add scoped career plan state"
```

### Task 4: Structured Report, Roadmap, Comparison Modal, and Action Progress UI

**Files:**

- Modify: `premium-dashboard.html`

**Interfaces:**

- `renderTiers()` keeps three existing cards and renders `renderCareerPlanCard(job, index)` inside each.
- `openCareerComparison(roleName)` renders the desktop two-column/mobile-stack comparison modal.
- `appendRoadmapTask(roleName, trackKey, node)` deduplicates and saves a task, while `toggleCareerTask(roleName, taskId)` recomputes progress.

- [ ] **Step 1: Add minimal reusable CSS classes before markup**

```css
.career-report-grid { display: grid; gap: 9px; }
.roadmap-track { display: grid; grid-auto-flow: column; grid-auto-columns: minmax(172px, 1fr); overflow-x: auto; }
.career-comparison-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; }
@media (max-width: 640px) { .career-comparison-grid { grid-template-columns: 1fr; } }
```

Use only `var(--*)` color and shadow tokens, fixed card dimensions where needed, and an existing `transition: var(--ease)` for focus/hover behavior.

- [ ] **Step 2: Render six collapsible report sections and progress blocks**

```javascript
function renderPlanActions(roleName, plan) {
  const progress = calculatePlanProgress(plan.tasks);
  return `<div class="plan-progress"><span style="width:${progress}%"></span></div>`;
}
```

Render all six named section cards. Each skill item includes a visual percentage fill and semantic tag. Completed tasks use `done` styling; overdue status is calculated only for incomplete tasks with dates before today.

- [ ] **Step 3: Add roadmap interactions and paid/full projection**

```javascript
button.addEventListener('click', () => appendRoadmapTask(roleName, trackKey, node));
trackToggle.addEventListener('click', () => renderTiers());
```

Free users retain a concise node preview and upgrade affordance. Basic/Premium users can switch technical/management tracks and see complete tooltip content; backend remains the authority if cached UI state is stale.

- [ ] **Step 4: Add comparison modal and evidence shortcut**

```javascript
function buildGapEvidenceDraft(skill) {
  return { id: crypto.randomUUID(), kind: 'project', title: `[待确认] ${skill} 相关经历`, verified: false, tags: [skill] };
}
```

The missing-skill handler appends this draft to the current user state, persists via established evidence workflow, switches to the evidence page, and shows a precise toast. Copy uses existing `copyText`; history is written with `saveLocal`.

- [ ] **Step 5: Run dashboard verifier and build**

Run: `node scripts/verify-premium-dashboard.mjs`

Run: `npm.cmd run build:h5`

Expected: both commands PASS; the dashboard keeps one inline script and the H5 build accepts the modified HTML.

- [ ] **Step 6: Commit UI integration**

```bash
git add premium-dashboard.html scripts/verify-premium-dashboard.mjs
git commit -m "feat: add interactive career planning dashboard"
```

### Task 5: Release Verification and Delivery

**Files:**

- Modify only files required by concrete verification or review findings.

- [ ] **Step 1: Run all automated verification**

Run: `resume-backend/.venv/Scripts/python.exe -m pytest -p no:cacheprovider tests -q`

Run: `node scripts/verify-premium-dashboard.mjs`

Run: `npm.cmd run build:h5`

Run: `git diff --check`

Expected: all commands exit 0; `git diff --check` reports no whitespace errors.

- [ ] **Step 2: Perform the single Impeccable detector pass**

Run: `node C:/Users/16102/.codex/skills/impeccable/scripts/detect.mjs --json premium-dashboard.html`

Expected: no blocking detector violations. Address all concrete findings in one focused patch.

- [ ] **Step 3: Review and re-verify**

Obtain an independent code-review pass covering authorization ownership, Free-to-paid projection, storage isolation, XSS escaping in generated markup, and mobile layout. Apply only verified findings, then re-run every affected command from Step 1.

- [ ] **Step 4: Commit and push the release**

```bash
git add premium-dashboard.html resume-backend/app/api/career.py resume-backend/app/schemas/career.py resume-backend/app/services/ai_client.py resume-backend/tests/test_support.py resume-backend/tests/test_job_plan_api.py scripts/verify-premium-dashboard.mjs docs/superpowers
git commit -m "feat: add interactive career roadmap planning"
git push origin feature/ai-resume-demo
```

## Plan Self-Review

- Spec coverage: Tasks 1-2 cover the authenticated structured API, LLM prompt, user-only repository reads, `expand_detail`, and membership projection. Tasks 3-4 cover namespaced local state, six report sections, native dual-track timeline, task progression, comparison modal, copy, history, mobile behavior, and evidence shortcut. Task 5 covers detector, test suite, review, commit, and push.
- Placeholder scan: the plan contains no unresolved implementation markers; all route names, helper names, models, state keys, and verification commands are defined in the relevant task.
- Type consistency: `JobPlanRequest`, `JobPlanResponse`, `build_job_plan`, `normalizeCareerPlan`, `calculatePlanProgress`, `buildGapEvidenceDraft`, `appendRoadmapTask`, and `openCareerComparison` use identical names across producer and consumer tasks.

