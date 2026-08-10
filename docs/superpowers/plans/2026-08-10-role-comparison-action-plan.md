# Role Comparison and Action Plan Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let an anonymous user compare two to four locally known roles, see explainable fit and gaps, and select one weekly target without changing existing recommendation, draft, or export payloads.

**Architecture:** Extend the existing `CareerRecommender` with deterministic catalog-backed comparison output. Verified resume-evidence text may only raise a role skill score when it contains an existing required-skill phrase; it never invents outcomes. The Uni-App layer keeps comparison selection and weekly target in the existing `career` Pinia checkpoint and uses one new comparison page.

**Tech Stack:** FastAPI, Pydantic v2, SQLite repositories, pytest, Uni-App Vue 3, Pinia, TypeScript, Vitest.

## Global Constraints

- Do not add login, payment, recruitment-site crawling, automatic applications, or external job-market data.
- `POST /api/career/compare` accepts exactly 2-4 unique role names from the local role catalog.
- Existing `POST /api/career/recommend`, `ResumePayload` v1, draft records, CSV data, and Word/PDF exports remain unchanged.
- Matching scores are direction-comparison support only and must not claim a hiring probability, salary result, or market forecast.
- Only verified evidence can be used as supplementary skill evidence; unknown facts remain `[待确认]`.
- New pages must use the existing light mobile design and remain usable at 360px width.

---

### Task 1: Comparison schemas and deterministic recommender

**Files:**
- Modify: `resume-backend/app/schemas/career.py`
- Modify: `resume-backend/app/services/career_recommender.py`
- Create: `resume-backend/tests/test_career_comparison.py`

**Interfaces:**
- Produces `CareerComparisonRequest(client_id, role_names)`.
- Produces `CareerComparisonResponse(profile, items, common_strengths, recommendation_notice)`.
- Adds `CareerRecommender.compare(profile, roles, verified_evidence) -> CareerComparisonResponse`.

- [ ] **Step 1: Write failing comparison-service tests**

```python
def test_compare_returns_exact_roles_ranked_with_7_30_90_day_tasks(api_client):
    save_profile(api_client, client_id="compare-client", skills=["Python", "SQL"])
    response = api_client.post(
        "/api/career/compare",
        json={
            "client_id": "compare-client",
            "role_names": ["数据工程师", "数据分析师"],
        },
    )
    data = assert_success(response)

    assert [item["role"]["role_name"] for item in data["items"]] == [
        "数据工程师",
        "数据分析师",
    ]
    assert all(set(item["action_plan"]) == {"seven_day", "thirty_day", "ninety_day"} for item in data["items"])
    assert all(item["missing_skills"] for item in data["items"])
```

```python
def test_compare_rejects_duplicate_or_out_of_range_role_names(api_client):
    save_profile(api_client, client_id="validation-client", skills=[])

    duplicate = api_client.post(
        "/api/career/compare",
        json={"client_id": "validation-client", "role_names": ["数据工程师", "数据工程师"]},
    )
    assert duplicate.status_code == 422

    too_many = api_client.post(
        "/api/career/compare",
        json={"client_id": "validation-client", "role_names": ["数据工程师"] * 5},
    )
    assert too_many.status_code == 422
```

- [ ] **Step 2: Run the new test to verify it fails**

Run:

```powershell
cd resume-backend
.\.venv\Scripts\python.exe -m pytest tests/test_career_comparison.py -v
```

Expected: FAIL because the comparison route and response models do not exist.

- [ ] **Step 3: Add request and response models**

Add the following Pydantic interfaces:

```python
class CareerComparisonRequest(BaseModel):
    client_id: str = Field(min_length=1, max_length=120)
    role_names: list[str] = Field(min_length=2, max_length=4)

    @field_validator("role_names")
    @classmethod
    def normalize_unique_role_names(cls, values: list[str]) -> list[str]:
        normalized = _normalize_list(values)
        if len(normalized) != len(values):
            raise ValueError("role_names must be unique")
        if len(normalized) < 2:
            raise ValueError("role_names must contain at least two roles")
        return normalized
```

Create `ComparisonActionPlan` with `seven_day`, `thirty_day`, and `ninety_day` string lists. Create `CareerComparisonItem` containing the pre-existing role, total score, five-score breakdown, matching advantages, missing skills, alternatives, risk notice, and this action plan. Create `CareerComparisonResponse` with `profile`, `items`, `common_strengths`, and a non-predictive notice.

- [ ] **Step 4: Implement comparison using existing scoring**

Add a `compare` method to `CareerRecommender`. For every requested `RoleProfile`, call the existing `_score_role`, preserve its five `ScoreBreakdown` objects, and make these changes only in the comparison copy:

```python
supplementary = [
    skill
    for skill in role.required_skills
    if _normalized(skill) in verified_evidence_text
]
```

Treat only exact normalized existing skill phrases as additional skill evidence. Keep the total score capped at 100. Generate task phases with factual, verifiable wording:

```python
{
    "seven_day": [f"完成 {skill} 的基础练习，并保留代码、笔记或截图证据。"],
    "thirty_day": [f"围绕 {role.role_name} 完成一个小型练习项目，记录真实职责和过程。"],
    "ninety_day": [f"投递或参与与 {role.internship_roles[0]} 相关的真实机会，并复盘反馈。"],
}
```

For each item, set `risk_notice` to the local role entry-difficulty explanation plus a warning that the score is not an offer prediction. Derive `common_strengths` as the ordered intersection of item advantages; use an empty list when no advantage is common.

- [ ] **Step 5: Run comparison tests**

Run the command from Step 2.

Expected: PASS for ranking, phase task shape, duplicate validation, and local-only notice behavior.

- [ ] **Step 6: Commit**

```powershell
git add resume-backend/app/schemas/career.py resume-backend/app/services/career_recommender.py resume-backend/tests/test_career_comparison.py
git commit -m "feat: add deterministic role comparison service"
```

### Task 2: Comparison API and verified-evidence integration

**Files:**
- Modify: `resume-backend/app/api/career.py`
- Modify: `resume-backend/app/repositories/career_catalog.py`
- Modify: `resume-backend/tests/test_career_comparison.py`

**Interfaces:**
- Adds `CareerCatalogRepository.get_roles_by_names(role_names) -> list[RoleProfile]`.
- Adds `POST /api/career/compare`.
- Reads only `ResumeEvidenceRepository.list(client_id)` items where `verified` is true.

- [ ] **Step 1: Extend the failing API test with evidence behavior**

```python
def test_compare_uses_only_verified_existing_skill_evidence(api_client):
    save_profile(api_client, client_id="evidence-client", skills=[])
    api_client.post("/api/evidence", json=verified_python_evidence("evidence-client"))
    api_client.post("/api/evidence", json=unverified_sql_evidence("evidence-client"))

    data = assert_success(api_client.post(
        "/api/career/compare",
        json={"client_id": "evidence-client", "role_names": ["数据工程师", "数据分析师"]},
    ))
    skills_reason = next(
        part["reason"]
        for part in data["items"][0]["score_breakdown"]
        if part["key"] == "skills"
    )
    assert "Python" not in data["items"][0]["missing_skills"]
    assert "SQL" in data["items"][0]["missing_skills"]
    assert "已确认经历" in skills_reason
```

- [ ] **Step 2: Run the API test to verify it fails**

Run:

```powershell
cd resume-backend
.\.venv\Scripts\python.exe -m pytest tests/test_career_comparison.py -v
```

Expected: FAIL because the route cannot resolve role names or read evidence.

- [ ] **Step 3: Add exact role lookup**

Implement a catalog method that preserves request order and fails with a `ValueError` listing unknown local role names:

```python
def get_roles_by_names(self, role_names: list[str]) -> list[RoleProfile]:
    catalog = {role.role_name: role for role in self.list_roles()}
    unknown = [name for name in role_names if name not in catalog]
    if unknown:
        raise ValueError(f"Unknown role names: {', '.join(unknown)}")
    return [catalog[name] for name in role_names]
```

- [ ] **Step 4: Register the comparison route**

Add:

```python
@router.post("/api/career/compare")
async def career_compare(payload: CareerComparisonRequest, request: Request):
    profile = request.app.state.career_profile_repository.get(payload.client_id)
    roles = request.app.state.career_catalog_repository.get_roles_by_names(payload.role_names)
    evidence = request.app.state.evidence_repository.list(payload.client_id)
    verified = [item for item in evidence if item.verified]
    return success(
        request.app.state.career_recommender.compare(
            profile,
            roles,
            verified_evidence=verified,
        ).model_dump()
    )
```

Convert unknown roles to the existing `422` validation-envelope style rather than querying any external source.

- [ ] **Step 5: Run comparison tests**

Run the command from Step 2.

Expected: PASS; unverified evidence does not remove a missing skill.

- [ ] **Step 6: Commit**

```powershell
git add resume-backend/app/api/career.py resume-backend/app/repositories/career_catalog.py resume-backend/tests/test_career_comparison.py
git commit -m "feat: expose role comparison API"
```

### Task 3: Typed comparison client and career state

**Files:**
- Modify: `resume-miniprogram/src/types/career.ts`
- Modify: `resume-miniprogram/src/services/career-api.ts`
- Modify: `resume-miniprogram/src/stores/career.ts`
- Create: `resume-miniprogram/src/tests/career-comparison-api.spec.ts`
- Create: `resume-miniprogram/src/tests/career-comparison-store.spec.ts`

**Interfaces:**
- Produces `CareerComparisonItem`, `CareerComparisonResult`, `ComparisonActionPlan`.
- Adds `compareRoles(clientId, roleNames)`.
- Store exposes `comparisonRoleNames`, `weeklyTarget`, `toggleComparisonRole(roleName)`, `setWeeklyTarget(role)`.

- [ ] **Step 1: Write failing typed-client and store tests**

```ts
it("maps comparison response fields and preserves three action-plan phases", async () => {
  mockComparisonRequest()
  const result = await compareRoles("client-a", ["数据工程师", "数据分析师"])
  expect(result.items[0].actionPlan.sevenDay).toHaveLength(1)
  expect(result.items[0].riskNotice).toContain("录用")
})
```

```ts
it("limits role comparison selection to four unique roles", () => {
  const store = useCareerStore()
  expect(store.toggleComparisonRole("数据工程师")).toBe(true)
  expect(store.toggleComparisonRole("数据工程师")).toBe(true)
  expect(store.comparisonRoleNames).toEqual([])
  ;["数据工程师", "数据分析师", "数据治理工程师", "机器学习工程师"].forEach(
    (role) => expect(store.toggleComparisonRole(role)).toBe(true),
  )
  expect(store.toggleComparisonRole("产品经理")).toBe(false)
})
```

- [ ] **Step 2: Run frontend comparison tests to verify they fail**

Run:

```powershell
cd resume-miniprogram
npm run test:unit -- career-comparison
```

Expected: FAIL because comparison types, client mapping, and store actions do not exist.

- [ ] **Step 3: Add TypeScript mapping and store persistence**

Map backend snake_case fields to camelCase. Persist only role-name selections and the selected weekly target in the existing career checkpoint:

```ts
toggleComparisonRole(roleName: string): boolean {
  const index = this.comparisonRoleNames.indexOf(roleName)
  if (index >= 0) this.comparisonRoleNames.splice(index, 1)
  else if (this.comparisonRoleNames.length >= 4) return false
  else this.comparisonRoleNames.push(roleName)
  this.checkpoint()
  return true
}
```

`setWeeklyTarget` must checkpoint the selected `RoleRecommendation` or comparison item but must not automatically overwrite a resume draft.

- [ ] **Step 4: Run frontend comparison tests**

Run the command from Step 2.

Expected: PASS for API mapping, four-role cap, toggle behavior, and checkpoint state.

- [ ] **Step 5: Commit**

```powershell
git add resume-miniprogram/src/types/career.ts resume-miniprogram/src/services/career-api.ts resume-miniprogram/src/stores/career.ts resume-miniprogram/src/tests/career-comparison-api.spec.ts resume-miniprogram/src/tests/career-comparison-store.spec.ts
git commit -m "feat: add role comparison client and state"
```

### Task 4: Planner selection controls and comparison page

**Files:**
- Modify: `resume-miniprogram/src/pages/career-planner/index.vue`
- Create: `resume-miniprogram/src/pages/role-comparison/index.vue`
- Modify: `resume-miniprogram/src/pages.json`
- Create: `resume-miniprogram/src/tests/career-comparison-selection.spec.ts`

**Interfaces:**
- Planner provides a “加入对比” action per recommendation and never selects more than four roles.
- Comparison page loads `compareRoles`, exposes one weekly-target action, and does not mutate the resume.

- [ ] **Step 1: Write failing selection helper test**

```ts
it("requires two selected roles before opening comparison", () => {
  expect(canOpenComparison([])).toBe(false)
  expect(canOpenComparison(["数据工程师", "数据分析师"])).toBe(true)
})
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```powershell
cd resume-miniprogram
npm run test:unit -- career-comparison-selection
```

Expected: FAIL because the selection helper does not exist.

- [ ] **Step 3: Add the pure selection helper and planner controls**

Create `src/utils/role-comparison.ts`:

```ts
export const canOpenComparison = (roleNames: string[]): boolean =>
  roleNames.length >= 2 && roleNames.length <= 4
```

In every planner role card add a compact “加入对比” toggle. Display a comparison bar only when at least one role is selected; show `已选 N/4`. The “查看对比” button shows a non-destructive toast until two roles are selected, then navigates to `/pages/role-comparison/index`.

- [ ] **Step 4: Implement the comparison page**

On page load, request `compareRoles(getClientId(), careerStore.comparisonRoleNames)`. For each role card render total score, five existing score breakdown rows, matching advantages, missing skills, risk notice, and `sevenDay` / `thirtyDay` / `ninetyDay` action sections. Add “设为本周主目标” that calls `careerStore.setWeeklyTarget(item)` and shows a success toast. Include a clear notice that the comparison is local decision support, not a recruitment prediction.

- [ ] **Step 5: Run the selection test and full frontend suite**

Run:

```powershell
cd resume-miniprogram
npm run test:unit
```

Expected: PASS, including existing career planner and resume tests.

- [ ] **Step 6: Commit**

```powershell
git add resume-miniprogram/src/pages/career-planner/index.vue resume-miniprogram/src/pages/role-comparison/index.vue resume-miniprogram/src/pages.json resume-miniprogram/src/utils/role-comparison.ts resume-miniprogram/src/tests/career-comparison-selection.spec.ts
git commit -m "feat: add role comparison planning page"
```

### Task 5: Documentation and full phase verification

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Document role comparison boundaries**

Add one feature bullet and explain that comparison uses only the local role catalog, saved career profile, voluntary assessment, and verified evidence. State that scores are not hiring odds and that verified evidence is never altered by comparison.

- [ ] **Step 2: Run complete backend verification**

Run:

```powershell
cd resume-backend
.\.venv\Scripts\python.exe -m pytest tests -v
```

Expected: all tests pass; document the optional Chromium PDF skip if it occurs.

- [ ] **Step 3: Run complete frontend and production-build verification**

Run:

```powershell
cd resume-miniprogram
npm run test:unit
npm run build:h5
npm run build:mp-weixin
```

Expected: all frontend tests and both production builds pass.

- [ ] **Step 4: Commit**

```powershell
git add README.md
git commit -m "docs: explain local role comparison workflow"
```
