# Graduate Career Assessment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an explainable graduate career assessment with annual official-employment
intelligence, interest/strength/constraint tests and concrete 7/30/90-day plans.

**Architecture:** FastAPI stores local annual insight snapshots and assessment answers,
computes deterministic RIASEC/work-style/evidence signals, then decorates the existing
career recommender with reasons and action plans. Uni-App presents a short multi-step
assessment and a mobile-friendly result page.

**Tech Stack:** FastAPI, SQLite, Pydantic, Uni-App Vue 3, Pinia, pytest and Vitest.

## Global Constraints

- No recruitment-site crawler, HTML scraping, browser automation, login bypass or bulk JD
  collection.
- Annual intelligence may only be local/approved public static summaries and must retain
  source label, publication date and confidence note.
- The assessment is career decision support, not a psychological/medical diagnosis and
  cannot promise employment.
- Existing job query, CSV, draft, Word/PDF export and career-planner contracts remain
  compatible.
- Recommendations cannot treat absent or `[待确认]` information as verified strength.

### Task 1: Annual Insight And Assessment Persistence

**Files:**
- Create: `resume-backend/app/schemas/assessment.py`
- Create: `resume-backend/app/repositories/assessment.py`
- Modify: `resume-backend/app/db.py`
- Test: `resume-backend/tests/test_assessment_repository.py`

**Interfaces:**

```python
def save_assessment(client_id: str, version: int, answers: dict[str, int],
                    result: dict[str, object]) -> dict[str, object]: ...
def list_annual_insights(year: int | None = None) -> list[dict[str, object]]: ...
```

- [ ] Write a failing test that saves an assessment, reloads it for the same client and
  asserts the answers/result survive without affecting `career_profile`.
- [ ] Run `pytest tests/test_assessment_repository.py -v` and confirm the missing
  repository/table failure.
- [ ] Create additive SQLite tables `annual_employment_insight` and `career_assessment`;
  validate year, source label, publication date and confidence note.
- [ ] Implement repository save/load/list methods with JSON serialization.
- [ ] Re-run the focused test and commit `feat: add assessment data storage`.

### Task 2: Deterministic Scoring And Human Action Plans

**Files:**
- Create: `resume-backend/app/services/career_assessment.py`
- Test: `resume-backend/tests/test_career_assessment.py`

**Interfaces:**

```python
def assessment_questions() -> list[dict[str, object]]: ...
def score_assessment(answers: dict[str, int]) -> dict[str, object]: ...
def build_action_plan(result: dict[str, object], profile: CareerProfile) -> dict[str, list[str]]: ...
```

- [ ] Write failing tests proving a high investigative/structured-evidence response produces
  explainable signals, while omitted answers never produce a strength.
- [ ] Run `pytest tests/test_career_assessment.py -v` and confirm the scoring interface is
  missing.
- [ ] Implement four bounded question groups: interest, work style, strength evidence and
  constraints; validate 1-5 answers and return per-dimension reasons.
- [ ] Generate concrete 7-day, 30-day and 90-day actions with visible deliverables,
  including a resume evidence correction, a scoped project/practice task and a review
  checkpoint.
- [ ] Re-run the focused test and commit `feat: add career assessment scoring`.

### Task 3: APIs And Recommendation Integration

**Files:**
- Create: `resume-backend/app/api/assessment.py`
- Modify: `resume-backend/main.py`
- Modify: `resume-backend/app/services/career_recommender.py`
- Test: `resume-backend/tests/test_assessment_api.py`
- Test: `resume-backend/tests/test_career_recommender.py`

- [ ] Write failing API tests for question retrieval, valid submission, validation failure,
  annual-insight provenance and reloading a saved result.
- [ ] Run `pytest tests/test_assessment_api.py -v` and confirm endpoints return 404.
- [ ] Register assessment repository/service/router and expose:
  `GET /api/career/assessment/questions`,
  `POST /api/career/assessment/submit`,
  `GET /api/career/assessment`,
  `GET/POST /api/career/annual-insights`.
- [ ] Add optional assessment reasons and action plans to career recommendations without
  changing existing role tier keys or profile fields.
- [ ] Re-run focused API/recommender tests and commit
  `feat: add assessment APIs and career guidance`.

### Task 4: Mini-Program Assessment And Result Pages

**Files:**
- Create: `resume-miniprogram/src/pages/career-assessment/index.vue`
- Create: `resume-miniprogram/src/services/assessment-api.ts`
- Create: `resume-miniprogram/src/types/assessment.ts`
- Create: `resume-miniprogram/src/stores/assessment.ts`
- Modify: `resume-miniprogram/src/pages.json`
- Modify: `resume-miniprogram/src/pages/career-planner/index.vue`
- Modify: `resume-miniprogram/src/pages/job-search/index.vue`
- Test: `resume-miniprogram/src/tests/assessment-api.spec.ts`

- [ ] Write a failing mapper test for snake_case assessment results and source-labelled
  annual insight cards.
- [ ] Run `npm run test:unit -- assessment-api` and confirm the service is missing.
- [ ] Implement a four-step page with progress indicator, five-point choices, optional
  skips and a clear “不是心理诊断” notice.
- [ ] Implement result sections: supportive summary, fit reasons, non-priority reasons,
  risks, three career tiers and 7/30/90-day actions.
- [ ] Add an entry from job search and a compact annual-insight/assessment card in the
  career planner.
- [ ] Run frontend unit tests plus H5 and MP-Weixin builds; commit
  `feat: add graduate career assessment UI`.

### Task 5: Documentation And Verification

**Files:**
- Modify: `README.md`
- Create: `docs/graduate-career-assessment-operations.md`

- [ ] Document annual insight source requirements, operator import process, interpretation
  boundaries and prohibited scraping behavior.
- [ ] Run `pytest tests -v`, `npm run test:unit`, `npm run build:h5` and
  `npm run build:mp-weixin`.
- [ ] Run `git diff --check`, commit the documentation and push only
  `feature/ai-resume-demo`; do not merge or create a PR.

