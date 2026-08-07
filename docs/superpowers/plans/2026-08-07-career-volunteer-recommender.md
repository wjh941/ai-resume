# 求职志愿规划系统 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an explainable career-volunteer planner that stores a user's major and preferences, evaluates at least 200 curated roles, and returns stretch, stable, and safe job recommendations without claiming offer probability.

**Architecture:** A static, curated role-and-major seed module initializes SQLite tables used by search and recommendation services. A deterministic recommender calculates professional, skill, feasibility, preference, and neutral market-signal scores. A new Uni-App planner page persists a career profile, displays tiered recommendations, and hands a selected role to the existing resume workflow.

**Tech Stack:** Python 3.11, FastAPI, Pydantic, SQLite, Vue 3, Uni-App, Pinia, Vitest, pytest.

## Global Constraints

- Do not implement crawling, batch collection, login bypasses, or anti-bot bypasses for any recruitment platform.
- Do not claim offer probability, salary guarantees, or fabricated user facts.
- Keep existing job analysis, resume review, drafts, exports, CSV formats, and optional Tavily market-search behavior compatible.
- Keep user-entered resume data unchanged; generated unknown resume details remain `[待确认]`.
- Seed at least 200 standard roles across exactly 12 role families.
- Tier results use `stretch`, `stable`, and `safe`; a role cannot appear in more than one tier.
- Do not push, merge, or create a Pull Request automatically.

---

## File Structure

| File | Responsibility |
| --- | --- |
| `resume-backend/app/services/career_catalog.py` | Static role-family, role, and major seed definitions. |
| `resume-backend/app/schemas/career.py` | Career-profile, role-detail, score, recommendation, and API request/response contracts. |
| `resume-backend/app/repositories/career_catalog.py` | SQLite read repository for role and major profiles. |
| `resume-backend/app/repositories/career_profiles.py` | SQLite persistence for one career profile per `client_id`. |
| `resume-backend/app/services/career_recommender.py` | Deterministic scoring, tiering, major report, and action-plan generation. |
| `resume-backend/app/api/career.py` | Role/major suggestion, family list, profile persistence, and recommendation endpoints. |
| `resume-backend/app/db.py` | Schema migrations and catalog initialization. |
| `resume-backend/main.py` | Register career repository, recommender, and router in app state. |
| `resume-backend/tests/test_career_api.py` | End-to-end API and persistence regression tests. |
| `resume-backend/tests/test_career_recommender.py` | Pure deterministic scoring and non-overlap tier tests. |
| `resume-miniprogram/src/types/career.ts` | Frontend contracts for profile and recommendation responses. |
| `resume-miniprogram/src/services/career-api.ts` | API request/mapping functions for the planner. |
| `resume-miniprogram/src/stores/career.ts` | Local career-profile checkpoint and selected-role state. |
| `resume-miniprogram/src/pages/career-planner/index.vue` | Mobile career-volunteer profile and tiered-results page. |
| `resume-miniprogram/src/pages/job-search/index.vue` | Entry link to the planner, without removing existing search flow. |
| `resume-miniprogram/src/pages.json` | Register the planner page. |
| `resume-miniprogram/src/utils/resume-autofill.ts` | Add optional major context to generated safe project/internship drafts. |
| `resume-miniprogram/src/tests/career-api.spec.ts` | API mapper tests. |
| `resume-miniprogram/src/tests/career-store.spec.ts` | Career store persistence tests. |

---

### Task 1: Add failing backend tests for catalog scale and profile APIs

**Files:**
- Create: `resume-backend/tests/test_career_api.py`
- Modify: `resume-backend/tests/conftest.py`

**Interfaces:**
- Consumes: FastAPI `api_client` fixture.
- Produces: Required behavior for `/api/role/families`, `/api/role/suggestions`, `/api/major/suggestions`, `/api/career/profile/save`, `/api/career/profile`, and `/api/career/recommend`.

- [ ] **Step 1: Write the failing catalog and profile API tests**

```python
def test_role_catalog_has_twelve_families_and_at_least_two_hundred_roles(api_client):
    families = assert_success(api_client.get("/api/role/families"))

    assert len(families["items"]) == 12
    assert sum(item["role_count"] for item in families["items"]) >= 200
    assert {"软件研发", "数据与数据平台", "市场、品牌与增长"}.issubset(
        {item["name"] for item in families["items"]}
    )


def test_career_profile_round_trip_and_major_suggestions(api_client):
    payload = {
        "client_id": "career-client",
        "identity_code": "2",
        "major": "计算机科学与技术",
        "education_level": "本科",
        "skills": ["Python", "SQL"],
        "industry_preferences": ["互联网"],
        "work_types": ["全职"],
    }
    saved = assert_success(api_client.post("/api/career/profile/save", json=payload))
    loaded = assert_success(api_client.get("/api/career/profile", params={"client_id": "career-client"}))
    majors = assert_success(api_client.get("/api/major/suggestions", params={"q": "计算机"}))

    assert saved["major"] == "计算机科学与技术"
    assert loaded["skills"] == ["Python", "SQL"]
    assert any(item["major_name"] == "计算机科学与技术" for item in majors["items"])
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:

```powershell
resume-backend\.venv\Scripts\python.exe -m pytest resume-backend/tests/test_career_api.py -v
```

Expected: `404 Not Found` for career endpoints.

- [ ] **Step 3: Commit the failing tests**

```powershell
git add resume-backend/tests/test_career_api.py
git commit -m "test: define career profile API contract"
```

### Task 2: Build catalog seed data and SQLite initialization

**Files:**
- Create: `resume-backend/app/services/career_catalog.py`
- Modify: `resume-backend/app/db.py`
- Test: `resume-backend/tests/test_career_api.py`

**Interfaces:**
- Produces:

```python
ROLE_FAMILIES: tuple[dict[str, str], ...]
ROLE_SEEDS: tuple[RoleSeed, ...]
MAJOR_SEEDS: tuple[MajorSeed, ...]

def seed_career_catalog(connection: sqlite3.Connection) -> None: ...
```

- [ ] **Step 1: Add a failing assertion for role-family coverage and aliases**

```python
def test_role_suggestions_match_family_aliases(api_client):
    data = assert_success(api_client.get("/api/role/suggestions", params={"q": "数据", "limit": 20}))
    family_by_name = {item["role_name"]: item["family"] for item in data["items"]}

    assert {"数据工程师", "数据分析师", "数据治理工程师"}.issubset(family_by_name)
    assert family_by_name["数据工程师"] == "数据与数据平台"
    assert family_by_name["数据标注专员"] == "人工智能与算法"
```

- [ ] **Step 2: Run the single new test**

Run:

```powershell
resume-backend\.venv\Scripts\python.exe -m pytest resume-backend/tests/test_career_api.py::test_role_suggestions_match_family_aliases -v
```

Expected: FAIL because `role_profile` does not exist.

- [ ] **Step 3: Add focused seed structures**

```python
@dataclass(frozen=True)
class RoleSeed:
    role_name: str
    family: str
    aliases: tuple[str, ...]
    recommended_majors: tuple[str, ...]
    adjacent_majors: tuple[str, ...]
    relevant_courses: tuple[str, ...]
    required_skills: tuple[str, ...]
    entry_skills: tuple[str, ...]
    alternative_roles: tuple[str, ...]
    internship_roles: tuple[str, ...]
    entry_difficulty: int
    industry_tags: tuple[str, ...]
    description: str
```

Define 12 family records and the following 204 explicit role names. Use family defaults for majors, entry skills, and industries, with targeted overrides for representative roles such as 数据工程师、数据分析师、AI Agent工程师、产品经理、UI设计师 and 财务专员. Do not generate role names by concatenating words.

```python
FAMILY_ROLE_NAMES = {
    "软件研发": (
        "后端开发工程师", "前端开发工程师", "全栈开发工程师", "移动端开发工程师",
        "iOS开发工程师", "Android开发工程师", "客户端开发工程师", "Java开发工程师",
        "Python开发工程师", "Go开发工程师", "C++开发工程师", ".NET开发工程师",
        "嵌入式软件工程师", "游戏开发工程师", "区块链开发工程师", "音视频开发工程师",
        "低代码开发工程师",
    ),
    "人工智能与算法": (
        "算法工程师", "机器学习工程师", "深度学习工程师", "计算机视觉工程师",
        "自然语言处理工程师", "推荐算法工程师", "搜索算法工程师", "大模型工程师",
        "AI Agent工程师", "MLOps工程师", "AI平台工程师", "数据挖掘工程师",
        "语音算法工程师", "AIGC工程师", "机器人算法工程师", "强化学习工程师",
        "AI应用工程师", "数据标注专员",
    ),
    "数据与数据平台": (
        "数据工程师", "大数据开发工程师", "数据仓库工程师", "ETL工程师",
        "数据分析师", "BI分析师", "数据科学家", "数据库运维工程师",
        "数据治理工程师", "数据质量工程师", "数据清洗专员",
        "数据架构师", "数据库开发工程师", "实时计算工程师", "数据采集工程师",
        "主数据工程师",
    ),
    "测试与质量工程": (
        "测试开发工程师", "自动化测试工程师", "软件测试工程师", "性能测试工程师",
        "安全测试工程师", "测试架构师", "质量工程师", "质量保证专员",
        "移动端测试工程师", "游戏测试工程师", "嵌入式测试工程师", "硬件测试工程师",
        "可靠性工程师", "认证测试工程师", "测试项目经理", "用户体验测试工程师",
        "测试数据工程师",
    ),
    "云计算、运维与安全": (
        "运维开发工程师", "SRE工程师", "云平台工程师", "DevOps工程师",
        "网络工程师", "系统运维工程师", "Linux运维工程师", "中间件工程师",
        "容器云工程师", "云安全工程师", "信息安全工程师", "网络安全工程师",
        "渗透测试工程师", "安全运营工程师", "安全架构师", "灾备工程师", "IT支持工程师",
    ),
    "产品、项目与解决方案": (
        "产品经理", "数据产品经理", "AI产品经理", "商业产品经理", "增长产品经理",
        "用户研究员", "项目经理", "PMO项目专员", "解决方案工程师", "售前技术顾问",
        "实施顾问", "ERP实施顾问", "数字化咨询顾问", "IT咨询顾问", "业务分析师",
        "需求分析师", "产品运营专员",
    ),
    "设计与内容创意": (
        "UI设计师", "UX设计师", "交互设计师", "视觉设计师", "平面设计师",
        "品牌设计师", "插画师", "动画设计师", "视频剪辑师", "游戏美术设计师",
        "3D设计师", "工业设计师", "包装设计师", "室内设计师", "服装设计师",
        "摄影师", "内容策划",
    ),
    "市场、品牌与增长": (
        "市场专员", "品牌专员", "新媒体运营", "内容运营", "SEO专员", "SEM专员",
        "广告投放专员", "社交媒体运营", "公关专员", "活动策划", "用户增长专员",
        "市场调研专员", "海外市场专员", "短视频运营", "私域运营", "CRM运营专员",
        "直播运营",
    ),
    "运营、电商与客户成功": (
        "电商运营", "店铺运营", "类目运营", "供应链运营", "用户运营", "社区运营",
        "商家运营", "策略运营", "平台运营", "客服专员", "客户成功经理", "物流运营",
        "采购专员", "订单运营专员", "仓储运营专员", "风控运营专员", "游戏运营",
    ),
    "销售、商务与供应链": (
        "销售代表", "大客户销售", "客户经理", "渠道销售", "商务拓展专员", "销售运营专员",
        "销售培训师", "招商主管", "外贸业务员", "跨境电商销售", "供应链采购经理",
        "供应链计划专员", "物流规划专员", "采购工程师", "招投标专员", "合同专员",
        "商务经理",
    ),
    "财务、法务、人力与行政": (
        "财务专员", "会计", "审计专员", "税务专员", "出纳", "资金专员", "法务专员",
        "合规专员", "知识产权专员", "HRBP", "招聘专员", "培训专员", "绩效专员",
        "薪酬专员", "行政专员", "总经理助理", "人事专员",
    ),
    "机械、电子、制造、能源与生物医药": (
        "机械工程师", "结构工程师", "电气工程师", "电子工程师", "硬件工程师",
        "PCB工程师", "自动化工程师", "控制工程师", "工艺工程师", "生产工程师",
        "设备工程师", "制造质量工程师", "研发工程师", "生物医药研发专员",
        "临床协调员", "医药代表", "环保工程师",
    ),
}
```

- [ ] **Step 4: Add database schema and idempotent seed**

```sql
CREATE TABLE IF NOT EXISTS role_profile (
    role_name TEXT PRIMARY KEY,
    family TEXT NOT NULL,
    aliases_json TEXT NOT NULL,
    recommended_majors_json TEXT NOT NULL,
    adjacent_majors_json TEXT NOT NULL,
    relevant_courses_json TEXT NOT NULL,
    required_skills_json TEXT NOT NULL,
    entry_skills_json TEXT NOT NULL,
    alternative_roles_json TEXT NOT NULL,
    internship_roles_json TEXT NOT NULL,
    entry_difficulty INTEGER NOT NULL CHECK (entry_difficulty BETWEEN 1 AND 5),
    industry_tags_json TEXT NOT NULL,
    description TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS major_catalog (
    major_name TEXT PRIMARY KEY,
    category TEXT NOT NULL,
    aliases_json TEXT NOT NULL,
    related_families_json TEXT NOT NULL,
    transferable_skills_json TEXT NOT NULL
);
```

Call `seed_career_catalog(connection)` from `initialize_database`. Derive additional `job_catalog` seed rows from `ROLE_SEEDS` only when a role is not already present, preserving the current search API.

- [ ] **Step 5: Run catalog API tests**

Run:

```powershell
resume-backend\.venv\Scripts\python.exe -m pytest resume-backend/tests/test_career_api.py -v
```

Expected: catalog tests still fail only because the router is not registered.

- [ ] **Step 6: Commit the seed and schema**

```powershell
git add resume-backend/app/services/career_catalog.py resume-backend/app/db.py
git commit -m "feat: add career role and major catalog"
```

### Task 3: Implement profile repository, schemas, and catalog/profile API

**Files:**
- Create: `resume-backend/app/schemas/career.py`
- Create: `resume-backend/app/repositories/career_catalog.py`
- Create: `resume-backend/app/repositories/career_profiles.py`
- Create: `resume-backend/app/api/career.py`
- Modify: `resume-backend/main.py`
- Test: `resume-backend/tests/test_career_api.py`

**Interfaces:**
- Produces:

```python
class CareerProfilePayload(BaseModel):
    client_id: str
    identity_code: IdentityCode
    major: str
    education_level: str
    graduation_year: int | None
    city_preferences: list[str]
    minimum_salary: str | None
    industry_preferences: list[str]
    work_types: list[str]
    skills: list[str]
    draft_id: str | None

class CareerProfileRepository:
    def save(self, profile: CareerProfilePayload) -> CareerProfilePayload: ...
    def get(self, client_id: str) -> CareerProfilePayload | None: ...

class CareerCatalogRepository:
    def list_families(self) -> list[RoleFamilySummary]: ...
    def search_roles(self, query: str, limit: int) -> list[RoleSummary]: ...
    def search_majors(self, query: str, limit: int) -> list[MajorSummary]: ...
    def list_roles(self) -> list[RoleProfile]: ...
```

- [ ] **Step 1: Add failing not-found and normalization tests**

```python
def test_unknown_career_profile_returns_not_found(api_client):
    response = api_client.get("/api/career/profile", params={"client_id": "missing"})

    assert response.status_code == 404


def test_cross_major_profile_is_saved_without_rejecting_user_input(api_client):
    data = assert_success(api_client.post("/api/career/profile/save", json={
        "client_id": "career-client",
        "identity_code": "5",
        "major": "跨专业/专业不限",
        "education_level": "本科",
        "skills": [],
        "industry_preferences": [],
        "work_types": [],
    }))

    assert data["major"] == "跨专业/专业不限"
```

- [ ] **Step 2: Run the tests to verify failure**

Run:

```powershell
resume-backend\.venv\Scripts\python.exe -m pytest resume-backend/tests/test_career_api.py -v
```

Expected: FAIL because profile repository and routes are absent.

- [ ] **Step 3: Add the `career_profile` schema and repository**

Use the existing `DraftRepository` conventions for the profile repository: JSON payload, UTC timestamps, one row per `client_id`, and no cross-client reads. Keep SQL that reads `role_profile` and `major_catalog` in `CareerCatalogRepository`, not in routers or the recommender.

- [ ] **Step 4: Add routers**

```python
@router.get("/api/role/families")
async def list_role_families(request: Request): ...

@router.get("/api/role/suggestions")
async def list_role_suggestions(request: Request, q: str = "", limit: int = 12): ...

@router.get("/api/major/suggestions")
async def list_major_suggestions(request: Request, q: str = "", limit: int = 12): ...

@router.post("/api/career/profile/save")
async def save_career_profile(payload: CareerProfilePayload, request: Request): ...

@router.get("/api/career/profile")
async def get_career_profile(client_id: str, request: Request): ...
```

Raise the existing `DraftNotFoundError` equivalent only for missing career profiles through a dedicated `CareerProfileNotFoundError`, mapped to the existing `not_found` envelope in `main.py`.

- [ ] **Step 5: Run API tests to verify pass**

Run:

```powershell
resume-backend\.venv\Scripts\python.exe -m pytest resume-backend/tests/test_career_api.py -v
```

Expected: PASS for catalog, major, profile round-trip, and missing-profile tests.

- [ ] **Step 6: Commit**

```powershell
git add resume-backend/app/schemas/career.py resume-backend/app/repositories/career_catalog.py resume-backend/app/repositories/career_profiles.py resume-backend/app/api/career.py resume-backend/main.py resume-backend/tests/test_career_api.py
git commit -m "feat: add career profile catalog APIs"
```

### Task 4: Implement deterministic recommendation scoring and tiers

**Files:**
- Create: `resume-backend/app/services/career_recommender.py`
- Modify: `resume-backend/app/schemas/career.py`
- Modify: `resume-backend/app/api/career.py`
- Create: `resume-backend/tests/test_career_recommender.py`
- Modify: `resume-backend/tests/test_career_api.py`

**Interfaces:**
- Produces:

```python
class CareerRecommender:
    def recommend(self, profile: CareerProfilePayload) -> CareerRecommendationResponse: ...

class RoleRecommendation(BaseModel):
    role_name: str
    family: str
    tier: Literal["stretch", "stable", "safe"]
    total_score: int
    score_breakdown: list[ScoreBreakdown]
    matching_level: Literal["high", "transferable", "needs_upskilling", "long_shot"]
    recommendation_reasons: list[str]
    missing_skills: list[str]
    reusable_evidence: list[str]
    seven_day_actions: list[str]
    thirty_day_actions: list[str]
    alternative_roles: list[str]
```

- [ ] **Step 1: Write failing deterministic scoring tests**

```python
def test_computer_science_profile_ranks_data_engineer_as_stable():
    recommender = build_test_recommender()
    result = recommender.recommend(
        CareerProfilePayload(
            client_id="client",
            identity_code="2",
            major="计算机科学与技术",
            education_level="本科",
            skills=["Python", "SQL", "数据结构"],
            industry_preferences=["互联网"],
            work_types=["全职"],
        )
    )

    stable_names = {item.role_name for item in result.tiers.stable}
    assert "数据工程师" in stable_names
    assert all(item.total_score <= 100 for item in result.tiers.stable)


def test_recommendation_tiers_do_not_repeat_roles():
    result = build_test_recommender().recommend(make_cross_major_profile())
    names = [item.role_name for tier in result.tiers.model_dump().values() for item in tier]

    assert len(names) == len(set(names))
```

- [ ] **Step 2: Run the recommender tests to verify failure**

Run:

```powershell
resume-backend\.venv\Scripts\python.exe -m pytest resume-backend/tests/test_career_recommender.py -v
```

Expected: FAIL because `CareerRecommender` does not exist.

- [ ] **Step 3: Implement score functions**

```python
def score_major(profile: CareerProfilePayload, role: RoleProfile) -> ScoreBreakdown: ...
def score_skills(profile: CareerProfilePayload, role: RoleProfile) -> ScoreBreakdown: ...
def score_feasibility(profile: CareerProfilePayload, role: RoleProfile) -> ScoreBreakdown: ...
def score_preferences(profile: CareerProfilePayload, role: RoleProfile) -> ScoreBreakdown: ...
def score_market_signal() -> ScoreBreakdown: ...
```

Use weights 30, 25, 20, 15, and 10. `score_market_signal()` returns `5/10` with the explanation “未接入授权的城市薪资职位数据，使用中性分，不代表市场热度” unless a future authorized provider supplies normalized evidence.

- [ ] **Step 4: Implement tier allocation**

Sort by `total_score` descending, then role name. Select no more than five roles per tier:

```python
stable = [role for role in ranked if role.total_score >= 70 and role.matching_level in {"high", "transferable"}][:5]
stretch = [role for role in ranked if role.total_score >= 60 and role.missing_skills][:5]
safe = [role for role in ranked if role.total_score >= 55 and role.entry_difficulty <= 3][:5]
```

Remove any role selected by an earlier tier before evaluating the next tier. If a tier has fewer than three roles, return its explicit `shortage_notice`.

- [ ] **Step 5: Expose recommendation endpoint**

```python
@router.post("/api/career/recommend")
async def recommend_careers(payload: CareerRecommendRequest, request: Request):
    profile = payload.profile or request.app.state.career_profile_repository.get(payload.client_id)
    if profile is None:
        raise CareerProfileNotFoundError
    return success(request.app.state.career_recommender.recommend(profile).model_dump())
```

- [ ] **Step 6: Run recommender and API tests**

Run:

```powershell
resume-backend\.venv\Scripts\python.exe -m pytest resume-backend/tests/test_career_recommender.py resume-backend/tests/test_career_api.py -v
```

Expected: PASS.

- [ ] **Step 7: Commit**

```powershell
git add resume-backend/app/services/career_recommender.py resume-backend/app/schemas/career.py resume-backend/app/api/career.py resume-backend/tests/test_career_recommender.py resume-backend/tests/test_career_api.py
git commit -m "feat: add explainable career recommendations"
```

### Task 5: Add frontend career contracts, API mapper, and persisted store

**Files:**
- Create: `resume-miniprogram/src/types/career.ts`
- Create: `resume-miniprogram/src/services/career-api.ts`
- Create: `resume-miniprogram/src/stores/career.ts`
- Create: `resume-miniprogram/src/tests/career-api.spec.ts`
- Create: `resume-miniprogram/src/tests/career-store.spec.ts`

**Interfaces:**
- Produces:

```ts
export type CareerTier = "stretch" | "stable" | "safe"
export interface CareerProfile { clientId: string; identityCode: IdentityCode; major: string; ... }
export interface CareerRecommendationResponse { profileSummary: CareerProfile; tiers: Record<CareerTier, RoleRecommendation[]>; majorReport: MajorReport }
export const useCareerStore = defineStore("career", ...)
export async function queryRoleFamilies(): Promise<RoleFamilySummary[]>
export async function queryRoleSuggestions(query: string): Promise<RoleSummary[]>
export async function queryMajorSuggestions(query: string): Promise<MajorSummary[]>
export async function saveCareerProfile(profile: CareerProfile): Promise<CareerProfile>
export async function queryCareerRecommendations(profile: CareerProfile): Promise<CareerRecommendationResponse>
```

- [ ] **Step 1: Write failing API mapping test**

```ts
it("maps tiered recommendation scores and major report", async () => {
  const result = await queryCareerRecommendations(profile)

  expect(result.tiers.stable[0].roleName).toBe("数据工程师")
  expect(result.tiers.stable[0].scoreBreakdown[0].weight).toBe(30)
  expect(result.majorReport.matchingLevel).toBe("high")
})
```

- [ ] **Step 2: Write failing store persistence test**

```ts
it("persists a major and selected target role", () => {
  const store = useCareerStore()
  store.updateProfile({ major: "计算机科学与技术" })
  store.selectRecommendation("数据工程师")

  setActivePinia(createPinia())
  const restored = useCareerStore()
  restored.restore()
  expect(restored.profile.major).toBe("计算机科学与技术")
  expect(restored.selectedRoleName).toBe("数据工程师")
})
```

- [ ] **Step 3: Run frontend tests to verify failure**

Run:

```powershell
Set-Location resume-miniprogram
npm.cmd run test:unit -- career-api.spec.ts career-store.spec.ts
```

Expected: FAIL with missing module imports.

- [ ] **Step 4: Implement frontend mappings and store**

Map snake_case backend values to camelCase. Use a dedicated storage key `resume_demo_career_profile`. Keep raw user skills and preferences, and do not copy sensitive resume text into the career store.

- [ ] **Step 5: Run frontend tests to verify pass**

Run:

```powershell
Set-Location resume-miniprogram
npm.cmd run test:unit -- career-api.spec.ts career-store.spec.ts
```

Expected: PASS.

- [ ] **Step 6: Commit**

```powershell
git add resume-miniprogram/src/types/career.ts resume-miniprogram/src/services/career-api.ts resume-miniprogram/src/stores/career.ts resume-miniprogram/src/tests/career-api.spec.ts resume-miniprogram/src/tests/career-store.spec.ts
git commit -m "feat: add career planner frontend data layer"
```

### Task 6: Build the mobile career-volunteer planner page

**Files:**
- Create: `resume-miniprogram/src/pages/career-planner/index.vue`
- Modify: `resume-miniprogram/src/pages.json`
- Modify: `resume-miniprogram/src/pages/job-search/index.vue`
- Test: `resume-miniprogram/src/tests/career-store.spec.ts`

**Interfaces:**
- Consumes: `useConsultationStore`, `useCareerStore`, `queryMajorSuggestions`, `saveCareerProfile`, `queryCareerRecommendations`, existing `queryJob`, `prepareResumeForJob`, `useResumeStore`.
- Produces: `/pages/career-planner/index` route.

- [ ] **Step 1: Add a failing route contract assertion**

```ts
it("stores a planner target role for the resume handoff", () => {
  const store = useCareerStore()
  store.selectRecommendation("数据工程师")

  expect(store.selectedRoleName).toBe("数据工程师")
})
```

- [ ] **Step 2: Run the test to verify failure**

Run:

```powershell
Set-Location resume-miniprogram
npm.cmd run test:unit -- career-store.spec.ts
```

Expected: FAIL because target-role selection is absent.

- [ ] **Step 3: Implement profile step**

Build a compact wizard with:

1. Identity picker initialized from `useConsultationStore`.
2. Major input with suggestion popover and a `跨专业/专业不限` quick option.
3. Education level and graduation year picker.
4. City, industry, work type, salary, and skills tag inputs.
5. Primary “生成志愿方案” action.

Use the current light workbench tokens: `#f4f7fb` page background, white cards, `#2d77d1` primary action, rounded 14-22rpx surfaces, normal text wrapping.

- [ ] **Step 4: Implement results and resume handoff**

Render tabs labelled `冲刺`, `稳妥`, `保底`. Each role card must show:

- total score and five score rows;
- matching level;
- recommendation reasons;
- missing skills;
- 7-day and 30-day actions;
- alternative roles;
- “查看岗位分析” and “按此岗位制作简历” actions.

For resume handoff:

```ts
const job = await queryJob(recommendation.roleName)
resumeStore.setJobIntelligence(job)
prepareResumeForJob(resumeStore.draft, job)
resumeStore.checkpoint()
uni.navigateTo({ url: "/pages/template-picker/index" })
```

- [ ] **Step 5: Add the planner entry**

Add a compact secondary button near the job-search workspace title:

```vue
<button class="secondary compact" @click="uni.navigateTo({ url: '/pages/career-planner/index' })">
  求职志愿规划
</button>
```

Do not alter existing direct job consultation behavior.

- [ ] **Step 6: Run frontend unit tests**

Run:

```powershell
Set-Location resume-miniprogram
npm.cmd run test:unit
```

Expected: PASS.

- [ ] **Step 7: Commit**

```powershell
git add resume-miniprogram/src/pages/career-planner/index.vue resume-miniprogram/src/pages.json resume-miniprogram/src/pages/job-search/index.vue resume-miniprogram/src/tests/career-store.spec.ts
git commit -m "feat: add career volunteer planner page"
```

### Task 7: Make resume drafts major-aware without fabricating facts

**Files:**
- Modify: `resume-miniprogram/src/utils/resume-autofill.ts`
- Modify: `resume-miniprogram/src/pages/resume-form/index.vue`
- Modify: `resume-miniprogram/src/pages/career-planner/index.vue`
- Modify: `resume-miniprogram/src/tests/resume-autofill.spec.ts`

**Interfaces:**
- Changes:

```ts
export function prepareResumeForJob(
  draft: ResumeDraft,
  job: JobIntelligence,
  major?: string,
): void
```

- [ ] **Step 1: Write a failing major-context test**

```ts
it("uses the chosen major as an editable context but keeps unknown facts marked", () => {
  const draft = createEmptyDraft()
  prepareResumeForJob(draft, frontendJob, "计算机科学与技术")

  expect(draft.resume.projects[0].description).toContain("计算机科学与技术")
  expect(draft.resume.projects[0].description).toContain("[待确认]")
})
```

- [ ] **Step 2: Run the test to verify failure**

Run:

```powershell
Set-Location resume-miniprogram
npm.cmd run test:unit -- resume-autofill.spec.ts
```

Expected: FAIL because `prepareResumeForJob` has no major parameter.

- [ ] **Step 3: Add optional major context**

Append one sentence only when `major` is nonempty and not `跨专业/专业不限`:

```ts
const majorContext = major && major !== "跨专业/专业不限"
  ? `可复用课程或专业能力：请补充${major}中与该岗位相关的真实课程、实验或作品 [待确认]。`
  : "请补充与目标岗位相关的真实课程、项目或作品 [待确认]。"
```

Keep existing no-overwrite behavior for employment and projects.

- [ ] **Step 4: Pass the chosen major from the planner handoff**

```ts
const job = await queryJob(recommendation.roleName)
resumeStore.setJobIntelligence(job)
prepareResumeForJob(resumeStore.draft, job, careerStore.profile.major)
resumeStore.checkpoint()
uni.navigateTo({ url: "/pages/template-picker/index" })
```

- [ ] **Step 5: Run targeted and complete frontend tests**

Run:

```powershell
Set-Location resume-miniprogram
npm.cmd run test:unit -- resume-autofill.spec.ts
npm.cmd run test:unit
```

Expected: PASS.

- [ ] **Step 6: Commit**

```powershell
git add resume-miniprogram/src/utils/resume-autofill.ts resume-miniprogram/src/pages/resume-form/index.vue resume-miniprogram/src/pages/career-planner/index.vue resume-miniprogram/src/tests/resume-autofill.spec.ts
git commit -m "feat: add major context to safe resume drafts"
```

### Task 8: Full regression, builds, and local preview

**Files:**
- Modify only if a failed test identifies a concrete regression.

- [ ] **Step 1: Run the complete backend suite**

Run:

```powershell
resume-backend\.venv\Scripts\python.exe -m pytest resume-backend/tests -v
```

Expected: all tests pass; PDF renderer may remain skipped only when Chromium is unavailable.

- [ ] **Step 2: Run the complete frontend suite**

Run:

```powershell
Set-Location resume-miniprogram
npm.cmd run test:unit
```

Expected: all tests pass.

- [ ] **Step 3: Build both targets**

Run:

```powershell
Set-Location resume-miniprogram
npm.cmd run build:h5
npm.cmd run build:mp-weixin
```

Expected: both build commands exit 0.

- [ ] **Step 4: Exercise the local API chain**

Run:

```powershell
Invoke-WebRequest -UseBasicParsing "http://127.0.0.1:8001/api/role/suggestions?q=%E6%95%B0%E6%8D%AE"
Invoke-WebRequest -UseBasicParsing "http://127.0.0.1:8001/api/major/suggestions?q=%E8%AE%A1%E7%AE%97%E6%9C%BA"
```

Expected: nonempty role and major suggestion envelopes.

- [ ] **Step 5: Inspect the final diff**

Run:

```powershell
git diff origin/feature/ai-resume-demo...HEAD --check
git status --short --branch
```

Expected: no whitespace errors and no unintended generated files.

- [ ] **Step 6: Do not push**

Leave all verified commits local until the user explicitly requests a push.
