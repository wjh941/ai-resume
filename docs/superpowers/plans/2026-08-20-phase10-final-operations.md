# Phase 10 Final Operations Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add secure operator access, mock push delivery, resume-import preview, observability, and final operations documentation without breaking current contracts.

**Architecture:** Add additive Phase 10 tables through the existing SQLite/PostgreSQL compatibility layer and a portable Alembic revision. Provider dispatch and document parsing remain focused services. H5 stores the signed role only for display; FastAPI dependencies authorize every operator request.

**Tech Stack:** FastAPI, Pydantic, SQLite/PostgreSQL, Alembic, PyJWT, APScheduler, Vue 3, Uni-App, Pinia, Vitest, pytest.

## Global Constraints

- Preserve existing APIs, tables, H5 `127.0.0.1:5186`, and FastAPI `127.0.0.1:8000`.
- Add only columns, tables, routes, and response fields; do not alter existing request fields or terminate the running `8000` process.
- Synchronize persisted operator roles from `OPERATOR_PHONE_ALLOWLIST` during phone login; backend JWT dependencies are the only authorization source.
- Use Simplified Chinese for all added or changed H5 visible text, retaining only PDF, Word, JWT, SMS, OAuth, ZIP, APScheduler, PostgreSQL, and SQLite.
- Do not call real providers or parse PDF/Word content. Keep explicit English deferred-integration comments at those boundaries.
- Use `apply_patch`, run focused tests before and after each change, and make atomic commits.

---

### Task 1: Schema, Settings, and Operator RBAC

**Files:**
- Modify: `resume-backend/app/config.py`, `resume-backend/app/db.py`, `resume-backend/app/repositories/users.py`, `resume-backend/app/services/auth.py`, `resume-backend/app/schemas/auth.py`, `resume-backend/app/api/auth.py`
- Create: `resume-backend/migrations/versions/20260820_phase10_operations.py`
- Test: `resume-backend/tests/test_phase10_rbac.py`

**Interfaces:** `Settings.operator_phone_allowlist`, `Settings.push_dispatcher_mode`, `Settings.log_level`, `Settings.resume_import_max_file_bytes`; `AuthPrincipal(user_id, role)`, `current_user_principal()`, and `require_operator()`. Existing `current_user_id()` keeps returning `str`.

- [ ] **Step 1: Write the failing role test.**

```python
def test_allowlisted_login_issues_operator_token(api_client, monkeypatch):
    monkeypatch.setenv("OPERATOR_PHONE_ALLOWLIST", "13800138000")
    payload = login_phone(api_client, "13800138000")
    assert payload["user"]["role"] == "operator"
    assert decode_token(payload["token"])["role"] == "operator"

def test_operator_route_rejects_regular_user(api_client):
    assert api_client.get("/api/operator/knowledge-items").status_code == 403
```

- [ ] **Step 2: Run `python -m pytest tests/test_phase10_rbac.py -q`.** Expect failure because the role column, signed claim, and operator dependency do not exist.
- [ ] **Step 3: Implement additive role persistence.** Add `users.role TEXT NOT NULL DEFAULT 'user'`, normalize the allowlist at login, synchronize the persisted role, sign it in JWT, and reject tokens whose role no longer matches storage.

```python
@dataclass(frozen=True)
class AuthPrincipal:
    user_id: str
    role: str

def require_operator(principal: AuthPrincipal = Depends(current_user_principal)) -> AuthPrincipal:
    if principal.role != "operator":
        raise HTTPException(status_code=403, detail="Operator permission is required")
    return principal
```

- [ ] **Step 4: Add portable migration.** Use revision `20260820_phase10`, down revision `20260819_phase9`, and `op.add_column("users", sa.Column("role", sa.String(length=24), nullable=False, server_default="user"))`.
- [ ] **Step 5: Run `python -m pytest tests/test_phase10_rbac.py tests/test_phase8_database.py tests/test_phase9_schema.py -q`.** Expect pass for JWT role, regular-user 403, and migration head.
- [ ] **Step 6: Commit `feat: add Phase10 operator RBAC foundation`.**

### Task 2: Push Dispatcher and Worker Events

**Files:**
- Create: `resume-backend/app/repositories/push_logs.py`, `resume-backend/app/services/push.py`
- Modify: `resume-backend/app/services/worker.py`, `resume-backend/app/repositories/job_collections.py`, `resume-backend/app/repositories/applications.py`, `resume-backend/app/repositories/membership.py`, `resume-backend/main.py`
- Test: `resume-backend/tests/test_phase10_push.py`

**Interfaces:** `PushDispatcher.dispatch(event_type, user_id, source_ref, payload) -> list[PushSendLog]`; `PushLogRepository.exists_for_source(event_type, target_type, source_ref) -> bool`; worker adds `push_job_alerts`, `push_interview_reminders`, and `push_order_changes` without removing Phase 9 keys.

- [ ] **Step 1: Write the failing mock-dispatch test.**

```python
def test_mock_dispatch_logs_both_targets(database_path, settings):
    logs = PushDispatcher(settings, PushLogRepository(database_path)).dispatch(
        "job_subscription_alert", "user-1", "alert-1", {"alert_id": "alert-1"}
    )
    assert {item.target_type for item in logs} == {"sms", "wechat_subscription"}
    assert {item.status for item in logs} == {"sent"}

def test_worker_does_not_send_the_same_source_twice(worker):
    assert worker.run_all_once()["push_job_alerts"] == 2
    assert worker.run_all_once()["push_job_alerts"] == 0
```

- [ ] **Step 2: Run `python -m pytest tests/test_phase10_push.py -q`.** Expect failure because push logs and dispatching do not exist.
- [ ] **Step 3: Implement `push_send_log` and both modes.** Persist source reference, target, mode, status, payload summary, error text, and timestamp. `mock` records `sent`; `real` records `skipped` and never sends network traffic.

```python
def _dispatch_target(self, event_type, user_id, source_ref, target, payload):
    if self._logs.exists_for_source(event_type, target, source_ref):
        return None
    # Provider invocation is intentionally deferred until production integration is approved.
    return self._logs.create(event_type, user_id, source_ref, target, self._mode, "sent" if self._mode == "mock" else "skipped", payload)
```

- [ ] **Step 4: Add worker source scans.** Scan new subscription alerts, due interview reminders, and newly expired orders; use source-log lookup for idempotence and mark reminders delivered only after mock dispatch.
- [ ] **Step 5: Run `python -m pytest tests/test_phase10_push.py tests/test_phase9_worker.py -q`.** Expect two logs per new source and no duplicate logs.
- [ ] **Step 6: Commit `feat: add Phase10 push dispatch framework`.**

### Task 3: Secure Resume Import Preview

**Files:**
- Create: `resume-backend/app/repositories/resume_imports.py`, `resume-backend/app/services/resume_imports.py`
- Modify: `resume-backend/app/schemas/draft.py`, `resume-backend/app/api/drafts.py`, `resume-backend/main.py`
- Test: `resume-backend/tests/test_phase10_resume_imports.py`

**Interfaces:** `ResumeImportService.accept_upload(user_id, draft_id, upload) -> ResumeImportRecord`; `POST /api/draft/{draft_id}/imports` returns `{id, status, original_filename, parsed_resume}`; the preview matches the current frontend resume structure.

- [ ] **Step 1: Write failing safe-upload tests.**

```python
def test_pdf_upload_returns_mock_preview(api_client, saved_draft):
    response = api_client.post(f"/api/draft/{saved_draft}/imports", files={"file": ("resume.pdf", b"%PDF-1.4", "application/pdf")})
    assert response.status_code == 200
    assert response.json()["data"]["parsed_resume"]["basic"]["name"] == ""

def test_upload_rejects_unsafe_type(api_client, saved_draft):
    response = api_client.post(f"/api/draft/{saved_draft}/imports", files={"file": ("resume.exe", b"x", "application/octet-stream")})
    assert response.status_code == 422
```

- [ ] **Step 2: Run `python -m pytest tests/test_phase10_resume_imports.py -q`.** Expect failure because the upload route does not exist.
- [ ] **Step 3: Implement streaming intake.** Require an owned draft, permit PDF/DOC/DOCX only, validate expected content types, write a generated filename under `TEMP_FILE_PATH/resume-imports`, enforce `RESUME_IMPORT_MAX_FILE_BYTES`, and store no exposed filesystem path.

```python
async def accept_upload(self, user_id, draft_id, upload):
    destination = self._safe_destination(import_id, suffix)
    size = await self._stream_with_limit(upload, destination)
    # Malware-scanner invocation is intentionally deferred until production integration is configured.
    return self._repository.create(user_id, draft_id, generated_name, upload.filename or "", size, empty_resume_preview())
```

- [ ] **Step 4: Run `python -m pytest tests/test_phase10_resume_imports.py tests/test_drafts_api.py -q`.** Expect pass for valid preview, invalid types, byte limits, and ownership.
- [ ] **Step 5: Commit `feat: add Phase10 resume import preview`.**

### Task 4: Operator Knowledge-Base Version API

**Files:**
- Create: `resume-backend/app/repositories/operator_knowledge.py`, `resume-backend/app/api/operator.py`
- Modify: `resume-backend/app/schemas/knowledgebase.py`, `resume-backend/main.py`
- Test: `resume-backend/tests/test_phase10_operator_knowledge.py`

**Interfaces:** `OperatorKnowledgeRepository.create`, `update`, `list_items`, `list_versions`, `restore_version`; all `/api/operator/knowledge-items` routes depend on `require_operator`; statuses are `active`, `offline`, and `invalid`.

- [ ] **Step 1: Write the failing version workflow test.**

```python
def test_operator_restore_creates_new_current_version(api_client, operator_headers):
    item = api_client.post("/api/operator/knowledge-items", headers=operator_headers, json={"title": "面试准备", "content": "初版", "status": "active"}).json()["data"]
    api_client.patch(f"/api/operator/knowledge-items/{item['id']}", headers=operator_headers, json={"content": "修订版", "status": "invalid"})
    restored = api_client.post(f"/api/operator/knowledge-items/{item['id']}/versions/1/restore", headers=operator_headers)
    assert restored.json()["data"]["version"] == 3
    assert restored.json()["data"]["status"] == "active"
```

- [ ] **Step 2: Run `python -m pytest tests/test_phase10_operator_knowledge.py -q`.** Expect failure because the API group and version history do not exist.
- [ ] **Step 3: Implement `knowledge_item` and immutable `knowledge_item_version`.** Every create, edit, status change, and restore creates a version; restoring history creates a new current version instead of mutating or deleting history.
- [ ] **Step 4: Run `python -m pytest tests/test_phase10_operator_knowledge.py tests/test_phase10_rbac.py tests/test_knowledge_sync_api.py -q`.** Expect pass for operator workflow, 403 denial, and public knowledge API compatibility.
- [ ] **Step 5: Commit `feat: add Phase10 operator knowledge APIs`.**

### Task 5: Structured Logging and Health Metrics

**Files:**
- Create: `resume-backend/app/services/observability.py`
- Modify: `resume-backend/main.py`, `resume-backend/app/api/system.py`, `resume-backend/app/services/worker.py`
- Test: `resume-backend/tests/test_phase10_observability.py`

**Interfaces:** `log_event(request, level, event, **context)`; `POST /api/system/client-errors`; health gains `push_dispatcher_mode` and `worker: {status, last_completed_at}` while retaining existing keys.

- [ ] **Step 1: Write failing observability tests.**

```python
def test_health_reports_push_and_worker(api_client):
    data = api_client.get("/health").json()["data"]
    assert data["push_dispatcher_mode"] == "mock"
    assert data["worker"]["status"] in {"disabled", "unknown", "healthy", "stale"}

def test_unhandled_error_is_sanitized_and_logged(api_client, api_app, caplog):
    @api_app.get("/test-error")
    def raise_for_test():
        raise RuntimeError("internal detail")
    response = api_client.get("/test-error")
    assert response.status_code == 500
    assert "traceback" not in response.text.lower()
    assert any("request_id" in record.message for record in caplog.records)
```

- [ ] **Step 2: Run `python -m pytest tests/test_phase10_observability.py -q`.** Expect failure because global structured logging and metrics do not exist.
- [ ] **Step 3: Implement `LOG_LEVEL`, JSON event logging, and persisted worker runs.** Attach request ID in middleware, attach user ID in principal resolution, log safe exception context, add a generic sanitized exception response, and derive worker state from `background_task_run` plus scan interval.
- [ ] **Step 4: Run `python -m pytest tests/test_phase10_observability.py tests/test_system_api.py tests/test_phase9_worker.py -q`.** Expect pass for safe errors, logging context, and health metrics.
- [ ] **Step 5: Commit `feat: add Phase10 observability metrics`.**

### Task 6: H5 Import, Operator, and Error Recovery

**Files:**
- Modify: `resume-miniprogram/src/stores/session.ts`, `resume-miniprogram/src/services/auth-api.ts`, `resume-miniprogram/src/services/http.ts`, `resume-miniprogram/src/main.ts`, `resume-miniprogram/src/pages/resume-editor/index.vue`, `resume-miniprogram/src/pages/account/index.vue`, `resume-miniprogram/src/pages.json`
- Create: `resume-miniprogram/src/services/resume-import-api.ts`, `resume-miniprogram/src/services/operator-api.ts`, `resume-miniprogram/src/services/client-error-reporting.ts`, `resume-miniprogram/src/pages/operator-knowledge/index.vue`, `resume-miniprogram/src/pages/error/index.vue`
- Test: `resume-miniprogram/src/tests/phase10-services.spec.ts`, `resume-miniprogram/src/tests/error-recovery.spec.ts`

**Interfaces:** `AuthSessionUser.role: "user" | "operator"`; `uploadResumeImport()`, `listOperatorKnowledge()`, `reportClientError()`; `installGlobalErrorHandler(app)` redirects to `/pages/error/index`.

- [ ] **Step 1: Write failing role and recovery tests.**

```ts
it("persists the operator role", () => {
  setAuthSession("token", { userId: "user-1", phone: "13800138000", role: "operator" })
  expect(getAuthUser()?.role).toBe("operator")
})

it("routes render errors to recovery", () => {
  installGlobalErrorHandler(app)
  app.config.errorHandler?.(new Error("boom"), null, "render")
  expect(reLaunch).toHaveBeenCalledWith({ url: "/pages/error/index" })
})
```

- [ ] **Step 2: Run `npm.cmd run test:unit -- phase10-services.spec.ts error-recovery.spec.ts`.** Expect failure because the new client surfaces do not exist.
- [ ] **Step 3: Implement role-aware session and sanitized client reporting.** Translate all touched login, session, and request feedback to Simplified Chinese; report errors without recursively calling the primary request wrapper.

```ts
export function installGlobalErrorHandler(app: App): void {
  app.config.errorHandler = (reason, _instance, info) => {
    void reportClientError({ message: sanitizeError(reason), component: info })
    uni.reLaunch({ url: "/pages/error/index" })
  }
}
```

- [ ] **Step 4: Implement editor import preview and operator page.** Save first, choose a PDF/Word file, upload it, let the user revise preview fields, and apply only after a Chinese confirmation. Show the operator entry only to the stored operator role; operator API still enforces JWT RBAC.
- [ ] **Step 5: Run `npm.cmd run test:unit -- phase10-services.spec.ts error-recovery.spec.ts`, `npm.cmd run build:h5`, and the Impeccable detector for all four touched pages.** Expect all tests/build to pass and detector output `[]`.
- [ ] **Step 6: Commit `feat: add Phase10 H5 operations workflows`.**

### Task 7: Environment and Final Documentation

**Files:**
- Modify: `resume-backend/.env.example`, `docs/DEPLOYMENT_PRECHECK.md`, `README.md`
- Create: `docs/phase10-changelog.md`

**Interfaces:** Documents `OPERATOR_PHONE_ALLOWLIST`, `PUSH_DISPATCHER_MODE`, push provider settings, `RESUME_IMPORT_MAX_FILE_BYTES`, and `LOG_LEVEL`; supplies final launch checklist and Phase 1-10 roadmap.

- [ ] **Step 1: Document all launch prerequisites.** Cover SMS, WeChat Open Platform, payment, push, malware scanning, PostgreSQL, worker, HTTPS, backups, secret rotation, exact `5186`/`8000` startup, and future team/provider/parsing/external-sync roadmap.
- [ ] **Step 2: Read all four resulting documents.** Run `Get-Content` for `.env.example`, `DEPLOYMENT_PRECHECK.md`, `phase10-changelog.md`, and `README.md`; confirm all required settings and final roadmap items are present without exposing any credentials.
- [ ] **Step 3: Commit `docs: complete Phase10 launch guidance`.**

### Task 8: Full Verification and Push

**Files:** Verify all Phase10 files.

- [ ] **Step 1: Run `python -m pytest tests -q`.** Expect all backend tests pass with only explicitly skipped optional tests.
- [ ] **Step 2: Run `npm.cmd run test:unit` and `npm.cmd run build:h5`.** Expect all Vitest tests pass and H5 compiles.
- [ ] **Step 3: Run Phase10 smoke tests.** Execute the five focused backend Phase10 files. Start the current worktree on an unused temporary loopback port with a unique temporary SQLite path, request `/health`, verify database/push/worker fields, stop only that process, then remove only that exact temporary directory.
- [ ] **Step 4: Run `git diff --check` and `git status --short`.** Expect no whitespace errors or uncommitted files.
- [ ] **Step 5: Push `feature/ai-resume-demo` with `git push origin feature/ai-resume-demo`.** Expect a non-force remote update.
