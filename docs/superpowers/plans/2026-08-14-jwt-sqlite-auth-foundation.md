# JWT SQLite Auth Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add JWT-backed multi-user ownership to the premium dashboard and
FastAPI backend while retaining SQLite and authenticated, user-scoped local
preview caches during the transition.

**Architecture:** Add a small auth service and `users` repository around a
versioned HS256 token, then pass `current_user_id` into each user-owned
repository method. SQLite schema migration stays in `app.db`; all production
AI calls use the configured OpenAI-compatible client. The dashboard owns a
small web-only auth utility which namespaces its existing local cache and
centralizes authenticated fetch/error handling.

**Tech Stack:** FastAPI, Pydantic v2, SQLite, PyJWT, httpx, vanilla HTML/CSS/JS,
Node built-in VM verification, pytest.

## Global Constraints

- Keep SQLite; do not add SQLAlchemy or a cloud database runtime in this phase.
- Keep existing localStorage and in-memory Mock preview behavior, but scope
  business keys by JWT user ID and never auto-import legacy unscoped keys.
- Keep `GET /health` and the named `/api/auth/*` endpoints public; every other
  `/api/*` endpoint must require a valid Bearer token.
- Trust only JWT `sub` as the user identity. Ignore all frontend `client_id`
  and `user_id` values for authorization.
- Keep the existing dashboard UI language, colors, modal system, and business
  workflows. Do not add payments, membership, sharing, or operations features.
- Production AI has no mock provider. Browser fallback stays temporary and
  user-scoped; automated tests may inject fakes at the application boundary.

---

### Task 1: Versioned JWT Authentication Primitives

**Files:**
- Create: `resume-backend/app/schemas/auth.py`
- Create: `resume-backend/app/repositories/users.py`
- Create: `resume-backend/app/services/auth.py`
- Create: `resume-backend/app/api/auth.py`
- Modify: `resume-backend/app/config.py`
- Modify: `resume-backend/app/db.py`
- Modify: `resume-backend/main.py`
- Modify: `resume-backend/requirements.txt`
- Modify: `resume-backend/tests/conftest.py`
- Test: `resume-backend/tests/test_auth_api.py`

**Interfaces:**
- Produces `AuthService.issue_token(user_id: str, token_version: int) -> str`.
- Produces `current_user_id(request: Request, credentials: HTTPAuthorizationCredentials | None) -> str`.
- Produces `UserRepository.find_or_create_by_phone(phone: str) -> UserRecord` and
  `UserRepository.invalidate_tokens(user_id: str) -> None`.
- Produces public `POST /api/auth/send-code`, `/login-phone`, `/wx-login`,
  `/logout`, and protected `GET /api/auth/me`.

- [ ] **Step 1: Write failing authentication tests**

```python
def test_demo_phone_login_issues_a_versioned_token(api_client):
    sent = api_client.post("/api/auth/send-code", json={"phone": "13800138000"})
    assert sent.json()["data"]["demo_code"] == "123456"
    login = api_client.post("/api/auth/login-phone", json={"phone": "13800138000", "code": "123456"})
    assert login.status_code == 200
    assert login.json()["data"]["token"]


def test_expired_tampered_and_logged_out_tokens_are_unauthorised(api_client, auth_headers):
    token = auth_headers("13800138000")
    assert api_client.get("/api/template/list", headers=token).status_code == 200
    assert api_client.post("/api/auth/logout", headers=token).status_code == 200
    assert api_client.get("/api/template/list", headers=token).status_code == 401
    assert api_client.get("/api/template/list", headers={"Authorization": "Bearer forged"}).status_code == 401
```

- [ ] **Step 2: Run the test to verify failure**

Run: `python -m pytest tests/test_auth_api.py -v`

Expected: FAIL because no auth router, JWT service, or `auth_headers` fixture exists.

- [ ] **Step 3: Implement the smallest secure authentication boundary**

```python
def current_user_id(request: Request, credentials = Depends(HTTPBearer(auto_error=False))) -> str:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Authentication is required")
    return request.app.state.auth_service.verify(credentials.credentials)


@router.post("/logout")
def logout(request: Request, token: str | None = Depends(optional_bearer_token)):
    if token:
        request.app.state.auth_service.invalidate(token)
    return success({"logged_out": True})
```

Use PyJWT for signing and verification. Include exactly `sub`, `token_version`,
and `exp` claims. Add `users` creation and token-version lookup to the
idempotent database initializer, enable `PRAGMA foreign_keys = ON` per
connection, and reject `AUTH_DEMO_MODE=false` login attempts when no SMS
provider configuration exists. Put Alibaba, Tencent, and generic HTTP SMS
hooks behind comments and a provider interface without sending a real message.

- [ ] **Step 4: Run focused tests**

Run: `python -m pytest tests/test_auth_api.py -v`

Expected: PASS for demo login, missing Bearer rejection, signature validation,
expiry validation, and logout token-version invalidation.

- [ ] **Step 5: Commit**

```bash
git add resume-backend/app resume-backend/main.py resume-backend/requirements.txt resume-backend/tests
git commit -m "feat: add versioned JWT authentication"
```

### Task 2: SQLite User Ownership Migration and User-Owned Repositories

**Files:**
- Create: `resume-backend/migrations/20260814_jwt_user_isolation.sql`
- Modify: `resume-backend/app/db.py`
- Modify: `resume-backend/app/repositories/drafts.py`
- Modify: `resume-backend/app/repositories/evidence.py`
- Modify: `resume-backend/app/repositories/applications.py`
- Modify: `resume-backend/app/repositories/assessment.py`
- Modify: `resume-backend/app/repositories/career_profiles.py`
- Modify: `resume-backend/app/services/downloads.py`
- Modify: `resume-backend/app/schemas/draft.py`
- Modify: `resume-backend/app/schemas/evidence.py`
- Modify: `resume-backend/app/schemas/application.py`
- Modify: `resume-backend/app/schemas/assessment.py`
- Modify: `resume-backend/app/schemas/career.py`
- Test: `resume-backend/tests/test_user_data_isolation.py`

**Interfaces:**
- Consumes `current_user_id` and `UserRepository` from Task 1.
- Changes user-owned repository methods to accept `user_id` as their first
  argument: `save(user_id, payload)`, `get(user_id, resource_id)`,
  `list(user_id, status=None)`, and `delete(user_id, resource_id)`.
- Changes `DownloadService.register(user_id, output_path, filename)` and
  `DownloadService.resolve(user_id, token)`.

- [ ] **Step 1: Write failing two-user repository tests**

```python
def test_draft_evidence_application_assessment_and_profile_are_user_scoped(tmp_path):
    drafts = DraftRepository(tmp_path / "resume.db")
    first = drafts.save("user-a", DraftSaveRequest.model_validate(make_draft_payload()))
    assert drafts.list("user-a") == [first]
    with pytest.raises(DraftNotFoundError):
        drafts.get("user-b", first["id"])
```

Add one equivalent assertion for each user-owned table, and assert that
`DownloadService.resolve("user-b", token)` raises `DownloadNotFoundError`.

- [ ] **Step 2: Run the test to verify failure**

Run: `python -m pytest tests/test_user_data_isolation.py -v`

Expected: FAIL because repositories still accept and query `client_id`.

- [ ] **Step 3: Implement schema migration and explicit user predicates**

```sql
ALTER TABLE user_draft ADD COLUMN user_id TEXT REFERENCES users(user_id);
CREATE INDEX IF NOT EXISTS idx_user_draft_owner_updated
  ON user_draft (user_id, updated_at DESC, id DESC);
```

Apply the same nullable transition column and owner index to evidence,
applications, profiles, assessments, and download records. `db.py` must use
`PRAGMA table_info` before every `ALTER TABLE`, so fresh and already-migrated
databases both start. Keep legacy `client_id` values untouched and set the
column internally to `user_id` for all new writes. Repositories must select,
update, and delete using `id = ? AND user_id = ?`; profile and assessment
upserts must target the current user's single record rather than client input.

- [ ] **Step 4: Run focused tests**

Run: `python -m pytest tests/test_user_data_isolation.py tests/test_drafts_api.py tests/test_evidence_api.py tests/test_applications_api.py tests/test_assessment_repository.py -v`

Expected: PASS with all legacy callers updated to obtain an authenticated user.

- [ ] **Step 5: Commit**

```bash
git add resume-backend/app resume-backend/migrations resume-backend/tests
git commit -m "feat: isolate SQLite business data by user"
```

### Task 3: Protect and Rewire All API Routes

**Files:**
- Modify: `resume-backend/app/api/drafts.py`
- Modify: `resume-backend/app/api/evidence.py`
- Modify: `resume-backend/app/api/applications.py`
- Modify: `resume-backend/app/api/assessment.py`
- Modify: `resume-backend/app/api/career.py`
- Modify: `resume-backend/app/api/ai.py`
- Modify: `resume-backend/app/api/consultation.py`
- Modify: `resume-backend/app/api/exports.py`
- Modify: `resume-backend/app/api/knowledgebase.py`
- Modify: `resume-backend/app/api/templates.py`
- Modify: `resume-backend/main.py`
- Test: `resume-backend/tests/test_api_authentication.py`
- Test: `resume-backend/tests/test_exports_api.py`

**Interfaces:**
- Consumes `current_user_id` from Task 1 and user-scoped repositories from Task 2.
- All non-auth `/api/*` endpoints declare `user_id: str = Depends(current_user_id)`.
- User input schemas no longer require `client_id`; extra legacy values are
  ignored by the API and do not reach repository query predicates.

- [ ] **Step 1: Write failing API access and cross-account tests**

```python
def test_every_business_api_requires_a_bearer_token(api_client):
    assert api_client.get("/api/draft/list").status_code == 401
    assert api_client.get("/api/job/suggestions?q=data").status_code == 401
    assert api_client.get("/health").status_code == 200


def test_second_user_cannot_download_first_users_export(api_client, auth_headers, saved_draft):
    owner = auth_headers("13800138000")
    other = auth_headers("13900139000")
    response = api_client.post("/api/export/word", json={"draft_id": saved_draft}, headers=owner)
    token = response.json()["data"]["download_url"].rsplit("/", 1)[-1]
    assert api_client.get(f"/downloads/{token}", headers=other).status_code == 404
```

- [ ] **Step 2: Run the test to verify failure**

Run: `python -m pytest tests/test_api_authentication.py tests/test_exports_api.py -v`

Expected: FAIL because existing routes accept unauthenticated client IDs.

- [ ] **Step 3: Inject the current user at the route boundary**

```python
@router.get("/list")
def list_drafts(request: Request, user_id: str = Depends(current_user_id)):
    return success(request.app.state.draft_repository.list(user_id))


@router.get("/downloads/{token}")
def download_file(token: str, request: Request, user_id: str = Depends(current_user_id)):
    download = request.app.state.download_service.resolve(user_id, token)
    return FileResponse(download.path, filename=download.filename)
```

Apply the same dependency to all business endpoints, including catalog,
template, consultation, AI, and knowledge-base routes. For profile,
assessment, comparison, and export routes, remove the front-end ownership
identifier from query/body construction and derive it from the dependency.
Keep the four auth routes and health outside this dependency.

- [ ] **Step 4: Run API regression tests**

Run: `python -m pytest tests/test_api_authentication.py tests/test_drafts_api.py tests/test_evidence_api.py tests/test_applications_api.py tests/test_assessment_api.py tests/test_career_api.py tests/test_exports_api.py -v`

Expected: PASS; unauthenticated requests return 401 and cross-user resources
return 404 without revealing ownership.

- [ ] **Step 5: Commit**

```bash
git add resume-backend/app/api resume-backend/main.py resume-backend/tests
git commit -m "feat: require JWT for business APIs"
```

### Task 4: Replace Production AI Mocking and Configure Runtime Boundaries

**Files:**
- Modify: `resume-backend/app/services/ai_client.py`
- Modify: `resume-backend/app/config.py`
- Modify: `resume-backend/main.py`
- Modify: `resume-backend/.env.example`
- Modify: `resume-backend/requirements.txt`
- Test: `resume-backend/tests/test_ai_error_mapping.py`
- Test: `resume-backend/tests/test_consultation_ai_client.py`

**Interfaces:**
- Produces `AIConfigurationError`, `AIAuthenticationError`, `AIRateLimitError`,
  and `AIServiceUnavailableError` mapped to stable JSON error envelopes.
- `build_ai_client(settings)` accepts only configured Ark or OpenAI-compatible
  production clients; tests set `app.state.ai_client` explicitly.

- [ ] **Step 1: Write failing AI configuration/error tests**

```python
def test_unconfigured_ai_returns_a_friendly_service_error(api_client, auth_headers):
    response = api_client.post("/api/job/query", json={"role_name": "Data Engineer"}, headers=auth_headers())
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "ai_not_configured"


def test_http_429_maps_to_ai_rate_limited():
    client = OpenAICompatibleClient(settings, transport=rate_limited_transport)
    with pytest.raises(AIRateLimitError):
        await client.query_job("Data Engineer")
```

- [ ] **Step 2: Run the test to verify failure**

Run: `python -m pytest tests/test_ai_error_mapping.py -v`

Expected: FAIL because the backend still builds `MockAIClient`.

- [ ] **Step 3: Remove the runtime mock provider and map failures**

```python
def build_ai_client(settings: Settings) -> AIClient:
    if not settings.ai_api_key or not settings.ai_model:
        return UnconfiguredAIClient()
    if settings.ai_provider in {"ark", "openai_compatible"}:
        return OpenAICompatibleClient(settings)
    raise ValueError("AI_PROVIDER must be ark or openai_compatible")
```

Map provider 401/403 to authentication/configuration errors, 429 to rate-limit,
and provider balance/insufficient-credit error payloads to `ai_balance_exhausted`.
Keep the frontend fallback behavior out of the backend. Document required
model values and CORS origins in `.env.example`; avoid placing any secret in
source control.

- [ ] **Step 4: Run focused and existing AI tests**

Run: `python -m pytest tests/test_ai_error_mapping.py tests/test_consultation_ai_client.py tests/test_job_query_api.py tests/test_resume_rewrite_api.py -v`

Expected: PASS using explicitly injected test clients only.

- [ ] **Step 5: Commit**

```bash
git add resume-backend/app resume-backend/.env.example resume-backend/requirements.txt resume-backend/tests
git commit -m "feat: configure production AI error handling"
```

### Task 5: Dashboard Authentication and User-Scoped Cache Layer

**Files:**
- Modify: `premium-dashboard.html`
- Modify: `scripts/verify-premium-dashboard.mjs`
- Test: `scripts/verify-premium-dashboard.mjs`

**Interfaces:**
- Produces `auth.getToken()`, `auth.getUserId()`, `auth.loginPhone(phone, code)`,
  `auth.logout()`, `requireLogin()`, and `userCacheKey(key)` in the dashboard's
  web-only utility block.
- Replaces direct `fetch` usage with `apiRequest(path, options)` that adds the
  Bearer token, 120-second timeout, and 401/403 reset behavior.

- [ ] **Step 1: Extend the dashboard contract test before editing UI code**

```javascript
assert.equal(context.userCacheKey('drafts'), 'resume-dashboard:user-a:drafts');
assert.equal(context.auth.getToken(), 'header.payload.signature');
assert.match(source, /Authorization.*Bearer/);
assert.match(source, /openLoginModal/);
assert.match(source, /AUTH_DEMO_MODE/);
```

- [ ] **Step 2: Run the dashboard verification to verify failure**

Run: `node scripts/verify-premium-dashboard.mjs`

Expected: FAIL because there is no auth utility, login guard, or scoped cache
key implementation.

- [ ] **Step 3: Add the minimal web-only auth layer without changing visual language**

```javascript
function userCacheKey(key) {
  const userId = auth.getUserId();
  return userId ? `resume-dashboard:${userId}:${key}` : null;
}

async function apiRequest(path, options = {}) {
  const token = auth.getToken();
  if (!token) return requireLogin();
  const headers = Object.assign({}, options.headers || {}, { Authorization: `Bearer ${token}` });
  return fetch(`${API_BASE_URL}${path}`, Object.assign({}, options, { headers }));
}
```

Use the existing header, button, card, and modal classes to render login
status and two login tabs. Add a capture-level guard plus direct guards inside
mutation/export handlers so pointer and keyboard paths cannot bypass login.
Keep the JWT-only session key unscoped. Namespace every existing business
`loadLocal`/`saveLocal` key after login; leave legacy keys untouched. Remove
`client_id` from frontend API payloads. Preserve temporary user-scoped Mock
fallback for offline/network/AI failures only, not 401/403. Add explicit
Chinese comments for webview migration, cache isolation, SMS provider hooks,
and WeChat configuration prerequisites.

- [ ] **Step 4: Run dashboard checks and browser smoke test**

Run: `node scripts/verify-premium-dashboard.mjs`

Expected: PASS for cache scoping, token injection, 401 cleanup, login modal
hooks, and existing dashboard behavior.

Open `http://127.0.0.1:5173/premium-dashboard.html` and verify: unauthenticated
business action opens login; demo phone login changes the header; logout locks
the same action; a second demo phone sees a different local cache namespace.

- [ ] **Step 5: Commit**

```bash
git add premium-dashboard.html scripts/verify-premium-dashboard.mjs
git commit -m "feat: add dashboard JWT login layer"
```

### Task 6: End-to-End Regression and Deployment Documentation

**Files:**
- Modify: `README.md`
- Modify: `resume-backend/.env.example`
- Modify: `resume-backend/migrations/20260814_jwt_user_isolation.sql`
- Test: `resume-backend/tests/test_auth_api.py`
- Test: `resume-backend/tests/test_user_data_isolation.py`

**Interfaces:**
- Consumes all tasks above.
- Documents exact configuration names: `JWT_SECRET`, `JWT_EXPIRE_HOURS`,
  `AUTH_DEMO_MODE`, SMS provider variables, WeChat placeholders, AI variables,
  object-storage placeholders, and `CORS_ORIGINS`.

- [ ] **Step 1: Add an end-to-end authenticated flow test**

```python
def test_two_phone_users_keep_all_dashboard_resources_isolated(api_client, auth_headers, resume_payload):
    first = auth_headers("13800138000")
    second = auth_headers("13900139000")
    draft_id = api_client.post("/api/draft/save", json={"job_title": "Data Engineer", "template_id": "technology", "resume": resume_payload}, headers=first).json()["data"]["id"]
    assert api_client.get(f"/api/draft/{draft_id}", headers=second).status_code == 404
```

- [ ] **Step 2: Run the test to verify the assembled system**

Run: `python -m pytest tests/test_auth_api.py tests/test_user_data_isolation.py tests/test_api_authentication.py -v`

Expected: PASS with all Token and ownership checks enabled.

- [ ] **Step 3: Document deployment and migration behavior**

Document that `AUTH_DEMO_MODE` must be false for production, a strong random
`JWT_SECRET` is required, `/downloads` requires the same Bearer header, and
legacy SQLite/localStorage records are preserved but intentionally unowned.
Include the one-time SQLite migration command and the future OSS/COS and
MySQL/PostgreSQL extension locations.

- [ ] **Step 4: Run final regression suite**

Run: `python -m pytest tests -q`

Run: `node scripts/verify-premium-dashboard.mjs`

Run: `npm.cmd run test:unit`

Run: `npm.cmd run build:h5`

Expected: all tests pass; the only permissible skip is the existing
environment-dependent Playwright PDF renderer test.

- [ ] **Step 5: Commit**

```bash
git add README.md resume-backend/.env.example resume-backend/migrations resume-backend/tests
git commit -m "docs: document JWT deployment transition"
```
