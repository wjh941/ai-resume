# Application Tracker and Delivery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an anonymous application tracker, local retry queue, functional draft management, cross-platform resume downloads, and local checkpoint cleanup without changing existing resume, CSV, job-query, or export-generation formats.

**Architecture:** Persist server-side application records in a new SQLite table scoped by `client_id`. Keep unsent application create/update payloads in an isolated Uni-App local-storage queue, replaying them through the typed API when the action page opens or the user requests sync. Reuse the existing draft and export APIs; platform-specific download handling stays in a small frontend utility.

**Tech Stack:** FastAPI, Pydantic v2, SQLite, pytest, Uni-App Vue 3, Pinia, TypeScript, Vitest.

## Global Constraints

- Do not add automatic job applications, recruitment-site crawling, recruitment-site login, payment, or account systems.
- Preserve `ResumePayload` v1, `user_draft.payload_json`, existing CSV paths, job-query behavior, and server-side Word/PDF generation logic.
- Every application operation is isolated by the existing anonymous `client_id`.
- Only user clicks create a tracker record; no navigation path may silently create a record.
- Local privacy cleanup deletes only device checkpoint and pending-queue keys, never makes a server bulk-delete request.
- H5 and `mp-weixin` builds must keep compiling with the current Uni-App dependencies.

---

### Task 1: Application persistence, validation, and API

**Files:**
- Modify: `resume-backend/app/db.py`
- Create: `resume-backend/app/schemas/application.py`
- Create: `resume-backend/app/repositories/applications.py`
- Create: `resume-backend/app/api/applications.py`
- Modify: `resume-backend/main.py`
- Create: `resume-backend/tests/test_applications_api.py`

**Interfaces:**
- `ApplicationSaveRequest`, `ApplicationRecord`, and `ApplicationStatus`.
- `ApplicationRepository.list(client_id, status=None)`, `save(payload)`, `delete(application_id, client_id)`.
- `GET /api/applications`, `POST /api/applications`, `DELETE /api/applications/{id}`.

- [ ] **Step 1: Write failing API tests**

```python
def test_application_crud_is_scoped_and_orders_next_actions(api_client):
    first = assert_success(api_client.post("/api/applications", json={
        "client_id": "client-a",
        "role_name": "数据工程师",
        "company": "[待确认]",
        "city": "上海",
        "source": "官网",
        "status": "applied",
        "applied_at": "2026-08-12",
        "next_action_at": "2026-08-15",
        "interview_notes": "",
        "draft_id": None,
        "notes": "",
    }))
    assert_success(api_client.post("/api/applications", json={
        "client_id": "client-a",
        "role_name": "数据分析师",
        "company": "Example",
        "city": "",
        "source": "内推",
        "status": "interview",
        "applied_at": "2026-08-11",
        "next_action_at": "2026-08-13",
        "interview_notes": "记录真实问题",
        "draft_id": None,
        "notes": "",
    }))

    items = assert_success(api_client.get("/api/applications", params={"client_id": "client-a"}))["items"]
    assert [item["role_name"] for item in items] == ["数据分析师", "数据工程师"]
    assert assert_success(api_client.get("/api/applications", params={"client_id": "client-b"})) == {"items": []}
    assert first["company"] == "[待确认]"
```

```python
def test_application_rejects_invalid_status_and_cross_client_update(api_client):
    saved = create_application(api_client, "owner-client")
    rejected = api_client.post("/api/applications", json={**saved, "client_id": "other-client"})
    assert rejected.status_code == 404
    invalid = api_client.post("/api/applications", json={**create_application_payload("owner-client"), "status": "unknown"})
    assert invalid.status_code == 422
```

- [ ] **Step 2: Run API tests to verify they fail**

Run:

```powershell
cd resume-backend
.\.venv\Scripts\python.exe -m pytest tests/test_applications_api.py -v
```

Expected: FAIL because application routes and schemas do not exist.

- [ ] **Step 3: Add the table, schemas, and repository**

Add this table in `initialize_database`:

```sql
CREATE TABLE IF NOT EXISTS application_tracker (
    id TEXT PRIMARY KEY,
    client_id TEXT NOT NULL,
    company TEXT NOT NULL,
    role_name TEXT NOT NULL,
    city TEXT NOT NULL,
    source TEXT NOT NULL,
    status TEXT NOT NULL,
    applied_at TEXT,
    next_action_at TEXT,
    interview_notes TEXT NOT NULL,
    draft_id TEXT,
    notes TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_application_tracker_client_status
ON application_tracker (client_id, status, next_action_at, updated_at DESC);
```

Use:

```python
ApplicationStatus = Literal["saved", "applied", "screening", "interview", "offer", "rejected", "closed"]
```

Normalize trim-only text. Require `client_id` and `role_name`; replace an empty `company` with `[待确认]`; accept dates only as `YYYY-MM-DD` or `None`. Update and delete must use `WHERE id = ? AND client_id = ?`.

- [ ] **Step 4: Register routes and error envelope**

Read the repository from `request.app.state.application_repository`. Add `ApplicationNotFoundError`, convert it in `main.py` to:

```python
JSONResponse(status_code=404, content=error("not_found", "Application not found"))
```

`GET /api/applications` accepts optional `status`. Invalid status remains a normal 422 Pydantic error.

- [ ] **Step 5: Run API tests**

Run the command from Step 2.

Expected: PASS for CRUD, ordering, validation, and anonymous-client isolation.

- [ ] **Step 6: Commit**

```powershell
git add resume-backend/app/db.py resume-backend/app/schemas/application.py resume-backend/app/repositories/applications.py resume-backend/app/api/applications.py resume-backend/main.py resume-backend/tests/test_applications_api.py
git commit -m "feat: add application tracker API"
```

### Task 2: Frontend application API and local retry queue

**Files:**
- Create: `resume-miniprogram/src/types/application.ts`
- Create: `resume-miniprogram/src/services/application-api.ts`
- Create: `resume-miniprogram/src/stores/applications.ts`
- Create: `resume-miniprogram/src/tests/application-api.spec.ts`
- Create: `resume-miniprogram/src/tests/application-store.spec.ts`

**Interfaces:**
- `ApplicationRecord`, `ApplicationInput`, and `ApplicationStatus`.
- `listApplications(clientId, status?)`, `saveApplication(input)`, `deleteApplication(clientId, id)`.
- Store: `queuePending(input)`, `syncPending()`, `pendingCount`, `clearLocalData()`.

- [ ] **Step 1: Write failing API mapping and queue tests**

```ts
it("maps application tracker snake_case data and forwards status filtering", async () => {
  const items = await listApplications("client-a", "interview")
  expect(items[0]).toMatchObject({
    id: "application-1",
    roleName: "数据工程师",
    nextActionAt: "2026-08-15",
  })
  expect(calls[0].url).toContain("status=interview")
})
```

```ts
it("keeps a failed application update in the local retry queue", async () => {
  const store = useApplicationsStore()
  await expect(store.saveOrQueue(applicationInput)).resolves.toEqual({ queued: true })
  expect(store.pendingCount).toBe(1)
  expect(storage.get("resume_demo_application_pending")).toBeTruthy()
})
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
cd resume-miniprogram
npm run test:unit -- application
```

Expected: FAIL because the application client and store do not exist.

- [ ] **Step 3: Implement typed mapping and queue store**

Persist only `ApplicationInput` records to `resume_demo_application_pending`. `saveOrQueue` calls `saveApplication`; on network failure it appends a de-duplicated item keyed by `id` or a generated `local_id` and returns `{ queued: true }`. `syncPending` processes a snapshot in array order, removes each only after a successful server save, and returns `{ synced, remaining }`. Do not queue deletes automatically.

- [ ] **Step 4: Run tests**

Run the command from Step 2.

Expected: PASS for mapping, status filter, queue persistence, and successful queue replay.

- [ ] **Step 5: Commit**

```powershell
git add resume-miniprogram/src/types/application.ts resume-miniprogram/src/services/application-api.ts resume-miniprogram/src/stores/applications.ts resume-miniprogram/src/tests/application-api.spec.ts resume-miniprogram/src/tests/application-store.spec.ts
git commit -m "feat: add local application sync queue"
```

### Task 3: Application tracker page and workflow entry

**Files:**
- Create: `resume-miniprogram/src/pages/applications/index.vue`
- Modify: `resume-miniprogram/src/pages.json`
- Modify: `resume-miniprogram/src/pages/career-planner/index.vue`
- Modify: `resume-miniprogram/src/pages/resume-editor/index.vue`
- Create: `resume-miniprogram/src/tests/application-filter.spec.ts`

**Interfaces:**
- `filterApplications(items, status)` returns all items for `"all"` or exact status matches.
- Tracker reads prefill query fields: `roleName`, `city`, `draftId`.
- Creation is only executed from the tracker’s explicit save button.

- [ ] **Step 1: Write failing status-filter test**

```ts
it("filters only the requested tracker status while retaining all items for all", () => {
  expect(filterApplications(items, "all")).toHaveLength(2)
  expect(filterApplications(items, "interview")).toEqual([items[1]])
})
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
cd resume-miniprogram
npm run test:unit -- application-filter
```

Expected: FAIL because the filter helper does not exist.

- [ ] **Step 3: Add the helper and tracker UI**

Create `src/utils/application-filter.ts`:

```ts
export const filterApplications = (
  items: ApplicationRecord[],
  status: "all" | ApplicationStatus,
): ApplicationRecord[] => status === "all" ? items : items.filter((item) => item.status === status)
```

The tracker page must:

- load server records and call `syncPending()` on `onShow`;
- show a soft warning when `pendingCount > 0`;
- offer status chips for all fixed statuses;
- prefill a new form from navigation query but not save until the user presses “保存投递计划”;
- use a confirmation modal before deletion;
- show `[待确认]` as a visible company placeholder rather than hiding it;
- render `nextActionAt`, `interviewNotes`, and linked `draftId` without navigating to external sites.

- [ ] **Step 4: Wire career and resume entries**

Add a planner action next to the current weekly target:

```ts
uni.navigateTo({ url: `/pages/applications/index?roleName=${encodeURIComponent(roleName)}` })
```

Add an editor action that pre-fills role, city, and current `draft.id`:

```ts
uni.navigateTo({
  url: `/pages/applications/index?roleName=${encodeURIComponent(resume.job.targetRole)}&city=${encodeURIComponent(resume.basic.city)}&draftId=${encodeURIComponent(store.draft.id || "")}`,
})
```

Neither action calls `saveApplication`.

- [ ] **Step 5: Run the focused and full frontend tests**

Run:

```powershell
cd resume-miniprogram
npm run test:unit -- application-filter
npm run test:unit
```

Expected: PASS.

- [ ] **Step 6: Commit**

```powershell
git add resume-miniprogram/src/pages/applications/index.vue resume-miniprogram/src/pages.json resume-miniprogram/src/pages/career-planner/index.vue resume-miniprogram/src/pages/resume-editor/index.vue resume-miniprogram/src/utils/application-filter.ts resume-miniprogram/src/tests/application-filter.spec.ts
git commit -m "feat: add application tracker workspace"
```

### Task 4: Draft management and local privacy controls

**Files:**
- Create: `resume-miniprogram/src/services/drafts-api.ts`
- Modify: `resume-miniprogram/src/pages/drafts/index.vue`
- Create: `resume-miniprogram/src/pages/privacy/index.vue`
- Modify: `resume-miniprogram/src/pages.json`
- Modify: `resume-miniprogram/src/stores/resume.ts`
- Modify: `resume-miniprogram/src/stores/career.ts`
- Modify: `resume-miniprogram/src/stores/consultation.ts`
- Create: `resume-miniprogram/src/utils/local-privacy.ts`
- Create: `resume-miniprogram/src/tests/local-privacy.spec.ts`

**Interfaces:**
- Typed draft list/get/copy/delete functions map existing draft endpoints.
- `clearLocalCareerWorkspace()` removes only known local keys.
- Draft page supports open, copy, delete, and create tracker prefill.

- [ ] **Step 1: Write failing local-privacy test**

```ts
it("removes only workspace checkpoint and pending-queue keys", () => {
  storage.set("resume_demo_checkpoint", { draft: true })
  storage.set("resume_demo_application_pending", [{ roleName: "数据工程师" }])
  storage.set("unrelated_key", "keep")

  clearLocalCareerWorkspace()

  expect(storage.has("resume_demo_checkpoint")).toBe(false)
  expect(storage.has("resume_demo_application_pending")).toBe(false)
  expect(storage.get("unrelated_key")).toBe("keep")
})
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
cd resume-miniprogram
npm run test:unit -- local-privacy
```

Expected: FAIL because the privacy utility does not exist.

- [ ] **Step 3: Implement typed draft page and privacy page**

Map the existing `/api/draft/list`, `/api/draft/{id}`, `/api/draft/{id}/copy`, and `/api/draft/{id}` endpoints. In the draft page, restoring a draft updates `useResumeStore().draft` and checkpoints it. Delete requires `uni.showModal`; after server success remove it from the visible list.

`clearLocalCareerWorkspace()` must call `uni.removeStorageSync` only for:

```ts
[
  "resume_demo_checkpoint",
  "resume_demo_career_planner",
  "resume_demo_consultation",
  "resume_demo_assessment",
  "resume_demo_application_pending",
]
```

The privacy page explains that server drafts, evidence, and applications remain until individually deleted. On confirmed cleanup, call the utility and the public reset actions in resume/career/consultation stores, then show a success toast.

- [ ] **Step 4: Run focused and full frontend tests**

Run:

```powershell
cd resume-miniprogram
npm run test:unit -- local-privacy
npm run test:unit
```

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add resume-miniprogram/src/services/drafts-api.ts resume-miniprogram/src/pages/drafts/index.vue resume-miniprogram/src/pages/privacy/index.vue resume-miniprogram/src/pages.json resume-miniprogram/src/stores/resume.ts resume-miniprogram/src/stores/career.ts resume-miniprogram/src/stores/consultation.ts resume-miniprogram/src/utils/local-privacy.ts resume-miniprogram/src/tests/local-privacy.spec.ts
git commit -m "feat: add draft management and local privacy controls"
```

### Task 5: Cross-platform Word and PDF download controls

**Files:**
- Create: `resume-miniprogram/src/services/export-api.ts`
- Create: `resume-miniprogram/src/utils/download-export.ts`
- Modify: `resume-miniprogram/src/pages/resume-editor/index.vue`
- Create: `resume-miniprogram/src/tests/download-export.spec.ts`

**Interfaces:**
- `requestWordExport(clientId, draftId)`, `requestPdfExport(clientId, draftId)`.
- `downloadExport(downloadUrl, filename, platform)` opens a browser URL on H5 and uses `uni.downloadFile` plus `uni.saveFile` on Mini Program.

- [ ] **Step 1: Write failing download-platform tests**

```ts
it("opens the resolved download URL on H5", async () => {
  await downloadExport("/downloads/token", "resume.docx", "h5")
  expect(openedUrl).toContain("/downloads/token")
})

it("downloads then saves a file on mp-weixin", async () => {
  await downloadExport("/downloads/token", "resume.docx", "mp-weixin")
  expect(downloadCalls).toHaveLength(1)
  expect(saveCalls).toHaveLength(1)
})
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
cd resume-miniprogram
npm run test:unit -- download-export
```

Expected: FAIL because export request and platform helper do not exist.

- [ ] **Step 3: Implement export request and download helper**

Use current `request` and `apiUrl`:

```ts
const result = await request<BackendExportResult>("/api/export/word", "POST", {
  client_id: clientId,
  draft_id: draftId,
})
```

For H5, resolve `apiUrl(result.download_url)` and invoke `window.open(url, "_blank")`; when no browser global exists, use `uni.setClipboardData` and show the URL fallback. For Mini Program, use `uni.downloadFile`, then `uni.saveFile`; if either fails, copy the resolved URL and show a readable fallback.

The editor must require an existing saved `draft.id`; if absent call its existing `save()` first, then request the selected export. No changes to backend filename rules.

- [ ] **Step 4: Run focused and full frontend tests**

Run:

```powershell
cd resume-miniprogram
npm run test:unit -- download-export
npm run test:unit
```

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add resume-miniprogram/src/services/export-api.ts resume-miniprogram/src/utils/download-export.ts resume-miniprogram/src/pages/resume-editor/index.vue resume-miniprogram/src/tests/download-export.spec.ts
git commit -m "feat: add cross-platform resume downloads"
```

### Task 6: Documentation and complete verification

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Document tracker and privacy boundaries**

Add concise instructions for creating and managing a manual tracker record, retrying local pending records, saving Word/PDF on H5 and Mini Program, and local-only privacy cleanup. State explicitly that the product does not auto-apply or scrape recruitment sites.

- [ ] **Step 2: Run full backend verification**

```powershell
cd resume-backend
.\.venv\Scripts\python.exe -m pytest tests -v
```

Expected: all tests pass; document the optional Chromium PDF skip if it occurs.

- [ ] **Step 3: Run full frontend and production builds**

```powershell
cd resume-miniprogram
npm run test:unit
npm run build:h5
npm run build:mp-weixin
```

Expected: all frontend tests and production builds pass.

- [ ] **Step 4: Commit**

```powershell
git add README.md
git commit -m "docs: explain application tracker workflow"
```
