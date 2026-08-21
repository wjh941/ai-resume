# Minor Improvements Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Improve the local job-reference, PDF print layout, first-login onboarding, and UI polish without changing existing business workflows.

**Architecture:** A static dataset enriches `JobMatcher` output through additive response fields. HTML template CSS keeps PDF changes presentation-only. A frontend `uni` storage utility and reusable tour component manage onboarding without an API, database table, or migration.

**Tech Stack:** FastAPI, Pydantic, pytest, Vue 3 Uni-App, TypeScript, Vitest, Playwright PDF.

## Global Constraints

- Keep all existing routes, request fields, database schema, and business logic compatible.
- New response fields must be additive and safe for older frontend clients to ignore.
- Keep new visible copy in Simplified Chinese, except technical proper nouns.
- Do not enable external SMS, payment, job-source, or push integrations.
- Store onboarding completion only in user-scoped frontend `uni` storage.
- Preserve the export API and renderer selection; change only PDF template CSS and renderer options.
- Preserve the blue-gray operating interface rather than introducing a second design system.

---

### Task 1: Local Mock Job Samples

**Files:**
- Create: `resume-backend/app/services/mock_job_samples.py`
- Modify: `resume-backend/app/schemas/career.py`
- Modify: `resume-backend/app/services/job_matching.py`
- Test: `resume-backend/tests/test_job_match_api.py`
- Create: `resume-miniprogram/src/services/job-match-api.ts`
- Create: `resume-miniprogram/src/types/job-match.ts`
- Modify: `resume-miniprogram/src/pages/career-planner/index.vue`
- Test: `resume-miniprogram/src/tests/job-match-api.spec.ts`

**Interfaces:**
- Produce `MockJobSample(company, city, salary_range, responsibilities, requirements, match_score_reference)`.
- Extend `JobMatchItem` with `responsibilities: list[str]`.
- `JobMatcher` uses a sample by role name but retains its existing calculated candidate match score.
- `listLocalJobMatches()` calls the existing `POST /api/job/match`; the Career Planner renders its results after a successful plan generation.

- [ ] **Step 1: Write the failing API test**

```python
def test_paid_match_returns_local_mock_sample_detail(api_client):
    grant_vip(api_client, "basic")
    response = api_client.post("/api/job/match", json={"target_role": "数据分析师"})
    item = next(item for item in response.json()["data"]["items"] if item["role_name"] == "数据分析师")
    assert item["company"].endswith("（模拟）")
    assert item["salary_range"] == "12k-18k（模拟参考）"
    assert item["responsibilities"]
    assert item["requirements"]
```

Update the old `本地岗位库参考` assertion to require a nonempty company and responsibilities for every result. Create a failing frontend service test that verifies `listLocalJobMatches()` issues `POST /api/job/match` and maps `responsibilities`.

- [ ] **Step 2: Verify the test fails**

Run `python -m pytest tests/test_job_match_api.py -q` from `resume-backend`.

Expected: the response lacks `responsibilities` and has no representative sample company/salary.

- [ ] **Step 3: Implement minimal static samples**

```python
@dataclass(frozen=True)
class MockJobSample:
    company: str
    city: str
    salary_range: str
    responsibilities: tuple[str, ...]
    requirements: tuple[str, ...]
    match_score_reference: int

MOCK_JOB_SAMPLES = {
    "数据分析师": MockJobSample(
        company="澄明数据科技（模拟）", city="上海", salary_range="12k-18k（模拟参考）",
        responsibilities=("维护业务指标体系", "完成专题数据分析"),
        requirements=("SQL", "Python", "数据可视化"), match_score_reference=78,
    ),
}
```

Add four more samples for role names already present in `ROLE_SEEDS`: a software-development role, data-science role, administration role, and finance role. Use sample fields when a sample exists. For uncatalogued roles, retain existing values and derive a concise local responsibility. Never replace the calculated `match_score` with `match_score_reference`.

Add a lightweight TypeScript `JobMatchItem` type and `listLocalJobMatches()` service that calls the existing route. In `career-planner/index.vue`, load this list after `generateCareerRecommendations()` succeeds and display `本地岗位参考` only when items exist. Each existing-style list item shows the local mock company, city, salary range, match score, responsibilities, and requirements. Add no request fields or routes.

- [ ] **Step 4: Verify focused tests pass**

Run `python -m pytest tests/test_job_match_api.py -q` from `resume-backend`, then `npm.cmd run test:unit -- --run src/tests/job-match-api.spec.ts` from `resume-miniprogram`.

- [ ] **Step 5: Commit**

Run `git add resume-backend/app/services/mock_job_samples.py resume-backend/app/services/job_matching.py resume-backend/app/schemas/career.py resume-backend/tests/test_job_match_api.py resume-miniprogram/src/services/job-match-api.ts resume-miniprogram/src/types/job-match.ts resume-miniprogram/src/pages/career-planner/index.vue resume-miniprogram/src/tests/job-match-api.spec.ts`, then `git commit -m "feat(jobs): enrich local mock listings"`.

### Task 2: Print-Safe PDF Layout

**Files:**
- Modify: `resume-backend/app/templates/html/base.html`
- Modify: `resume-backend/app/services/export_pdf.py`
- Test: `resume-backend/tests/test_exports_api.py`

**Interfaces:**
- `render_resume_html()` remains HTML-template based.
- `_render_with_playwright()` retains its signature and passes `prefer_css_page_size=True` to `page.pdf()`.

- [ ] **Step 1: Write failing layout/renderer tests**

```python
def test_resume_html_has_print_safe_wrapping_and_page_rules():
    html = render_resume_html(ResumePayload.model_validate(make_draft_payload()["resume"]), "technology")
    assert "@page { size: A4; margin: 14mm 16mm; }" in html
    assert "overflow-wrap: anywhere" in html
    assert "break-inside: avoid" in html

@pytest.mark.asyncio
async def test_playwright_pdf_prefers_css_page_size(monkeypatch, tmp_path):
    # Install a minimal async Playwright fake that records page.pdf keyword arguments.
    await _render_with_playwright("<html></html>", tmp_path / "resume.pdf", str(tmp_path))
    assert pdf_kwargs["prefer_css_page_size"] is True
```

The fake replaces the imported Playwright module, so no real browser is required. Keep the existing browser integration test optional.

- [ ] **Step 2: Verify the test fails**

Run `python -m pytest tests/test_exports_api.py -q` from `resume-backend`.

Expected: CSS assertions and the captured `prefer_css_page_size` assertion fail.

- [ ] **Step 3: Apply CSS-only presentation changes**

In `base.html`, use:

```css
@page { size: A4; margin: 14mm 16mm; }
body { font-size: 10pt; line-height: 1.58; overflow-wrap: anywhere; word-break: break-word; }
h1 { font-size: 23pt; line-height: 1.2; }
h2 { margin: 15px 0 7px; break-after: avoid; }
section, .entry { break-inside: avoid; }
.entry { margin: 7px 0; }
```

Update the existing `page.pdf()` call with `prefer_css_page_size=True`. Do not change export routes, filenames, watermark logic, or renderer fallback.

- [ ] **Step 4: Verify focused tests pass**

Run `python -m pytest tests/test_exports_api.py -q` from `resume-backend`.

- [ ] **Step 5: Commit**

Run `git add resume-backend/app/templates/html/base.html resume-backend/app/services/export_pdf.py resume-backend/tests/test_exports_api.py`, then `git commit -m "style(export): improve PDF print layout"`.

### Task 3: Local First-Login Onboarding

**Files:**
- Create: `resume-miniprogram/src/utils/onboarding.ts`
- Create: `resume-miniprogram/src/components/OnboardingTour.vue`
- Create: `resume-miniprogram/src/tests/onboarding.spec.ts`
- Modify: `resume-miniprogram/src/pages/job-search/index.vue`
- Modify: `resume-miniprogram/src/pages/account/index.vue`

**Interfaces:**
- `hasCompletedOnboarding(userId: string): boolean`
- `completeOnboarding(userId: string): void`
- `OnboardingTour` accepts `visible: boolean` and emits `complete` and `navigate` with `"resume" | "career" | "applications"`.

- [ ] **Step 1: Write the failing storage test**

```ts
it("records completion only for the current user", () => {
  expect(hasCompletedOnboarding("user-a")).toBe(false)
  completeOnboarding("user-a")
  expect(hasCompletedOnboarding("user-a")).toBe(true)
  expect(hasCompletedOnboarding("user-b")).toBe(false)
  expect(storage.get("resume_demo_onboarding_v1:user-a")).toBe("completed")
})
```

Use the Map-backed `globalThis.uni` storage fixture pattern from `auth-session.spec.ts`.

- [ ] **Step 2: Verify the test fails**

Run `npm.cmd run test:unit -- --run src/tests/onboarding.spec.ts` from `resume-miniprogram`.

Expected: the onboarding utility is missing.

- [ ] **Step 3: Implement storage and the reusable tour**

```ts
const ONBOARDING_KEY_PREFIX = "resume_demo_onboarding_v1:"

export function hasCompletedOnboarding(userId: string): boolean {
  return storage()?.getStorageSync(`${ONBOARDING_KEY_PREFIX}${userId}`) === "completed"
}

export function completeOnboarding(userId: string): void {
  storage()?.setStorageSync(`${ONBOARDING_KEY_PREFIX}${userId}`, "completed")
}
```

Render three Simplified Chinese steps: 完善简历, 生成职业规划, 管理投递. The component exposes previous, next, skip, complete, and current-workflow actions. Skip and complete emit `complete`; a transition honors `prefers-reduced-motion`.

- [ ] **Step 4: Mount automatic and manual entry points**

In `job-search/index.vue`, on mount, open the tour only when `getAuthUser()` returns a user whose key is not completed. On `complete`, save the flag and hide the tour. Map `navigate` to `/pages/resume-editor/index`, `/pages/career-planner/index`, and `/pages/applications/index`.

In `account/index.vue`, add `重新查看新手引导`; it opens the same component without clearing completion state.

- [ ] **Step 5: Verify focused frontend tests and build**

Run `npm.cmd run test:unit -- --run src/tests/onboarding.spec.ts src/tests/auth-session.spec.ts`, then `npm.cmd run build:h5` from `resume-miniprogram`.

- [ ] **Step 6: Commit**

Run `git add resume-miniprogram/src/utils/onboarding.ts resume-miniprogram/src/components/OnboardingTour.vue resume-miniprogram/src/tests/onboarding.spec.ts resume-miniprogram/src/pages/job-search/index.vue resume-miniprogram/src/pages/account/index.vue`, then `git commit -m "feat(h5): add local onboarding tour"`.

### Task 4: UI Rhythm and Motion Refinement

**Files:**
- Modify: `resume-miniprogram/src/App.vue`
- Modify: `resume-miniprogram/src/pages/login/index.vue`
- Modify: `resume-miniprogram/src/pages/account/index.vue`
- Modify: `resume-miniprogram/src/pages/job-search/index.vue`
- Modify: `resume-miniprogram/src/pages/career-planner/index.vue`
- Modify: `resume-miniprogram/src/pages/applications/index.vue`

**Interfaces:** No route, API, store, or form-payload changes.

- [ ] **Step 1: Load incumbent UI context**

Run `node C:\Users\16102\.codex\skills\impeccable\scripts\context.mjs --target resume-miniprogram/src/pages/job-search/index.vue` once. Read the directive and the incumbent `App.vue` rules before editing.

- [ ] **Step 2: Apply minimal shared visual tokens**

Add `--ui-space-2: 12rpx`, `--ui-space-3: 18rpx`, `--ui-space-4: 26rpx`, `--ui-card-radius: 16rpx`, and `--ui-control-radius: 10rpx` to `App.vue`. Add focus-visible, active, disabled, hover, and reduced-motion states for existing buttons only.

- [ ] **Step 3: Refine the named operational pages**

Replace matching hard-coded card radius and spacing values with shared tokens in login, account, job-search, career-planner, and applications. Preserve all existing Chinese copy and control behavior. Add a tab-active transition in login and a single suggestion-list enter/leave transition in job-search. Do not add nested cards, decorative imagery, or new business state.

- [ ] **Step 4: Run the visual detector exactly once after UI edits**

Read `C:\Users\16102\.codex\skills\impeccable\reference\craft-floor.md` immediately before editing. After all UI changes, run:

```powershell
node C:\Users\16102\.codex\skills\impeccable\scripts\detect.mjs --json resume-miniprogram/src/App.vue resume-miniprogram/src/pages/login/index.vue resume-miniprogram/src/pages/account/index.vue resume-miniprogram/src/pages/job-search/index.vue resume-miniprogram/src/pages/career-planner/index.vue resume-miniprogram/src/pages/applications/index.vue resume-miniprogram/src/components/OnboardingTour.vue
```

Resolve detector findings without changing business behavior.

- [ ] **Step 5: Build and commit**

Run `npm.cmd run build:h5` from `resume-miniprogram`. Then run `git add resume-miniprogram/src/App.vue resume-miniprogram/src/pages/login/index.vue resume-miniprogram/src/pages/account/index.vue resume-miniprogram/src/pages/job-search/index.vue resume-miniprogram/src/pages/career-planner/index.vue resume-miniprogram/src/pages/applications/index.vue resume-miniprogram/src/components/OnboardingTour.vue`, followed by `git commit -m "style(h5): refine operational UI motion"`.

### Task 5: Full Regression Verification

**Files:** No expected source changes.

**Interfaces:** Verifies the new local sample, PDF presentation, onboarding storage, and all established business contracts together.

- [ ] **Step 1: Run backend regression**

Run `python -m pytest tests -q` from `resume-backend`.

- [ ] **Step 2: Run frontend regression**

Run `npm.cmd run test:unit` from `resume-miniprogram`.

- [ ] **Step 3: Build and check repository state**

Run `npm.cmd run build:h5` from `resume-miniprogram`, then `git diff --check` and `git status --short` from the repository root.

Expected: all non-optional tests pass, the H5 build exits successfully, and no whitespace errors or uncommitted source changes remain.
