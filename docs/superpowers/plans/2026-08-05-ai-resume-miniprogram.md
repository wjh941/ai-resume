# AI岗位查询与智能简历生成小程序 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> superpowers:subagent-driven-development (recommended) or
> superpowers:executing-plans to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver a local Uni-App and FastAPI demo for job intelligence,
resume draft editing, safe AI rewrite, four templates, and Word/PDF exports.

**Architecture:** FastAPI owns SQLite, AI clients, exports, and file expiry.
Uni-App owns mobile workflow pages and local checkpoints. A local `client_id`
scopes drafts without login. Mock AI is the default provider.

**Tech Stack:** Python 3.11, FastAPI, Pydantic, SQLite, python-docx,
Playwright, optional WeasyPrint, pytest, Uni-App Vue 3, TypeScript, Pinia,
uni-ui, Vitest.

## Global Constraints

- Project root: `D:\Projects\ai-resume-miniprogram`.
- No payment, accounts, crawler, management console, or real login.
- No AI-generated factual resume changes: employers, dates, schools,
  certificates, project identity, and stated metrics remain immutable.
- `AI_PROVIDER=mock` works without an API key.
- PDF uses Playwright by default with browsers stored in D drive; WeasyPrint
  is optional fallback only.
- The backend returns expiring download URLs; mini-program direct download and
  open is primary, H5 URL is fallback.
- Do not create a remote, push, merge, or PR.

---

### Task 1: FastAPI, Schemas, SQLite, Templates, And Draft CRUD

**Files:**
- Create: `resume-backend/requirements.txt`
- Create: `resume-backend/.env.example`
- Create: `resume-backend/main.py`
- Create: `resume-backend/app/config.py`
- Create: `resume-backend/app/db.py`
- Create: `resume-backend/app/schemas/{common,resume,job,draft}.py`
- Create: `resume-backend/app/repositories/{drafts,templates}.py`
- Create: `resume-backend/app/services/template_service.py`
- Create: `resume-backend/app/api/{drafts,templates}.py`
- Create: `resume-backend/tests/{conftest,test_drafts_api,test_templates_api}.py`

**Interfaces:**

```python
class ResumePayload(BaseModel):
    version: Literal[1] = 1
    basic: BasicInfo
    job: JobPreference
    education: list[EducationItem] = []
    employment: list[EmploymentItem] = []
    projects: list[ProjectItem] = []
    skills: SkillCertificateInfo
    self_evaluation: str = ""
    section_visibility: SectionVisibility = SectionVisibility()

class DraftSaveRequest(BaseModel):
    id: str | None = None
    client_id: str
    job_title: str
    template_id: Literal["business", "technology", "graduate", "analytics"]
    resume: ResumePayload
    job_intelligence: JobIntelligence | None = None
```

- [ ] **Step 1: Write failing CRUD tests**

```python
def test_draft_crud_is_scoped_to_client(api_client):
    saved = api_client.post("/api/draft/save", json=make_draft_payload("client-a"))
    draft_id = saved.json()["data"]["id"]

    assert api_client.get(f"/api/draft/{draft_id}", params={"client_id": "client-a"}).status_code == 200
    assert api_client.get(f"/api/draft/{draft_id}", params={"client_id": "client-b"}).status_code == 404

def test_copy_creates_independent_draft(api_client):
    source = api_client.post("/api/draft/save", json=make_draft_payload()).json()["data"]
    copied = api_client.post(f"/api/draft/{source['id']}/copy", json={"client_id": "demo-client"}).json()["data"]
    assert copied["id"] != source["id"]
```

- [ ] **Step 2: Run the red tests**

Run:

```powershell
D:\Python311\python.exe -m pytest resume-backend/tests/test_drafts_api.py -v
```

Expected: FAIL because the server and routes do not exist.

- [ ] **Step 3: Implement configuration and database**

- Load `.env` into immutable `Settings`.
- `initialize_database()` creates `user_draft`, `template_table`, and
  `job_cache`.
- Seed templates `business`, `technology`, `graduate`, and `analytics`.
- Store resume and job snapshots as versioned JSON payloads.

- [ ] **Step 4: Implement scoped draft routes**

```python
POST /api/draft/save
GET /api/draft/list?client_id=
GET /api/draft/{id}?client_id=
POST /api/draft/{id}/copy
DELETE /api/draft/{id}?client_id=
GET /api/template/list
GET /health
```

Success response: `{"code":"ok","data":{},"message":""}`. A draft missing
for that `client_id` returns HTTP 404 with `code="not_found"`.

- [ ] **Step 5: Run the tests**

Run:

```powershell
D:\Python311\python.exe -m pytest resume-backend/tests/test_drafts_api.py resume-backend/tests/test_templates_api.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```powershell
git add resume-backend
git commit -m "feat: add resume draft backend foundation"
```

### Task 2: Mock/Compatible AI, Job Cache, And Rewrite Guard

**Files:**
- Create: `resume-backend/app/services/ai_client.py`
- Create: `resume-backend/app/services/job_cache.py`
- Create: `resume-backend/app/services/rewrite_guard.py`
- Create: `resume-backend/app/api/ai.py`
- Create: `resume-backend/tests/{test_job_query_api,test_resume_rewrite_api}.py`

**Interfaces:**

```python
class AIClient(Protocol):
    async def query_job(self, role_name: str) -> JobIntelligence: ...
    async def rewrite_resume(
        self,
        resume: ResumePayload,
        job: JobIntelligence,
        mode: Literal["light", "deep"],
    ) -> ResumePayload: ...

def validate_rewrite_facts(original: ResumePayload, rewritten: ResumePayload) -> None: ...
```

- [ ] **Step 1: Write failing AI tests**

```python
async def test_same_role_uses_unexpired_cache(api_client, mock_ai_client):
    await api_client.post("/api/job/query", json={"role_name": "数据工程师"})
    await api_client.post("/api/job/query", json={"role_name": "数据工程师"})
    assert mock_ai_client.job_query_count == 1

async def test_rewrite_rejects_changed_employer(api_client, mock_ai_client):
    mock_ai_client.rewrite_result = resume_with_changed_employer()
    result = await api_client.post("/api/resume/ai-rewrite", json=make_rewrite_payload())
    assert result.status_code == 422
    assert result.json()["code"] == "rewrite_fact_violation"
```

- [ ] **Step 2: Run the red tests**

Run:

```powershell
D:\Python311\python.exe -m pytest resume-backend/tests/test_job_query_api.py resume-backend/tests/test_resume_rewrite_api.py -v
```

Expected: FAIL because AI routes do not exist.

- [ ] **Step 3: Implement AI providers**

- `MockAIClient` returns deterministic role intelligence and modifies only
  mutable description fields.
- `ArkAIClient` and `OpenAICompatibleClient` use `httpx.AsyncClient` and
  parse strict JSON through Pydantic.
- `build_ai_client()` chooses `mock`, `ark`, or `openai_compatible`.

- [ ] **Step 4: Implement cache and immutable-field guard**

- Cache by normalized role and provider mode until `CACHE_EXPIRE_DAY`.
- Compare basic identity, school/major/degree, employer/title/date range,
  project name/role/date range, certificate names, and existing metrics.
- Reject response on an immutable field mismatch.

- [ ] **Step 5: Add routes and verify**

```python
POST /api/job/query
POST /api/resume/ai-rewrite
```

Run:

```powershell
D:\Python311\python.exe -m pytest resume-backend/tests/test_job_query_api.py resume-backend/tests/test_resume_rewrite_api.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```powershell
git add resume-backend
git commit -m "feat: add cached ai job and resume rewrite services"
```

### Task 3: Word/PDF Exports And Expiring Downloads

**Files:**
- Create: `resume-backend/app/services/{export_filenames,export_word,export_pdf,downloads}.py`
- Create: `resume-backend/app/templates/html/{base,business,technology,graduate,analytics}.html`
- Create: `resume-backend/app/api/exports.py`
- Create: `resume-backend/tests/test_exports_api.py`

**Interfaces:**

```python
class ExportRequest(BaseModel):
    client_id: str
    draft_id: str

class ExportResult(BaseModel):
    filename: str
    download_url: str
    expires_at: datetime

def build_export_filename(name: str, role: str, extension: Literal["docx", "pdf"]) -> str: ...
```

- [ ] **Step 1: Write failing export tests**

```python
def test_word_export_returns_safe_filename(api_client, saved_draft):
    result = api_client.post("/api/export/word", json={"client_id": "demo-client", "draft_id": saved_draft.id})
    assert result.status_code == 200
    assert result.json()["data"]["filename"] == "张三-数据工程师-简历.docx"

def test_expired_download_returns_not_found(api_client, expired_download):
    assert api_client.get(f"/downloads/{expired_download.token}").status_code == 404
```

- [ ] **Step 2: Run the red tests**

Run:

```powershell
D:\Python311\python.exe -m pytest resume-backend/tests/test_exports_api.py -v
```

Expected: FAIL because export routes do not exist.

- [ ] **Step 3: Implement export and lifecycle**

- Normalize filename parts and replace filesystem-invalid characters.
- Create `download_file` storage with token, path, display filename, and
  expiry timestamp.
- Render Word with `python-docx`; render HTML/CSS PDF through Playwright
  `page.pdf(format="A4", print_background=True)`.
- Allow WeasyPrint only when `PDF_RENDERER=weasyprint`.
- Clean expired output on startup and every 15 minutes.

- [ ] **Step 4: Implement routes and verify**

```python
POST /api/export/word
POST /api/export/pdf
GET /downloads/{token}
```

Run:

```powershell
D:\Python311\python.exe -m pytest resume-backend/tests/test_exports_api.py -v
```

Expected: PASS. PDF test may skip only when Chromium is absent with an
explicit skip reason.

- [ ] **Step 5: Commit**

```powershell
git add resume-backend
git commit -m "feat: add resume word and pdf exports"
```

### Task 4: Uni-App Application Shell, Job Search, And Form

**Files:**
- Create: `resume-miniprogram/{package.json,vite.config.ts,tsconfig.json}`
- Create: `resume-miniprogram/src/{main.ts,App.vue,pages.json,manifest.json}`
- Create: `resume-miniprogram/src/types/{api,resume}.ts`
- Create: `resume-miniprogram/src/services/{http,resume-api}.ts`
- Create: `resume-miniprogram/src/stores/{session,resume}.ts`
- Create: `resume-miniprogram/src/utils/validators.ts`
- Create: `resume-miniprogram/src/pages/{job-search,resume-form}/index.vue`
- Create: `resume-miniprogram/src/components/{FormField,ResumeArraySection}.vue`
- Create: `resume-miniprogram/src/tests/{validators,resume-store}.spec.ts`

**Interfaces:**

```ts
export function getClientId(): string
export function validateResume(resume: ResumePayload): ValidationError[]
export const useResumeStore = defineStore("resume", {
  state: (): ResumeState => ({ activeJob: null, draft: createEmptyDraft() }),
  actions: { restoreCheckpoint(): void, checkpoint(): void },
})
```

- [ ] **Step 1: Write failing frontend tests**

```ts
it("rejects invalid phone", () => {
  expect(validateResume(makeResume({ phone: "123" }))).toContainEqual(
    expect.objectContaining({ field: "basic.phone" }),
  )
})

it("keeps one generated client id", () => {
  expect(getClientId()).toBe(getClientId())
})
```

- [ ] **Step 2: Run red tests**

Run:

```powershell
cd resume-miniprogram
npm run test:unit
```

Expected: FAIL because frontend files are absent.

- [ ] **Step 3: Implement shell and typed services**

- Configure the five requested pages.
- Store one generated UUID with `uni.setStorageSync`.
- Normalize `uni.request` response and error handling.
- Use a local checkpoint on meaningful form changes.

- [ ] **Step 4: Implement job search and multi-item form**

- Query non-empty role names.
- Render role intelligence sections.
- Build typed add/remove controls for education, employment, and projects.
- Save to `/api/draft/save`; retain local checkpoint after transient API
  failure.

- [ ] **Step 5: Verify and commit**

Run:

```powershell
npm run test:unit
```

Expected: PASS.

```powershell
git add resume-miniprogram
git commit -m "feat: add uni-app job search and resume form"
```

### Task 5: Templates, Editor, Drafts, And Mobile Download

**Files:**
- Create: `resume-miniprogram/src/pages/{template-picker,resume-editor,drafts}/index.vue`
- Create: `resume-miniprogram/src/components/{ResumePreview,ResumeSectionCard,TemplateCard,InlineEditPopup,SectionOrderControl}.vue`
- Create: `resume-miniprogram/src/utils/{download,order}.ts`
- Create: `resume-miniprogram/src/tests/resume-order.spec.ts`

**Interfaces:**

```ts
export type TemplateId = "business" | "technology" | "graduate" | "analytics"
export function moveArrayItem<T>(items: T[], index: number, direction: -1 | 1): T[]
export async function downloadAndOpen(url: string, filename: string): Promise<void>
```

- [ ] **Step 1: Write the failing ordering test**

```ts
it("moves a project without mutating original state", () => {
  const original = [{ id: "a" }, { id: "b" }]
  expect(moveArrayItem(original, 1, -1).map((item) => item.id)).toEqual(["b", "a"])
  expect(original.map((item) => item.id)).toEqual(["a", "b"])
})
```

- [ ] **Step 2: Run red test**

Run:

```powershell
npm run test:unit -- resume-order.spec.ts
```

Expected: FAIL because `moveArrayItem` does not exist.

- [ ] **Step 3: Implement template/editor workflow**

- Render four templates from one resume payload.
- Persist selection through draft save.
- Use an inline text popup for editing.
- Use move-up/down controls for ordered records.
- Use section visibility switches without deleting data.
- Run guarded light/deep AI rewrite through backend.

- [ ] **Step 4: Implement draft manager and download**

- List/get/copy/delete by `client_id`.
- Confirm before deletion.
- Use `uni.downloadFile`, then `uni.openDocument`.
- Show H5 URL only as fallback.

- [ ] **Step 5: Verify and commit**

Run:

```powershell
npm run test:unit
```

Expected: PASS.

```powershell
git add resume-miniprogram
git commit -m "feat: add templates editor drafts and downloads"
```

### Task 6: Startup Script, Documentation, And Full Demo Validation

**Files:**
- Create: `scripts/start.bat`
- Create: `README.md`
- Create: `docs/{local-development,wechat-build-and-release,server-deployment}.md`
- Create: `resume-backend/tests/test_smoke_flow.py`
- Create: `.gitignore`

- [ ] **Step 1: Write failing mock-mode smoke test**

```python
def test_mock_mode_flow_queries_saves_rewrites_and_exports(api_client):
    job = api_client.post("/api/job/query", json={"role_name": "数据工程师"}).json()["data"]
    draft = api_client.post("/api/draft/save", json=make_draft_payload(job=job)).json()["data"]
    rewritten = api_client.post("/api/resume/ai-rewrite", json=make_rewrite_payload(draft_id=draft["id"])).json()["data"]
    word = api_client.post("/api/export/word", json={"client_id": "demo-client", "draft_id": draft["id"]}).json()["data"]
    assert rewritten["basic"]["name"] == "张三"
    assert word["filename"].endswith(".docx")
```

- [ ] **Step 2: Run red smoke test**

Run:

```powershell
D:\Python311\python.exe -m pytest resume-backend/tests/test_smoke_flow.py -v
```

Expected: FAIL until all services are wired.

- [ ] **Step 3: Implement `start.bat`**

- Create or reuse `resume-backend\.venv`.
- Install requirements.
- Set `PLAYWRIGHT_BROWSERS_PATH=%~dp0..\.cache\playwright`.
- Install Chromium only when absent.
- Copy `.env.example` only when `.env` is missing.
- Start Uvicorn on `127.0.0.1:8000`.

- [ ] **Step 4: Write delivery documentation**

- Local development and `.env` setup.
- Uni-App build plus WeChat Mini Program compilation steps.
- HTTPS server deployment.
- SQLite-to-MySQL migration path.
- Real job-data provider integration boundary.
- Future payment boundary without implementing it.

- [ ] **Step 5: Run all validation**

Run:

```powershell
D:\Python311\python.exe -m pytest resume-backend/tests -v
cd resume-miniprogram
npm run test:unit
cd ..
D:\Python311\python.exe -m compileall -q resume-backend
git diff --check
```

Expected: PASS without an external AI key.

- [ ] **Step 6: Commit**

```powershell
git add .
git commit -m "docs: add demo startup and deployment guides"
```

