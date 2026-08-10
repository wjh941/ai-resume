# Trustworthy Resume Workbench Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a fact-preserving evidence library, deterministic job-targeted resume suggestions, and resume readiness checks without changing legacy draft or export payloads.

**Architecture:** Store user-authored evidence in a new SQLite table isolated by `client_id`; keep exported resume records unchanged. A backend suggestion service converts evidence into explicitly verified or `[待确认]` draft suggestions, while a readiness service inspects a `ResumePayload` without mutating it. The Uni-App client adds an evidence page, typed API mapping, and a no-overwrite suggestion application utility.

**Tech Stack:** FastAPI, Pydantic v2, SQLite, pytest, Uni-App Vue 3, Pinia, TypeScript, Vitest.

## Global Constraints

- Do not add login, payment, web scraping, automatic job applications, or recruitment-site crawling.
- Never fabricate employers, dates, metrics, or outcomes. Unknown evidence must remain `[待确认]`.
- Preserve existing `ResumePayload` v1, `user_draft.payload_json`, Word/PDF export request formats, and job-query behavior.
- Every data operation is scoped to the existing anonymous `client_id`.
- Existing frontend and backend tests must remain passing; add regression tests before implementation.
- New UI must remain usable at 360px width and use the existing light visual language.

---

### Task 1: Evidence persistence and validation

**Files:**
- Modify: `resume-backend/app/db.py`
- Create: `resume-backend/app/schemas/evidence.py`
- Create: `resume-backend/app/repositories/evidence.py`
- Create: `resume-backend/tests/test_evidence_repository.py`

**Interfaces:**
- Produces `ResumeEvidence`, `ResumeEvidenceSaveRequest`, `EvidenceKind`.
- Produces `EvidenceRepository.list(client_id)`, `save(payload)`, and `delete(evidence_id, client_id)`.
- Evidence storage is independent from `user_draft`.

- [ ] **Step 1: Write failing repository tests**

```python
def test_evidence_round_trip_is_scoped_to_client(database_path):
    repository = EvidenceRepository(database_path)
    saved = repository.save(
        ResumeEvidenceSaveRequest(
            client_id="client-a",
            kind="project",
            title="Data quality coursework",
            context="Database systems course",
            actions="Implemented validation rules",
            outcome="",
            proof_note="Repository screenshot",
            verified=True,
        )
    )

    assert repository.list("client-a") == [saved]
    assert repository.list("client-b") == []
```

- [ ] **Step 2: Run the repository test to verify it fails**

Run:

```powershell
cd resume-backend
.\.venv\Scripts\python.exe -m pytest tests/test_evidence_repository.py -v
```

Expected: FAIL because `EvidenceRepository` and evidence schemas do not exist.

- [ ] **Step 3: Add the Pydantic schema**

```python
EvidenceKind = Literal["coursework", "project", "activity", "internship", "employment"]

class ResumeEvidenceSaveRequest(BaseModel):
    id: str | None = None
    client_id: str = Field(min_length=1)
    kind: EvidenceKind
    title: str = Field(min_length=1, max_length=160)
    context: str = Field(default="", max_length=2_000)
    actions: str = Field(min_length=1, max_length=4_000)
    outcome: str = Field(default="", max_length=2_000)
    proof_note: str = Field(default="", max_length=1_000)
    verified: bool = False
```

Use a response model with `id`, all payload fields, `created_at`, and `updated_at`.

- [ ] **Step 4: Create the SQLite table and repository**

Add `resume_evidence` to `initialize_database`:

```sql
CREATE TABLE IF NOT EXISTS resume_evidence (
    id TEXT PRIMARY KEY,
    client_id TEXT NOT NULL,
    kind TEXT NOT NULL,
    title TEXT NOT NULL,
    context TEXT NOT NULL,
    actions TEXT NOT NULL,
    outcome TEXT NOT NULL,
    proof_note TEXT NOT NULL,
    verified INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_resume_evidence_client_updated
ON resume_evidence (client_id, updated_at DESC, id DESC);
```

`save` must update an existing record only when both `id` and `client_id` match. `delete` must return `False` when the item does not belong to the supplied user.

- [ ] **Step 5: Run repository tests**

Run the command from Step 2.

Expected: PASS, including client isolation and update/delete behavior.

- [ ] **Step 6: Commit**

```powershell
git add resume-backend/app/db.py resume-backend/app/schemas/evidence.py resume-backend/app/repositories/evidence.py resume-backend/tests/test_evidence_repository.py
git commit -m "feat: persist resume evidence library"
```

### Task 2: Suggestion and readiness services

**Files:**
- Create: `resume-backend/app/schemas/resume_quality.py`
- Create: `resume-backend/app/services/evidence_suggestions.py`
- Create: `resume-backend/app/services/resume_readiness.py`
- Create: `resume-backend/tests/test_resume_readiness.py`
- Create: `resume-backend/tests/test_evidence_suggestions.py`

**Interfaces:**
- Consumes `ResumeEvidence` records and a target role string.
- Produces `EvidenceSuggestionResponse` with at most three `EvidenceSuggestion` items.
- Produces `ResumeReadinessReport` with `blocking_items`, `warning_items`, and `ready`.

- [ ] **Step 1: Write failing service tests**

```python
def test_suggestions_keep_unknown_outcome_marked_pending():
    suggestion = build_evidence_suggestions(
        "Data Engineer",
        [make_evidence(kind="project", actions="Built ETL validation", outcome="", verified=True)],
    )[0]
    assert "[待确认]" in suggestion.description
    assert "Built ETL validation" in suggestion.description

def test_readiness_blocks_missing_contact_and_warns_pending_text():
    report = inspect_resume_readiness(make_resume(name="", phone="", pending_project=True))
    assert "姓名" in report.blocking_items
    assert "手机号" in report.blocking_items
    assert report.warning_items
    assert report.ready is False
```

- [ ] **Step 2: Run the service tests to verify they fail**

Run:

```powershell
cd resume-backend
.\.venv\Scripts\python.exe -m pytest tests/test_resume_readiness.py tests/test_evidence_suggestions.py -v
```

Expected: FAIL because the services and report models do not exist.

- [ ] **Step 3: Implement deterministic evidence suggestions**

For each evidence item, derive one target section:

```python
section = "employment" if evidence.kind in {"internship", "employment"} else "project"
```

Use the evidence title, context, and actions verbatim. Include the target role only as a framing phrase. If `verified` is false or `outcome` is blank, append `[待确认：补充真实成果或核验证据]`; do not infer metrics, employers, dates, or outcomes. Sort verified items before unverified ones and return at most three.

- [ ] **Step 4: Implement readiness inspection**

Block export when `basic.name`, `basic.phone`, `basic.email`, or `job.target_role` is blank. Warn when any resume text contains `[待确认]`, when no project/employment item exists, or when an item lacks a description. `ready` is true only when there are no blocking items.

- [ ] **Step 5: Run the service tests**

Run the command from Step 2.

Expected: PASS and no test may rely on a network AI provider.

- [ ] **Step 6: Commit**

```powershell
git add resume-backend/app/schemas/resume_quality.py resume-backend/app/services/evidence_suggestions.py resume-backend/app/services/resume_readiness.py resume-backend/tests/test_resume_readiness.py resume-backend/tests/test_evidence_suggestions.py
git commit -m "feat: add fact-preserving resume quality services"
```

### Task 3: Evidence and readiness API surface

**Files:**
- Create: `resume-backend/app/api/evidence.py`
- Modify: `resume-backend/main.py`
- Create: `resume-backend/tests/test_evidence_api.py`

**Interfaces:**
- `GET /api/evidence?client_id=...`
- `POST /api/evidence`
- `DELETE /api/evidence/{evidence_id}?client_id=...`
- `POST /api/resume/evidence-suggestions`
- `POST /api/resume/readiness`

- [ ] **Step 1: Write failing API tests**

```python
def test_evidence_api_is_client_scoped_and_generates_pending_safe_suggestions(api_client):
    saved = api_client.post("/api/evidence", json=make_evidence_payload()).json()["data"]
    assert api_client.get("/api/evidence", params={"client_id": "other-client"}).json()["data"] == {"items": []}
    suggestions = api_client.post(
        "/api/resume/evidence-suggestions",
        json={"client_id": "demo-client", "role_name": "Data Engineer"},
    )
    assert suggestions.status_code == 200
    assert "[待确认]" in suggestions.json()["data"]["items"][0]["description"]
```

- [ ] **Step 2: Run API tests to verify they fail**

Run:

```powershell
cd resume-backend
.\.venv\Scripts\python.exe -m pytest tests/test_evidence_api.py -v
```

Expected: FAIL with 404 because the routes are not registered.

- [ ] **Step 3: Implement and register routes**

Create one router tagged `evidence`. Read the repository from `request.app.state.evidence_repository`; convert unknown or cross-client delete attempts to the existing 404 envelope. Instantiate the repository in `create_app` and include the router with the existing routers.

- [ ] **Step 4: Run API tests**

Run the command from Step 2.

Expected: PASS for list, create/update/delete, client isolation, suggestions, and readiness.

- [ ] **Step 5: Commit**

```powershell
git add resume-backend/app/api/evidence.py resume-backend/main.py resume-backend/tests/test_evidence_api.py
git commit -m "feat: expose evidence and resume readiness APIs"
```

### Task 4: Typed frontend evidence client and suggestion application

**Files:**
- Create: `resume-miniprogram/src/types/evidence.ts`
- Create: `resume-miniprogram/src/services/evidence-api.ts`
- Create: `resume-miniprogram/src/utils/evidence-suggestions.ts`
- Create: `resume-miniprogram/src/tests/evidence-api.spec.ts`
- Create: `resume-miniprogram/src/tests/evidence-suggestions.spec.ts`

**Interfaces:**
- `listEvidence(clientId)`, `saveEvidence(payload)`, `deleteEvidence(clientId, id)`, `getEvidenceSuggestions(clientId, roleName)`, `checkResumeReadiness(resume)`.
- `applyEvidenceSuggestion(draft, suggestion): boolean`.

- [ ] **Step 1: Write failing frontend tests**

```ts
it("maps snake_case evidence and readiness API responses", async () => {
  ;(globalThis as typeof globalThis & { uni: unknown }).uni = {
    request: vi.fn().mockResolvedValue({
      statusCode: 200,
      data: {
        code: "ok",
        message: "",
        data: {
          items: [{
            id: "evidence-1",
            client_id: "client-a",
            kind: "project",
            title: "Data pipeline",
            context: "",
            actions: "Built validation",
            outcome: "",
            proof_note: "",
            verified: true,
            created_at: "2026-08-10T00:00:00+00:00",
            updated_at: "2026-08-10T00:00:00+00:00",
          }],
        },
      },
    }),
  }

  const evidence = await listEvidence("client-a")
  expect(evidence[0]).toMatchObject({
    id: "evidence-1",
    clientId: "client-a",
    verified: true,
    createdAt: "2026-08-10T00:00:00+00:00",
  })
})

it("adds a suggestion only to an empty target section", () => {
  const draft = createEmptyDraft()
  expect(applyEvidenceSuggestion(draft, projectSuggestion)).toBe(true)
  expect(applyEvidenceSuggestion(draft, projectSuggestion)).toBe(false)
})
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:

```powershell
cd resume-miniprogram
npm run test:unit -- evidence
```

Expected: FAIL because evidence types, service, and application utility do not exist.

- [ ] **Step 3: Implement API mapping and no-overwrite utility**

The utility must:

```ts
if (suggestion.targetSection === "project" && draft.resume.projects.length === 0) {
  draft.resume.projects.push(suggestion.projectDraft)
  return true
}
```

Use the equivalent rule for `employment`; return `false` when the target section already contains a user item. Do not alter basic information, skills, job preference, existing descriptions, or `jobIntelligence`.

- [ ] **Step 4: Run frontend evidence tests**

Run the command from Step 2.

Expected: PASS with API mapping and no-overwrite regression coverage.

- [ ] **Step 5: Commit**

```powershell
git add resume-miniprogram/src/types/evidence.ts resume-miniprogram/src/services/evidence-api.ts resume-miniprogram/src/utils/evidence-suggestions.ts resume-miniprogram/src/tests/evidence-api.spec.ts resume-miniprogram/src/tests/evidence-suggestions.spec.ts
git commit -m "feat: add typed evidence suggestion client"
```

### Task 5: Evidence library mobile page and resume-form integration

**Files:**
- Create: `resume-miniprogram/src/pages/evidence/index.vue`
- Modify: `resume-miniprogram/src/pages.json`
- Modify: `resume-miniprogram/src/pages/resume-form/index.vue`
- Modify: `resume-miniprogram/src/stores/resume.ts`
- Create: `resume-miniprogram/src/tests/evidence-suggestion-flow.spec.ts`

**Interfaces:**
- The evidence page consumes only `getClientId` and the typed evidence API.
- The resume store produces `applyEvidenceSuggestion(suggestion): boolean`, which checkpoints only after a successful no-overwrite write.

- [ ] **Step 1: Write failing suggestion flow test**

```ts
it("checkpoints only after applying a suggestion to an empty section", () => {
  const store = useResumeStore()
  expect(store.applyEvidenceSuggestion(projectSuggestion)).toBe(true)
  expect(store.draft.resume.projects).toEqual([projectSuggestion.projectDraft])

  expect(store.applyEvidenceSuggestion(projectSuggestion)).toBe(false)
  expect(store.draft.resume.projects).toEqual([projectSuggestion.projectDraft])
})
```

- [ ] **Step 2: Run the flow test to verify it fails**

Run:

```powershell
cd resume-miniprogram
npm run test:unit -- evidence-suggestion-flow
```

Expected: FAIL because `useResumeStore` does not expose `applyEvidenceSuggestion`.

- [ ] **Step 3: Implement the evidence page**

Use a scrollable card layout with:

- Type picker for the five supported evidence kinds.
- Inputs for title, context, actions, outcome, proof note, and confirmed-fact switch.
- Save, edit, and delete controls.
- A short permanent notice that AI may only use user-provided facts and that missing outcomes remain `[待确认]`.

Do not write raw proof links into a public export automatically.

- [ ] **Step 4: Integrate evidence entry and suggestions into the resume form**

Add an “经历证据” entry near the AI enrichment section. When an active job exists, request suggestions and render:

- source evidence title;
- target section label;
- safety label for unverified evidence;
- one “写入空白区” action.

The resume store action must call the pure no-overwrite utility and checkpoint after success. The form calls that action. When there is no empty target section, show a non-destructive toast and retain the suggestion.

- [ ] **Step 5: Run frontend tests**

Run:

```powershell
cd resume-miniprogram
npm run test:unit
```

Expected: PASS, including existing resume autofill and store tests.

- [ ] **Step 6: Commit**

```powershell
git add resume-miniprogram/src/pages/evidence/index.vue resume-miniprogram/src/pages.json resume-miniprogram/src/pages/resume-form/index.vue resume-miniprogram/src/stores/resume.ts resume-miniprogram/src/tests/evidence-suggestion-flow.spec.ts
git commit -m "feat: add evidence library resume flow"
```

### Task 6: Readiness check before template selection

**Files:**
- Modify: `resume-miniprogram/src/pages/template-picker/index.vue`
- Create: `resume-miniprogram/src/utils/template-selection.ts`
- Create: `resume-miniprogram/src/tests/resume-readiness-flow.spec.ts`

**Interfaces:**
- `checkResumeReadiness(resume)` returns `{ ready, blockingItems, warningItems }`.
- `decideTemplateSelection(report)` returns `{ blocked: boolean, requiresWarningConfirmation: boolean }`.
- The template picker does not change export APIs and does not mutate the resume.

- [ ] **Step 1: Write failing readiness-flow test**

```ts
it("blocks template navigation when the readiness report has blocking items", () => {
  expect(
    decideTemplateSelection({
      ready: false,
      blockingItems: ["姓名"],
      warningItems: [],
    }),
  ).toEqual({ blocked: true, requiresWarningConfirmation: false })
})
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```powershell
cd resume-miniprogram
npm run test:unit -- readiness-flow
```

Expected: FAIL because `decideTemplateSelection` does not exist.

- [ ] **Step 3: Implement non-mutating readiness interaction**

Implement `decideTemplateSelection` first. Before `uni.navigateTo`, request readiness. If there are blocking items, show the first blocking label and remain on the template picker. If only warnings exist, show a modal containing the first three warnings and require an explicit “继续预览” confirmation. Preserve the selected template only after user continuation.

- [ ] **Step 4: Run the readiness test and full frontend suite**

Run:

```powershell
cd resume-miniprogram
npm run test:unit
```

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add resume-miniprogram/src/pages/template-picker/index.vue resume-miniprogram/src/utils/template-selection.ts resume-miniprogram/src/tests/resume-readiness-flow.spec.ts
git commit -m "feat: check resume readiness before template preview"
```

### Task 7: Full verification and documentation

**Files:**
- Modify: `README.md`
- Modify: `docs/graduate-career-assessment-operations.md` only if its navigation section requires an evidence-page reference.

- [ ] **Step 1: Document evidence workflow**

Add concise documentation explaining:

- evidence is private to the anonymous client ID;
- only user-confirmed facts should be exported;
- `[待确认]` warnings are intentional and must be replaced with real details;
- evidence deletion does not rewrite previously saved resume drafts.

- [ ] **Step 2: Run backend verification**

```powershell
cd resume-backend
.\.venv\Scripts\python.exe -m pytest tests -v
```

Expected: all backend tests pass; document any optional renderer skip.

- [ ] **Step 3: Run frontend verification**

```powershell
cd resume-miniprogram
npm run test:unit
npm run build:h5
npm run build:mp-weixin
```

Expected: all frontend tests and both production builds pass.

- [ ] **Step 4: Commit**

```powershell
git add README.md docs/graduate-career-assessment-operations.md
git commit -m "docs: explain evidence-backed resume workflow"
```
