# 报告分层与岗位年度就业洞察 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为精美桌面 HTML 仪表盘提供可部署的精简版/专业版报告切换，并新增按岗位查询、带可追溯证据的年度就业洞察。

**Architecture:** 将 `premium-dashboard.html` 放入 UniApp 的 `public` 静态目录，使 Vite 开发与 Docker H5 构建使用同一产物。后端以新增 `report` 包装对象追加在现有 API 输出中，统一由报告投影服务根据请求层级和会员能力过滤；旧字段、端点和默认行为不变。年度洞察增加岗位归属字段和专用查询端点，专业版的证据仅来自用户已验证经历、归档年度资料或明确标注的分析框架。

**Tech Stack:** FastAPI、Pydantic v2、SQLite/Alembic、Vitest、UniApp/Vite、原生 HTML/CSS/JavaScript。

## Global Constraints

- 桌面 HTML 首轮覆盖岗位情报、岗位匹配、职业规划、职业测评、简历建议和年度就业洞察；H5 只保留复用 API 的兼容性，不重复制作 UI。
- 所有既有端点、既有响应字段和未传 `report_mode` 时的行为必须保持兼容。
- 免费用户不得从任何响应中接收专业版 `evidence`、季度行动计划或被隐藏的专业字段。
- 仅使用已验证个人经历、归档年度资料和明确标注的分析框架；不实现招聘爬虫、实时岗位数量、实时薪资或外部招聘数据同步。
- 所有新增用户可见文本使用简体中文；只保留 PDF、Word、JWT、SMS、OAuth、ZIP、APScheduler、PostgreSQL、SQLite 等技术专有名词。
- 保持 H5 `127.0.0.1:5186` 与后端 `127.0.0.1:8000` 的端口契约不变；不干扰已运行的后端进程。
- 每个任务遵循 TDD：先写失败测试，确认失败，最小实现，确认通过，再提交。

---

## File Structure

- `resume-miniprogram/public/premium-dashboard.html`：可被 Vite 直接复制到 H5 生产产物的独立桌面网页。
- `resume-miniprogram/public/dashboard-report-tier.js`：桌面网页使用的报告层级请求、响应标准化和安全渲染辅助函数，可由 Vitest 直接导入测试。
- `resume-miniprogram/src/tests/dashboard-report-tier.spec.ts`：报告层级前端辅助函数与静态页面加载约束测试。
- `resume-miniprogram/vite.config.ts`：删除仅开发环境使用的根目录 HTML 中间件，保留 `/api`、`/downloads`、`/health` 代理。
- `resume-backend/app/schemas/report.py`：新增的报告模式、证据和包装 Pydantic 模型。
- `resume-backend/app/services/report_tiering.py`：唯一负责将完整报告投影为精简版或专业版的纯函数。
- `resume-backend/app/schemas/job.py`、`app/schemas/career.py`、`app/schemas/assessment.py`：为既有请求追加可选 `report_mode`，并定义岗位年度洞察查询请求。
- `resume-backend/app/api/ai.py`、`app/api/career.py`、`app/api/assessment.py`：在既有响应上追加 `report`，新增岗位年度洞察查询端点。
- `resume-backend/app/repositories/assessment.py`、`app/db.py`：保存、迁移和按岗位/年份读取归档年度资料。
- `resume-backend/migrations/versions/20260821_phase12_report_tiering.py`：SQLite 和 PostgreSQL 都可运行的 `role_name` 列迁移。
- `resume-backend/tests/test_report_tiering.py`、`tests/test_annual_insight_api.py`：报告投影、权限隔离、岗位筛选和旧接口兼容测试。
- `README.md`：记录桌面网页生产路径和报告层级使用范围。

---

### Task 1: Ship the desktop HTML dashboard in H5 builds

**Files:**
- Move: `premium-dashboard.html` to `resume-miniprogram/public/premium-dashboard.html`
- Create: `resume-miniprogram/public/dashboard-report-tier.js`
- Modify: `resume-miniprogram/vite.config.ts`
- Modify: `resume-miniprogram/public/premium-dashboard.html`
- Test: `resume-miniprogram/src/tests/dashboard-report-tier.spec.ts`

**Interfaces:**
- Produces `withReportMode(payload, mode)`, `normalizeReport(result)`, `visibleEvidence(report)`, and `escapeText(value)`; in browsers they are also exposed as `window.ResumeDashboardReportTier`.
- `withReportMode(payload, mode)` returns a shallow copy with `report_mode` only for `simplified` and `professional`.
- `normalizeReport(result)` returns `{ mode, summary, actions, evidence, sourceNotice, upgradeNotice }`, accepting missing additive `report` fields from older responses.
- `visibleEvidence(report)` returns `[]` unless `report.mode === "professional"`.

- [ ] **Step 1: Write the failing dashboard delivery test**

Create `resume-miniprogram/src/tests/dashboard-report-tier.spec.ts` with an import from `../../public/dashboard-report-tier.js` and assertions that the static page is present at the production public path:

```ts
import { describe, expect, it } from "vitest"
import { readFileSync } from "node:fs"
import { resolve } from "node:path"
import {
  normalizeReport,
  visibleEvidence,
  withReportMode,
} from "../../public/dashboard-report-tier.js"

it("adds only valid report modes to API payloads", () => {
  expect(withReportMode({ role_name: "数据分析师" }, "professional")).toEqual({
    role_name: "数据分析师",
    report_mode: "professional",
  })
  expect(withReportMode({ role_name: "数据分析师" }, "auto")).toEqual({
    role_name: "数据分析师",
  })
})

it("never exposes professional evidence from a simplified report", () => {
  const report = normalizeReport({
    report: { mode: "simplified", summary: "先补 SQL 项目", actions: ["完成一个项目"], evidence: [{ title: "hidden" }] },
  })
  expect(visibleEvidence(report)).toEqual([])
})

it("ships the standalone dashboard through Vite public assets", () => {
  const html = readFileSync(resolve(process.cwd(), "public/premium-dashboard.html"), "utf8")
  expect(html).toContain('src="./dashboard-report-tier.js"')
})
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `npm.cmd run test:unit -- --run src/tests/dashboard-report-tier.spec.ts`

Expected: FAIL because the public dashboard and report-tier module do not exist.

- [ ] **Step 3: Move the dashboard and create its report-tier helper**

Move the root HTML file to `resume-miniprogram/public/premium-dashboard.html`. Create `resume-miniprogram/public/dashboard-report-tier.js` as an ES module and attach the same functions to `window` for the classic dashboard script:

```js
export function withReportMode(payload, mode) {
  return mode === "simplified" || mode === "professional"
    ? { ...payload, report_mode: mode }
    : { ...payload }
}

export function normalizeReport(result) {
  const report = result?.report || {}
  return {
    mode: report.mode === "professional" ? "professional" : "simplified",
    summary: typeof report.summary === "string" ? report.summary : "",
    actions: Array.isArray(report.actions) ? report.actions : [],
    evidence: Array.isArray(report.evidence) ? report.evidence : [],
    sourceNotice: typeof report.source_notice === "string" ? report.source_notice : "",
    upgradeNotice: typeof report.upgrade_notice === "string" ? report.upgrade_notice : "",
  }
}

export function visibleEvidence(report) {
  return report.mode === "professional" ? report.evidence : []
}

export function escapeText(value) {
  return String(value ?? "").replace(/[&<>"']/g, (character) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[character]))
}

if (typeof window !== "undefined") {
  window.ResumeDashboardReportTier = { withReportMode, normalizeReport, visibleEvidence, escapeText }
}
```

Add `<script type="module" src="./dashboard-report-tier.js"></script>` after the dashboard’s existing classic script, immediately before `</body>`, so the classic script and the module do not race during initial render. Update `vite.config.ts` to remove `readFileSync`, `resolve`, and the `serve-premium-dashboard` middleware; Vite serves `public/premium-dashboard.html` at the identical URL automatically.

- [ ] **Step 4: Run the focused test and production build**

Run: `npm.cmd run test:unit -- --run src/tests/dashboard-report-tier.spec.ts`

Expected: PASS with three passing tests.

Run: `npm.cmd run build:h5`

Expected: PASS and `dist/build/h5/premium-dashboard.html` plus `dist/build/h5/dashboard-report-tier.js` exist.

- [ ] **Step 5: Commit the independently deployable desktop page**

```powershell
git add resume-miniprogram/public/premium-dashboard.html resume-miniprogram/public/dashboard-report-tier.js resume-miniprogram/src/tests/dashboard-report-tier.spec.ts resume-miniprogram/vite.config.ts
git commit -m "feat(web): ship premium dashboard as static asset"
```

### Task 2: Add the shared report-tier contract and projection service

**Files:**
- Create: `resume-backend/app/schemas/report.py`
- Create: `resume-backend/app/services/report_tiering.py`
- Test: `resume-backend/tests/test_report_tiering.py`

**Interfaces:**
- Produces `ReportMode = Literal["simplified", "professional"]`.
- Produces `ReportEvidence(type, title, detail, date, scope)` and `LayeredReport(mode, summary, actions, evidence, source_notice, upgrade_notice)`.
- Produces `ReportEvidenceInput(type, title, detail, date, scope)` and `project_report(requested_mode, default_mode, vip, required_feature, summary, actions, evidence, source_notice, professional_actions)`.
- `project_report` returns `LayeredReport` and is the only function that decides whether evidence is transmitted.

- [ ] **Step 1: Write failing projection tests**

Create tests that use a free `VipStatus` and a basic `VipStatus`:

```python
from app.services.membership import VipStatus
from app.services.report_tiering import ReportEvidenceInput, project_report

def test_free_professional_request_returns_simplified_without_evidence():
    report = project_report(
        requested_mode="professional",
        default_mode="simplified",
        vip=VipStatus("free", None, False),
        required_feature="full_job_report",
        summary="结论",
        actions=["行动一"],
        evidence=[ReportEvidenceInput("personal_evidence", "项目", "证明 SQL 能力", "", "数据分析师")],
        source_notice="资料范围",
        professional_actions=["季度行动"],
    )
    assert report.mode == "simplified"
    assert report.evidence == []
    assert report.actions == ["行动一"]
    assert report.upgrade_notice

def test_basic_user_can_choose_simplified_or_professional():
    vip = VipStatus("basic", None, False)
    assert project_report("simplified", "professional", vip, "full_job_report", "结论", ["行动"], [], "范围", ["专业行动"]).mode == "simplified"
    assert project_report("professional", "simplified", vip, "full_job_report", "结论", ["行动"], [], "范围", ["专业行动"]).mode == "professional"

def test_missing_mode_uses_the_adapter_default_without_changing_legacy_behavior():
    vip = VipStatus("basic", None, False)
    assert project_report(None, "professional", vip, "full_job_report", "结论", ["行动"], [], "范围", ["专业行动"]).mode == "professional"
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest tests/test_report_tiering.py -q`

Expected: FAIL because `app.services.report_tiering` does not exist.

- [ ] **Step 3: Implement validated report models and the pure projection function**

Create `app/schemas/report.py` with Pydantic bounds: summary maximum 1,000 characters, actions maximum 3 in simplified output, evidence maximum 20 items, title maximum 160 characters, detail maximum 1,000 characters, date maximum 32 characters, scope maximum 240 characters. In `app/services/report_tiering.py`, normalize a missing `requested_mode` to the adapter-supplied `default_mode`; do not treat a browser parameter as an entitlement.

Implement the central permission branch:

```python
desired_mode = requested_mode or default_mode
is_professional = (
    desired_mode == "professional"
    and vip is not None
    and vip.allows(required_feature)
)
return LayeredReport(
    mode="professional" if is_professional else "simplified",
    summary=summary,
    actions=professional_actions if is_professional else actions[:3],
    evidence=validated_evidence if is_professional else [],
    source_notice=source_notice,
    upgrade_notice="" if is_professional else "升级会员可查看证据映射、资料来源和行动计划。",
)
```

- [ ] **Step 4: Run focused tests to verify the security boundary**

Run: `python -m pytest tests/test_report_tiering.py -q`

Expected: PASS; assert serialized free reports do not contain each unique professional evidence title.

- [ ] **Step 5: Commit the shared contract**

```powershell
git add resume-backend/app/schemas/report.py resume-backend/app/services/report_tiering.py resume-backend/tests/test_report_tiering.py
git commit -m "feat(reports): add server-side report tier projection"
```

### Task 3: Add role-aware annual insight storage and API

**Files:**
- Modify: `resume-backend/app/schemas/assessment.py`
- Modify: `resume-backend/app/repositories/assessment.py`
- Modify: `resume-backend/app/api/assessment.py`
- Modify: `resume-backend/app/db.py`
- Create: `resume-backend/migrations/versions/20260821_phase12_report_tiering.py`
- Test: `resume-backend/tests/test_annual_insight_api.py`

**Interfaces:**
- `AnnualInsightPayload.role_name: str = ""` keeps old operator writes valid and normalizes to a maximum of 120 characters.
- `AnnualInsightQueryPayload(role_name: str, year: int | None, report_mode: ReportMode | None)` validates role name and year.
- `AssessmentRepository.list_annual_insights_for_role(role_name: str, year: int | None) -> list[dict[str, object]]` returns exact-role rows first, then rows whose `role_name == ""`, ordered by year/date/id descending.
- `POST /api/career/annual-insights/query` returns `{ "role_name": str, "year": int | null, "report": LayeredReport }` and does not alter `POST`/`GET /api/career/annual-insights`.

- [ ] **Step 1: Write failing repository and API tests**

Create `tests/test_annual_insight_api.py` using existing `grant_vip` and authenticated headers. Seed one `role_name="数据分析师"` record and one empty-role general record. Assert:

```python
def test_role_query_prioritizes_role_sources_then_general_sources(api_client):
    # Save a data-analyst source and a general source for 2026.
    response = api_client.post(
        "/api/career/annual-insights/query",
        json={"role_name": "数据分析师", "year": 2026, "report_mode": "professional"},
    )
    data = response.json()["data"]
    assert data["report"]["mode"] == "professional"
    assert [item["title"] for item in data["report"]["evidence"]] == ["数据分析师年度资料", "通用就业资料"]

def test_free_role_query_never_receives_source_evidence(api_client):
    response = api_client.post(
        "/api/career/annual-insights/query",
        json={"role_name": "数据分析师", "year": 2026, "report_mode": "professional"},
    )
    data = response.json()["data"]
    assert data["report"]["mode"] == "simplified"
    assert data["report"]["evidence"] == []
```

Add an old API regression test proving `POST /api/career/annual-insights` accepts a payload without `role_name` and `GET /api/career/annual-insights?year=2026` returns the existing fields.

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest tests/test_annual_insight_api.py -q`

Expected: FAIL with `404` for the new query endpoint and missing `role_name` support.

- [ ] **Step 3: Implement portable storage migration and query behavior**

Add `role_name TEXT NOT NULL DEFAULT ''` to the SQLite creation SQL. Add `_migrate_phase12_report_tiering(connection)` that checks `PRAGMA table_info(annual_employment_insight)` and executes one `ALTER TABLE annual_employment_insight ADD COLUMN role_name TEXT NOT NULL DEFAULT ''` only when absent; invoke it after `_migrate_phase11_password_accounts`.

Create the Alembic revision with `down_revision = "20260821_phase11"` and use SQLAlchemy column operations that work for PostgreSQL:

```python
def upgrade() -> None:
    op.add_column(
        "annual_employment_insight",
        sa.Column("role_name", sa.String(length=120), nullable=False, server_default=""),
    )

def downgrade() -> None:
    with op.batch_alter_table("annual_employment_insight") as batch:
        batch.drop_column("role_name")
```

Update all repository INSERT and SELECT statements to include `role_name`. Build evidence from real repository rows only; every `annual_source` evidence item must use `source_label`, `publication_date`, `scope`, and `confidence_note` from that row. If no rows match, return a professional report with `evidence=[]` and the explicit summary `暂无可核验年度资料，可先参考岗位基础能力并补充已验证经历。`.

- [ ] **Step 4: Run focused repository/API tests and migration check**

Run: `python -m pytest tests/test_annual_insight_api.py tests/test_assessment_repository.py tests/test_assessment_api.py -q`

Expected: PASS with exact-role ordering, general fallback, free-user evidence isolation, and old annual-insight endpoint compatibility.

Run: `alembic heads`

Expected: one head, `20260821_phase12`.

- [ ] **Step 5: Commit role-aware annual insights**

```powershell
git add resume-backend/app/api/assessment.py resume-backend/app/db.py resume-backend/app/repositories/assessment.py resume-backend/app/schemas/assessment.py resume-backend/migrations/versions/20260821_phase12_report_tiering.py resume-backend/tests/test_annual_insight_api.py
git commit -m "feat(insights): add role-aware annual reports"
```

### Task 4: Attach report tiers to existing analysis APIs without breaking fields

**Files:**
- Modify: `resume-backend/app/schemas/job.py`
- Modify: `resume-backend/app/schemas/career.py`
- Modify: `resume-backend/app/api/ai.py`
- Modify: `resume-backend/app/api/career.py`
- Modify: `resume-backend/app/api/assessment.py`
- Modify: `resume-backend/app/services/auth.py`
- Test: `resume-backend/tests/test_report_tiering.py`
- Test: `resume-backend/tests/test_job_match_api.py`
- Test: `resume-backend/tests/test_job_plan_api.py`
- Test: `resume-backend/tests/test_assessment_api.py`

**Interfaces:**
- `JobQueryRequest`, `JobMatchRequest`, `JobPlanRequest`, and `ResumeRewriteRequest` gain `report_mode: ReportMode | None = None`.
- Assessment `GET` accepts `report_mode: ReportMode | None = Query(default=None)`; assessment submission gains an optional `report_mode` field.
- Existing API response root fields remain unchanged and gain an additive `report` key only.
- Every adapter calls `project_report`; no endpoint relies on frontend hiding for authorization.
- `optional_current_user_principal(request, credentials) -> AuthPrincipal | None` returns `None` when no bearer token is supplied and raises the existing `401` response only for an invalid supplied token; `/api/job/query` uses it so anonymous access remains valid.

- [ ] **Step 1: Write failing compatibility and projection tests**

Add explicit assertions for each displayed analysis endpoint:

```python
def test_job_match_free_professional_request_hides_detail_and_evidence(api_client):
    response = api_client.post("/api/job/match", json={"target_role": "数据分析师", "report_mode": "professional"})
    report = response.json()["data"]["report"]
    assert report["mode"] == "simplified"
    assert report["evidence"] == []
    assert response.json()["data"]["items"]  # existing field remains

def test_basic_job_plan_can_choose_simplified_after_unlock(api_client):
    grant_vip(api_client, "basic")
    response = api_client.post("/api/job/plan", json={"role_name": "数据工程师", "expand_detail": True, "report_mode": "simplified"})
    assert response.json()["data"]["report"]["mode"] == "simplified"
    assert response.json()["data"]["report_scope"] == "detailed"  # old field semantics are unchanged
```

Add equivalent assessment and resume-rewrite tests. For each, make a second request without `report_mode` and assert the previous shape and legacy gating behavior remain unchanged.

- [ ] **Step 2: Run focused tests to verify they fail**

Run: `python -m pytest tests/test_report_tiering.py tests/test_job_match_api.py tests/test_job_plan_api.py tests/test_assessment_api.py -q`

Expected: FAIL because current schemas reject `report_mode` or responses lack the additive `report` object.

- [ ] **Step 3: Build endpoint-specific evidence inputs and attach reports**

Use the following sources; never make a fact-like claim without a source notice:

- `/api/job/query`: job intelligence responsibilities/skills become `analysis_framework` evidence; the report summary states they are structured岗位知识, not live hiring data.
- `/api/job/match`: verified evidence titles from `_match_context` become `personal_evidence`; matched and missing skills create at most three concise actions.
- `/api/job/plan`: verified evidence from `_job_plan_context` become `personal_evidence`; existing detailed plan sections become professional actions. Do not change `project_job_plan_for_vip` or its `report_scope` projection.
- `/api/career/assessment`: top interests, strength evidence, and existing assessment notice produce concise actions; 7/30/90-day routes are only placed in professional actions when `full_assessment` is allowed.
- `/api/resume/ai-rewrite`: derive evidence from the submitted resume and job only after `validate_rewrite_facts`; label it `analysis_framework` unless it corresponds to a verified evidence repository record.

Keep `/api/job/query` public. Add this optional-principal dependency in `app/services/auth.py`, reusing the existing bearer parser so a missing token remains anonymous while an invalid supplied token remains a `401`:

```python
def optional_current_user_principal(
    request: Request,
    token: str | None = Depends(optional_bearer_token),
) -> AuthPrincipal | None:
    if token is None:
        return None
    try:
        principal = request.app.state.auth_service.verify_principal(token)
    except AuthenticationError as error:
        raise HTTPException(status_code=401, detail="Authentication is invalid or expired") from error
    request.state.user_id = principal.user_id
    return principal
```

Use it only in `query_job`: `vip = request.app.state.membership_service.current_vip(principal.user_id) if principal else None`, then call `project_report(payload.report_mode, "simplified", vip, "full_job_report", ...)`. Other adapters use their existing authenticated `VipStatus`: job matching and job planning use `full_job_report`; assessment uses `full_assessment`; annual insights use `industry_insight`; resume rewrite uses `full_job_report` while retaining its existing `deep` gate. Their `default_mode` must reproduce current behavior: the endpoint's already-unlocked detailed view maps to `"professional"`, otherwise `"simplified"`.

Wrap each old model dump rather than changing the Pydantic response type:

```python
payload = result.model_dump()
payload["report"] = project_report(...).model_dump(mode="json")
return success(payload)
```

For calls without `report_mode`, pass the endpoint’s current effective level so legacy `full_job_report`, `full_assessment`, `detail_unlocked`, and `deep` rewrite behavior stays unchanged.

- [ ] **Step 4: Run focused tests to verify both tiers and legacy outputs**

Run: `python -m pytest tests/test_report_tiering.py tests/test_job_match_api.py tests/test_job_plan_api.py tests/test_assessment_api.py tests/test_consultation_api.py -q`

Expected: PASS. Inspect every free professional-request response string for a unique evidence title and assert it is absent.

- [ ] **Step 5: Commit additive report support across existing APIs**

```powershell
git add resume-backend/app/api/ai.py resume-backend/app/api/assessment.py resume-backend/app/api/career.py resume-backend/app/schemas/career.py resume-backend/app/schemas/job.py resume-backend/app/services/auth.py resume-backend/tests/test_report_tiering.py resume-backend/tests/test_job_match_api.py resume-backend/tests/test_job_plan_api.py resume-backend/tests/test_assessment_api.py
git commit -m "feat(api): add tiered analysis reports"
```

### Task 5: Render tier switches and role annual insights in the desktop dashboard

**Files:**
- Modify: `resume-miniprogram/public/premium-dashboard.html`
- Modify: `resume-miniprogram/public/dashboard-report-tier.js`
- Modify: `resume-miniprogram/src/tests/dashboard-report-tier.spec.ts`

**Interfaces:**
- `renderReport(report)` returns safe HTML using `escapeText` and calls `visibleEvidence` before constructing evidence cards; browser use exposes it through `window.ResumeDashboardReportTier`.
- `renderReportModeTabs(surface, mode)` returns the shared concise/professional segmented control with `data-report-surface` and `data-report-mode` attributes.
- Dashboard state has `reportMode: "simplified" | "professional"` per report surface and `annualInsight: { roleName, year, report }`.
- `requestAnnualInsight(roleName, year, mode)` sends `POST /api/career/annual-insights/query` through the existing `apiOrMock` and `withReportMode` helper.

- [ ] **Step 1: Write failing browser-helper tests**

Extend `dashboard-report-tier.spec.ts`:

Extend the existing module import to include `renderReport`:

```ts
import { renderReport } from "../../public/dashboard-report-tier.js"
```

```ts
it("keeps professional evidence out of simplified HTML", () => {
  const html = renderReport({
    mode: "simplified",
    summary: "先补项目",
    actions: ["完成 SQL 项目"],
    evidence: [{ type: "annual_source", title: "不应出现", detail: "", date: "2026-01-01", scope: "全国" }],
    sourceNotice: "本地资料",
    upgradeNotice: "升级可查看资料来源",
  })
  expect(html).not.toContain("不应出现")
  expect(html).toContain("升级可查看资料来源")
})

it("renders professional evidence with source date and scope", () => {
  const html = renderReport({
    mode: "professional",
    summary: "结论",
    actions: [],
    evidence: [{ type: "annual_source", title: "年度报告", detail: "岗位需求", date: "2026-01-15", scope: "数据分析师" }],
    sourceNotice: "资料范围",
    upgradeNotice: "",
  })
  expect(html).toContain("年度报告")
  expect(html).toContain("2026-01-15")
  expect(html).toContain("数据分析师")
})
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `npm.cmd run test:unit -- --run src/tests/dashboard-report-tier.spec.ts`

Expected: FAIL because `renderReport` is not exported.

- [ ] **Step 3: Implement the shared report bar and annual-insight panel**

Add reusable report renderers in `dashboard-report-tier.js`; they must independently escape every dynamic value so tests and the classic dashboard do not depend on a script-scope helper:

```js
export function renderReportModeTabs(surface, mode) {
  const conciseActive = mode === "simplified" ? "is-active" : ""
  const professionalActive = mode === "professional" ? "is-active" : ""
  return `<div class="report-tier-bar">
    <div class="report-tier-tabs" role="tablist" aria-label="报告版本">
      <button type="button" class="${conciseActive}" data-report-surface="${escapeText(surface)}" data-report-mode="simplified">精简版</button>
      <button type="button" class="${professionalActive}" data-report-surface="${escapeText(surface)}" data-report-mode="professional">专业版</button>
    </div>
  </div>`
}

export function renderReport(report) {
  const actions = report.actions.map((item) => `<li>${escapeText(item)}</li>`).join("")
  const evidence = visibleEvidence(report).map((item) => `<article class="report-evidence-card">
    <strong>${escapeText(item.title)}</strong><p>${escapeText(item.detail)}</p>
    <small>${escapeText(item.date)} ${escapeText(item.scope)}</small>
  </article>`).join("")
  const notice = report.mode === "professional" ? report.sourceNotice : report.upgradeNotice
  return `<section class="report-result report-${escapeText(report.mode)}">
    <p class="report-summary">${escapeText(report.summary)}</p>
    <ul class="report-actions">${actions}</ul>${evidence}
    <p class="field-help">${escapeText(notice)}</p>
  </section>`
}

if (typeof window !== "undefined") {
  Object.assign(window.ResumeDashboardReportTier, { renderReport, renderReportModeTabs })
}
```

The rendered tabs must have this stable shape:

```html
<div class="report-tier-bar">
  <div class="report-tier-tabs" role="tablist">
    <button data-report-mode="simplified">精简版</button>
    <button data-report-mode="professional">专业版</button>
  </div>
  <p class="field-help">资料范围提示</p>
</div>
```

In the annual-insight page replace the current static-only entry state with: a role input, existing `/api/job/suggestions` result list, year select defaulting to the current year, `renderReportModeTabs("annual-insight", mode)`, query button, result region, and separate messages for missing资料、无会员权限、网络失败。Define `requestAnnualInsight(roleName, year, mode)` in the classic script as `apiOrMock("/api/career/annual-insights/query", { method: "POST", body: JSON.stringify(withReportMode({ role_name: roleName, year }, mode)) })`; normalize `response.data` and set the result region to `renderReport(report)`. Keep the existing static decision framework below the dynamic result as a general reference section.

Update report-producing dashboard actions to pass their surface’s selected `report_mode` through `withReportMode`, call `normalizeReport`, and place the resulting shared report block above detailed legacy content. Professional mode with a simplified response must render the backend `upgradeNotice`, not a frontend guess.

- [ ] **Step 4: Run focused frontend tests and H5 build**

Run: `npm.cmd run test:unit -- --run src/tests/dashboard-report-tier.spec.ts`

Expected: PASS with safe simplified and professional rendering assertions.

Run: `npm.cmd run build:h5`

Expected: PASS; inspect `dist/build/h5/premium-dashboard.html` to confirm the annual-insight input, report controls, and `dashboard-report-tier.js` reference are present.

- [ ] **Step 5: Commit the dashboard experience**

```powershell
git add resume-miniprogram/public/premium-dashboard.html resume-miniprogram/public/dashboard-report-tier.js resume-miniprogram/src/tests/dashboard-report-tier.spec.ts
git commit -m "feat(web): add tiered annual job insights"
```

### Task 6: Document the desktop report experience and run full verification

**Files:**
- Modify: `README.md`
- Test: `resume-backend/tests/`
- Test: `resume-miniprogram/src/tests/`

**Interfaces:**
- Documents `/premium-dashboard.html` as the desktop browser entry point in both dev and production builds.
- Documents that concise reports are for all logged-in users, professional reports require the relevant membership capability, and evidence is limited to recorded personal evidence plus archived annual sources.

- [ ] **Step 1: Write the failing documentation delivery assertion**

Add one assertion to `dashboard-report-tier.spec.ts` that reads `README.md` and requires both `/premium-dashboard.html` and `精简版` / `专业版` to be documented:

```ts
it("documents the deployed desktop report entry and tier boundary", () => {
  const readme = readFileSync(resolve(process.cwd(), "..", "README.md"), "utf8")
  expect(readme).toContain("/premium-dashboard.html")
  expect(readme).toContain("精简版")
  expect(readme).toContain("专业版")
})
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `npm.cmd run test:unit -- --run src/tests/dashboard-report-tier.spec.ts`

Expected: FAIL because the README does not describe the tier boundary.

- [ ] **Step 3: Update deployment and user-facing documentation**

Update README to state that `resume-miniprogram/public/premium-dashboard.html` is copied to `dist/build/h5/premium-dashboard.html`, works behind the existing `/api` proxy, and can use `window.__RESUME_API_BASE_URL__` in a static HTTPS deployment. Describe the report modes and evidence boundary exactly as defined in the approved specification. State that annual insights are archived decision support, not real-time hiring information or an employment guarantee.

- [ ] **Step 4: Run full verification and browser smoke checks**

Run in `resume-backend`: `python -m pytest tests -q`

Expected: PASS with no failures.

Run in `resume-miniprogram`: `npm.cmd run test:unit`

Expected: PASS with no failures.

Run in `resume-miniprogram`: `npm.cmd run build:h5`

Expected: PASS.

With the existing services left running, check:

```powershell
Invoke-WebRequest -UseBasicParsing 'http://127.0.0.1:5186/premium-dashboard.html' | Select-Object -ExpandProperty StatusCode
Invoke-RestMethod 'http://127.0.0.1:8000/health' | ConvertTo-Json -Compress
```

Expected: dashboard status `200`; health response reports `"status":"healthy"`. In the opened dashboard, log in with the development flow, select a role, verify concise output, request professional mode as a free user, then repeat with a Basic/Premium test account and verify source/evidence cards appear only in the professional response.

- [ ] **Step 5: Commit documentation and verification-ready state**

```powershell
git add README.md resume-miniprogram/src/tests/dashboard-report-tier.spec.ts
git commit -m "docs: explain tiered dashboard reports"
```
