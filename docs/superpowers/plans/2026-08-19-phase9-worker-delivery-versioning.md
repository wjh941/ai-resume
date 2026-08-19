# Phase 9 Worker, Delivery, and Versioning Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Phase9 background work, delivery management, resume versions, and career tasks without changing existing contracts.

**Architecture:** Keep the repository SQL contract, add only portable schema revisions, and run APScheduler in a separate process. Existing Vue pages gain compact controls that consume additive endpoints only.

**Tech Stack:** FastAPI, Pydantic, sqlite3/psycopg adapter, Alembic, APScheduler, Vue 3, Pinia, uni-app, Vitest.

## Global Constraints

- Keep H5 at `127.0.0.1:5186` and FastAPI at `127.0.0.1:8000`.
- Keep SQLite as development default and PostgreSQL selected by `DATABASE_URL`.
- Preserve all existing routes, response envelopes, fields, and workflows; add fields and endpoints only.
- Use Simplified Chinese for Phase9 user-facing strings; retain only PDF, Word, JWT, SMS, OAuth, ZIP, APScheduler, PostgreSQL, and SQLite as technical proper nouns.
- Do not stop or alter the user-owned process currently listening on port 8000.
- Do not implement external alert delivery or document parsing.

---

### Task 1: Schema and Worker Settings

**Files:**
- Modify: `resume-backend/app/config.py`
- Modify: `resume-backend/app/db.py`
- Create: `resume-backend/migrations/versions/20260819_phase9_worker_delivery.py`
- Modify: `resume-backend/.env.example`
- Test: `resume-backend/tests/test_phase9_schema.py`

**Interfaces:**
- Produces `Settings.worker_enabled: bool`, `worker_scan_interval_seconds: int`, and `worker_lock_ttl_seconds: int`.
- Produces tables `background_task_lock`, `job_match_alert`, `interview_reminder`, `resume_version`, and `career_task`.
- Produces nullable or defaulted `application_tracker` fields `contact_info`, `attachment_ref`, `timeline_json`, and `next_interview_at`.

- [ ] **Step 1: Write the failing schema tests**

```python
def test_phase9_schema_is_additive(tmp_path):
    database = tmp_path / "phase9.db"
    initialize_database(database)
    with connect(database) as connection:
        columns = {row[1] for row in connection.execute("PRAGMA table_info(application_tracker)")}
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
    assert {"contact_info", "attachment_ref", "timeline_json", "next_interview_at"} <= columns
    assert {"background_task_lock", "job_match_alert", "interview_reminder", "resume_version", "career_task"} <= tables


def test_settings_reads_worker_configuration(monkeypatch):
    monkeypatch.setenv("WORKER_ENABLED", "true")
    monkeypatch.setenv("TASK_SCAN_INTERVAL_SECONDS", "45")
    monkeypatch.setenv("WORKER_LOCK_TTL_SECONDS", "90")
    settings = load_settings()
    assert (settings.worker_enabled, settings.worker_scan_interval_seconds, settings.worker_lock_ttl_seconds) == (True, 45, 90)
```

- [ ] **Step 2: Run the test and confirm failure**

Run: `python -m pytest tests/test_phase9_schema.py -q`

Expected: FAIL because the settings, fields, and tables do not exist.

- [ ] **Step 3: Add the smallest portable schema change**

```python
# db.py after existing migrations
_ensure_column(connection, "application_tracker", "contact_info", "TEXT NOT NULL DEFAULT ''")
_ensure_column(connection, "application_tracker", "attachment_ref", "TEXT NOT NULL DEFAULT ''")
_ensure_column(connection, "application_tracker", "timeline_json", "TEXT NOT NULL DEFAULT '[]'")
_ensure_column(connection, "application_tracker", "next_interview_at", "TEXT")
```

Create an Alembic revision with `down_revision = "20260819_phase8"`, portable
TEXT, BOOLEAN, and TIMESTAMP columns, and matching table indexes. Read worker
values through `load_settings` with defaults `false`, `300`, and `600`.

- [ ] **Step 4: Verify SQLite and PostgreSQL SQL**

Run: `python -m pytest tests/test_phase9_schema.py -q`

Expected: PASS.

Run: `$env:DATABASE_URL='postgresql+psycopg://user:secret@localhost:5432/resume'; alembic upgrade head --sql`

Expected: output creates Phase9 objects without SQLite-only syntax.

- [ ] **Step 5: Commit**

```bash
git add resume-backend/app/config.py resume-backend/app/db.py resume-backend/migrations/versions/20260819_phase9_worker_delivery.py resume-backend/.env.example resume-backend/tests/test_phase9_schema.py
git commit -m "feat: add Phase9 schema foundation"
```

### Task 2: Standalone APScheduler Worker

**Files:**
- Create: `resume-backend/app/services/worker.py`
- Create: `resume-backend/worker.py`
- Modify: `resume-backend/app/repositories/job_collections.py`
- Modify: `resume-backend/app/repositories/membership.py`
- Modify: `resume-backend/requirements.txt`
- Test: `resume-backend/tests/test_phase9_worker.py`

**Interfaces:**
- Produces `TaskLeaseRepository.acquire(task_name: str, owner_id: str, ttl_seconds: int) -> bool`.
- Produces `BackgroundWorker.run_all_once() -> dict[str, int]`.
- Produces `MembershipRepository.expire_all_pending_orders(expire_minutes: int) -> int`.
- Produces `JobCollectionRepository.create_pending_alerts() -> int`.

- [ ] **Step 1: Write the failing worker tests**

```python
def test_task_lease_allows_one_owner(database_path):
    leases = TaskLeaseRepository(database_path)
    assert leases.acquire("order_expiry", "first", 60) is True
    assert leases.acquire("order_expiry", "second", 60) is False


def test_worker_cycle_creates_alert_and_runs_maintenance(database_path, settings):
    initialize_database(database_path)
    JobCollectionRepository(database_path).set_subscription("user-a", True, "data engineer")
    result = BackgroundWorker.from_settings(settings, owner_id="test").run_all_once()
    assert result["job_match_alerts"] == 1
    assert set(result) == {"job_match_alerts", "expired_exports", "expired_orders"}
```

- [ ] **Step 2: Run the test and confirm failure**

Run: `python -m pytest tests/test_phase9_worker.py -q`

Expected: FAIL because worker classes do not exist.

- [ ] **Step 3: Implement the worker outside FastAPI**

```python
class BackgroundWorker:
    def run_all_once(self) -> dict[str, int]:
        return {
            "job_match_alerts": self._run_with_lease("job_match_alerts", self._scan_subscriptions),
            "expired_exports": self._run_with_lease("expired_exports", self.downloads.cleanup_expired),
            "expired_orders": self._run_with_lease("expired_orders", self._expire_orders),
        }
```

`worker.py` must create a `BlockingScheduler`, schedule `run_all_once` at the
configured interval, and exit cleanly when `WORKER_ENABLED` is false. The job
scan creates a pending in-app alert, updates `last_notify_at`, and never calls
a delivery provider. Add APScheduler to requirements.

- [ ] **Step 4: Verify worker behavior**

Run: `python -m pytest tests/test_phase9_worker.py -q`

Expected: PASS.

Run: `$env:WORKER_ENABLED='false'; python worker.py`

Expected: exits without binding port 8000.

- [ ] **Step 5: Commit**

```bash
git add resume-backend/app/services/worker.py resume-backend/worker.py resume-backend/app/repositories/job_collections.py resume-backend/app/repositories/membership.py resume-backend/requirements.txt resume-backend/tests/test_phase9_worker.py
git commit -m "feat: add scheduled maintenance worker"
```

### Task 3: Application Delivery Management APIs

**Files:**
- Modify: `resume-backend/app/schemas/application.py`
- Modify: `resume-backend/app/repositories/applications.py`
- Modify: `resume-backend/app/api/applications.py`
- Test: `resume-backend/tests/test_phase9_applications.py`

**Interfaces:**
- `ApplicationRepository.list(user_id, status=None, interview_date=None)` preserves the status query and adds an interview-date filter.
- `add_timeline_event`, `list_timeline`, and `save_reminder` operate only on the authenticated user's application.

- [ ] **Step 1: Write the failing API test**

```python
def test_timeline_reminder_and_interview_filter(client, auth_headers):
    saved = client.post("/api/applications", headers=auth_headers, json={
        "role_name": "数据工程师", "status": "interview", "contact_info": "张老师",
        "attachment_ref": "材料.zip", "next_interview_at": "2026-08-25T10:00:00+00:00",
    }).json()["data"]
    event = client.post(f"/api/applications/{saved['id']}/timeline", headers=auth_headers, json={"title": "一面", "occurred_at": "2026-08-20T10:00:00+00:00"})
    reminder = client.post(f"/api/applications/{saved['id']}/reminders", headers=auth_headers, json={"reminder_at": "2026-08-25T09:30:00+00:00"})
    listed = client.get("/api/applications?interview_date=2026-08-25", headers=auth_headers)
    assert event.status_code == reminder.status_code == listed.status_code == 200
    assert listed.json()["data"]["items"][0]["contact_info"] == "张老师"
```

- [ ] **Step 2: Run the test and confirm failure**

Run: `python -m pytest tests/test_phase9_applications.py -q`

Expected: FAIL with missing fields and endpoints.

- [ ] **Step 3: Implement additive fields and routes**

```python
@router.post("/{application_id}/timeline")
def add_timeline_event(application_id: str, payload: TimelineEventRequest, request: Request, user_id: str = Depends(current_user_id)):
    return success(request.app.state.application_repository.add_timeline_event(user_id, application_id, payload))

@router.get("/{application_id}/timeline")
def list_timeline(application_id: str, request: Request, user_id: str = Depends(current_user_id)):
    return success({"items": request.app.state.application_repository.list_timeline(user_id, application_id)})
```

Store timeline events as bounded JSON entries. Store reminders in
`interview_reminder` as `pending`; no external delivery is attempted.

- [ ] **Step 4: Verify new and legacy application tests**

Run: `python -m pytest tests/test_phase9_applications.py tests/test_applications_api.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add resume-backend/app/schemas/application.py resume-backend/app/repositories/applications.py resume-backend/app/api/applications.py resume-backend/tests/test_phase9_applications.py
git commit -m "feat: extend application delivery tracking"
```

### Task 4: Resume Version APIs and Import Skeleton

**Files:**
- Modify: `resume-backend/app/repositories/drafts.py`
- Modify: `resume-backend/app/api/drafts.py`
- Modify: `resume-backend/app/schemas/draft.py`
- Test: `resume-backend/tests/test_phase9_resume_versions.py`

**Interfaces:**
- `create_version(user_id, draft_id, note) -> dict`, `list_versions(user_id, draft_id) -> list[dict]`, and `restore_version(user_id, draft_id, version_id) -> dict`.
- `compare_versions(user_id, draft_id, left_id, right_id) -> dict[str, list[str]]` reports changed field names.

- [ ] **Step 1: Write the failing version test**

```python
def test_snapshot_restore_and_compare(client, auth_headers, draft_payload):
    draft = client.post("/api/draft/save", headers=auth_headers, json=draft_payload).json()["data"]
    first = client.post(f"/api/draft/{draft['id']}/versions", headers=auth_headers, json={"note": "投递前"}).json()["data"]
    client.post("/api/draft/save", headers=auth_headers, json={**draft_payload, "id": draft["id"], "job_title": "后端工程师"})
    second = client.post(f"/api/draft/{draft['id']}/versions", headers=auth_headers, json={"note": "调整后"}).json()["data"]
    diff = client.get(f"/api/draft/{draft['id']}/versions/compare?left_id={first['id']}&right_id={second['id']}", headers=auth_headers)
    restored = client.post(f"/api/draft/{draft['id']}/versions/{first['id']}/restore", headers=auth_headers)
    assert "job_title" in diff.json()["data"]["changed_fields"]
    assert restored.json()["data"]["job_title"] == draft["job_title"]
```

- [ ] **Step 2: Run the test and confirm failure**

Run: `python -m pytest tests/test_phase9_resume_versions.py -q`

Expected: FAIL because version routes do not exist.

- [ ] **Step 3: Implement snapshots without changing draft routes**

```python
@router.post("/{draft_id}/versions")
def create_version(draft_id: str, payload: DraftVersionCreateRequest, request: Request, user_id: str = Depends(current_user_id)):
    return success(request.app.state.draft_repository.create_version(user_id, draft_id, payload.note))

@router.post("/{draft_id}/import")
def import_resume_document(draft_id: str):
    raise HTTPException(status_code=501, detail="文档解析将在后续版本提供，请先手动补充简历内容。")
```

Snapshot the existing draft payload as JSON, restore it only to the owned draft,
and mark the restored version active. Diff top-level values and resume section
names; it is a preview rather than a destructive merge.

- [ ] **Step 4: Verify new and legacy draft tests**

Run: `python -m pytest tests/test_phase9_resume_versions.py tests/test_drafts_api.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add resume-backend/app/repositories/drafts.py resume-backend/app/api/drafts.py resume-backend/app/schemas/draft.py resume-backend/tests/test_phase9_resume_versions.py
git commit -m "feat: add resume version snapshots"
```

### Task 5: Career Task APIs

**Files:**
- Create: `resume-backend/app/repositories/career_tasks.py`
- Modify: `resume-backend/app/schemas/career.py`
- Modify: `resume-backend/app/api/career.py`
- Modify: `resume-backend/main.py`
- Test: `resume-backend/tests/test_phase9_career_tasks.py`

**Interfaces:**
- `CareerTaskRepository.generate_from_action_plan(user_id, plan_id, action_plan) -> list[dict]`.
- `list`, `save`, and `delete` enforce user ownership for all task rows.

- [ ] **Step 1: Write the failing career task test**

```python
def test_generate_update_and_list_career_tasks(client, auth_headers, career_profile_payload):
    client.post("/api/career/profile/save", headers=auth_headers, json=career_profile_payload)
    generated = client.post("/api/career/tasks/generate", headers=auth_headers, json={"plan_id": "test-user", "action_plan": {"seven_day": ["整理作品集"], "thirty_day": [], "ninety_day": []}})
    task_id = generated.json()["data"]["items"][0]["id"]
    completed = client.patch(f"/api/career/tasks/{task_id}", headers=auth_headers, json={"status": "completed", "due_date": "2026-08-30"})
    assert completed.json()["data"]["status"] == "completed"
```

- [ ] **Step 2: Run the test and confirm failure**

Run: `python -m pytest tests/test_phase9_career_tasks.py -q`

Expected: FAIL because the repository and routes do not exist.

- [ ] **Step 3: Implement focused schemas, repository, and routes**

```python
class CareerTaskSaveRequest(BaseModel):
    id: str | None = None
    plan_id: str = Field(min_length=1, max_length=120)
    title: str = Field(min_length=1, max_length=240)
    description: str = Field(default="", max_length=4000)
    due_date: date | None = None
    status: Literal["pending", "completed"] = "pending"
    link_to_application_id: str | None = None
    link_to_evidence_id: str | None = None
```

Generate one distinct task for every nonempty 7/30/90-day action, label its
source phase in its description, and avoid duplicate pending titles per plan.
Register `career_task_repository` on `app.state`.

- [ ] **Step 4: Verify new and legacy career tests**

Run: `python -m pytest tests/test_phase9_career_tasks.py tests/test_career_api.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add resume-backend/app/repositories/career_tasks.py resume-backend/app/schemas/career.py resume-backend/app/api/career.py resume-backend/main.py resume-backend/tests/test_phase9_career_tasks.py
git commit -m "feat: add career action tasks"
```

### Task 6: Chinese Frontend Integrations

**Files:**
- Modify: `resume-miniprogram/src/types/application.ts`
- Modify: `resume-miniprogram/src/services/application-api.ts`
- Create: `resume-miniprogram/src/services/resume-version-api.ts`
- Create: `resume-miniprogram/src/services/career-task-api.ts`
- Modify: `resume-miniprogram/src/pages/applications/index.vue`
- Modify: `resume-miniprogram/src/pages/resume-editor/index.vue`
- Modify: `resume-miniprogram/src/pages/career-planner/index.vue`
- Test: `resume-miniprogram/src/tests/phase9-services.spec.ts`

**Interfaces:**
- Maps the additive timeline, reminder, interview-filter, resume-version, and career-task routes.
- All new and touched user-visible page copy is Simplified Chinese.

- [ ] **Step 1: Write the failing service mapping tests**

```ts
it("maps application contact and interview fields", async () => {
  requestMock.mockResolvedValueOnce({ items: [{ id: "a1", contact_info: "联系人", attachment_ref: "材料.zip", timeline_json: [], next_interview_at: null }] })
  const rows = await listApplications("client")
  expect(rows[0].contactInfo).toBe("联系人")
})

it("creates a named resume snapshot", async () => {
  await createResumeVersion("draft-1", "投递前")
  expect(requestMock).toHaveBeenCalledWith("/api/draft/draft-1/versions", "POST", { note: "投递前" })
})
```

- [ ] **Step 2: Run the test and confirm failure**

Run: `npm.cmd run test:unit -- phase9-services.spec.ts`

Expected: FAIL because the mapping functions and fields do not exist.

- [ ] **Step 3: Add compact UI controls and Chinese copy**

```ts
const upcomingInterviews = computed(() => applications.value.filter((item) => item.nextInterviewAt))
const versions = ref<ResumeVersion[]>([])
const careerTasks = ref<CareerTask[]>([])
```

Keep the current application form and append contact/attachment fields, an
interview date filter, an upcoming-interview list, and record timeline events.
Add a compact version section in the resume editor and a task checklist below
career recommendations. Translate English titles, loading states, empty states,
and button labels touched in these pages to Simplified Chinese.

- [ ] **Step 4: Verify frontend behavior**

Run: `npm.cmd run test:unit -- phase9-services.spec.ts`

Expected: PASS.

Run: `npm.cmd run build:h5`

Expected: H5 build completes without type or template errors.

- [ ] **Step 5: Commit**

```bash
git add resume-miniprogram/src/types/application.ts resume-miniprogram/src/services/application-api.ts resume-miniprogram/src/services/resume-version-api.ts resume-miniprogram/src/services/career-task-api.ts resume-miniprogram/src/pages/applications/index.vue resume-miniprogram/src/pages/resume-editor/index.vue resume-miniprogram/src/pages/career-planner/index.vue resume-miniprogram/src/tests/phase9-services.spec.ts
git commit -m "feat: add Phase9 career and delivery UI"
```

### Task 7: Deployment, Documentation, and Verification

**Files:**
- Modify: `docker-compose.yml`
- Modify: `docs/DEPLOYMENT_PRECHECK.md`
- Create: `docs/phase9-changelog.md`
- Test: `resume-backend/tests/test_phase9_operations.py`

**Interfaces:**
- Compose defines a `worker` service with the same PostgreSQL target and controlled export volume as `backend`.
- Documentation defines `WORKER_ENABLED`, scan interval, lock lease, and the single-worker deployment recommendation.

- [ ] **Step 1: Write the failing worker deployment test**

```python
def test_compose_worker_shares_database_and_export_volume():
    compose = Path("../docker-compose.yml").read_text(encoding="utf-8")
    entry = Path("worker.py").read_text(encoding="utf-8")
    assert "worker:" in compose
    assert "DATABASE_URL:" in compose
    assert "export_data:/app/temp" in compose
    assert "BlockingScheduler" in entry
```

- [ ] **Step 2: Run the test and confirm failure**

Run: `python -m pytest tests/test_phase9_operations.py -q`

Expected: FAIL because Compose does not yet declare a worker service.

- [ ] **Step 3: Add deployment configuration and Phase9 records**

```yaml
  worker:
    build: ./resume-backend
    command: ["python", "worker.py"]
    env_file: ./resume-backend/.env
    environment:
      DATABASE_URL: postgresql+psycopg://${POSTGRES_USER:-ai_resume}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB:-ai_resume}
      WORKER_ENABLED: "true"
    volumes:
      - export_data:/app/temp
```

Document manual worker invocation, shared-database lock behavior, and the
remaining delivery/document-parsing work in `docs/phase9-changelog.md` and
the deployment precheck. Do not alter H5 or FastAPI port mappings.

- [ ] **Step 4: Run all required verification**

Run: `python -m pytest tests -q`

Expected: all backend tests pass.

Run: `npm.cmd run test:unit`

Expected: all frontend unit tests pass.

Run: `npm.cmd run build:h5`

Expected: H5 build passes and maintains its proxy target at port 8000.

Run: `python -c "from app.services.worker import BackgroundWorker; print('worker module import ok')"`

Expected: prints confirmation without binding port 8000.

- [ ] **Step 5: Commit and push the complete phase**

```bash
git add docker-compose.yml docs/DEPLOYMENT_PRECHECK.md docs/phase9-changelog.md resume-backend/tests/test_phase9_operations.py
git commit -m "docs: complete Phase9 worker deployment"
git push origin feature/ai-resume-demo
```
