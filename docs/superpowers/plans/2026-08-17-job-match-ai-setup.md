# Job Matching and AI Setup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Execute task-by-task with a red-green test cycle and review each boundary before moving on.

**Goal:** Add JWT-owned, explainable job matching and a secure local-development AI connection flow without changing existing resume, evidence, delivery, membership, or persistence contracts.

**Architecture:** The backend derives the candidate context only from repositories scoped by JWT `sub`, then scores the existing local role catalog deterministically. A separate development-only model configuration API exposes status and accepts settings only from loopback clients; it never returns secrets and is unavailable in production. The single HTML dashboard consumes those APIs, preserves offline Mock behavior, and puts all AI entry points behind one clear model-setup guard.

**Tech Stack:** FastAPI, SQLite repositories, Pydantic, vanilla JavaScript, native CSS, browser localStorage, pytest, Node assert verifier.

## Global Constraints

- Keep `premium-dashboard.html` as one self-contained document with no CDN or new dependencies.
- Derive all backend user state from JWT `sub`; never trust a frontend user identifier or profile payload.
- Job matching is a local-catalog recommendation, not a real-time job feed; expose that limitation in the returned notice and UI.
- Model secrets are never returned or stored in browser storage. Browser configuration is allowed only on `127.0.0.1` in `APP_ENV=development` with an explicit environment switch.
- Preserve current JWT, membership, local-storage namespace, Mock fallback, and business endpoints.

---

### Task 1: Detect stale local backends and safely configure AI in development

**Files:**
- Modify: `resume-backend/main.py`
- Modify: `resume-backend/app/config.py`
- Create: `resume-backend/app/api/system.py`
- Modify: `resume-backend/.env.example`
- Create: `scripts/start-resume-backend.ps1`
- Test: `resume-backend/tests/test_system_api.py`

**Interfaces:**
- Produces `GET /health` with `capabilities: ["job_plan", "job_match", "ai_setup"]`.
- Produces `GET /api/system/ai-status` returning `configured`, `provider`, `model`, `setup_allowed` and no secret fields.
- Produces `POST /api/system/ai-config` accepting `{provider, base_url, api_key, model}` only from loopback development clients when `AI_CONFIG_UI_ENABLED=true`.

- [ ] **Step 1: Write failing tests**

```python
def test_health_declares_current_dashboard_capabilities(api_client):
    data = api_client.get('/health').json()['data']
    assert {'job_plan', 'job_match', 'ai_setup'} <= set(data['capabilities'])

def test_ai_setup_is_loopback_development_only(api_client):
    response = api_client.post('/api/system/ai-config', json={
        'provider': 'openai_compatible', 'base_url': 'https://api.example.test/v1',
        'api_key': 'secret', 'model': 'example-model'
    })
    assert response.status_code == 403
```

- [ ] **Step 2: Run the focused tests and confirm they fail because the endpoints and capability contract do not exist.**

Run: `resume-backend/.venv/Scripts/python.exe -m pytest tests/test_system_api.py -q`

- [ ] **Step 3: Implement the smallest safe configuration boundary.**

```python
if settings.app_env == 'production' or not settings.ai_config_ui_enabled:
    raise HTTPException(status_code=403, detail='Local model setup is disabled')
if request.client is None or request.client.host not in {'127.0.0.1', '::1'}:
    raise HTTPException(status_code=403, detail='Local model setup only accepts loopback clients')
```

Write only managed AI lines atomically into `resume-backend/.env`, reload `app.state.settings` and `app.state.ai_client`, and return status without `api_key`. Add `scripts/start-resume-backend.ps1` to start the current worktree with `--reload` and verify the health capabilities before reporting the URL.

- [ ] **Step 4: Run focused tests, then the full backend suite.**

Run: `resume-backend/.venv/Scripts/python.exe -m pytest tests/test_system_api.py -q`
Run: `resume-backend/.venv/Scripts/python.exe -m pytest -q`

### Task 2: Add JWT-owned local-catalog job matching

**Files:**
- Modify: `resume-backend/app/schemas/career.py`
- Create: `resume-backend/app/services/job_matching.py`
- Modify: `resume-backend/app/api/ai.py`
- Test: `resume-backend/tests/test_job_match_api.py`

**Interfaces:**
- Produces `POST /api/job/match` accepting only filters: `city`, `salary_min`, `salary_max`, `seniority`, `category`, `target_role`.
- Returns `{items, total, limited, source_notice}` where every item includes `role_name`, `company`, `salary_range`, `match_score`, `matched_skills`, `missing_skills`, `description`, `requirements`, and `detail_unlocked`.

- [ ] **Step 1: Write failing endpoint tests.**

```python
def test_free_job_match_returns_only_three_items(api_client):
    response = api_client.post('/api/job/match', json={})
    data = response.json()['data']
    assert response.status_code == 200
    assert len(data['items']) <= 3
    assert data['limited'] is True

def test_job_match_uses_only_current_jwt_user_context(api_client, auth_headers):
    owner = auth_headers('13900000111')
    other = auth_headers('13900000112')
    # Seed an owner-only resume/evidence record, then request as other.
    assert api_client.post('/api/job/match', headers=other, json={}).status_code == 200
```

- [ ] **Step 2: Run focused tests and confirm `404 Not Found`.**

Run: `resume-backend/.venv/Scripts/python.exe -m pytest tests/test_job_match_api.py -q`

- [ ] **Step 3: Implement deterministic matching.**

```python
def match(user_context: MatchContext, roles: list[RoleProfile]) -> list[JobMatch]:
    # Compare normalized resume skills, verified evidence text and saved career profile
    # against role required and entry skills; sort by score then role name.
    ...
```

Build context from `career_profile_repository`, `draft_repository`, `evidence_repository`, and `assessment_repository` with the JWT user id. For Free, project the result to three cards and no detailed gaps; Basic and Premium receive the complete list. Use transparent source labels such as `本地岗位库参考` and `以正式 JD 为准` instead of inventing a real employer or salary.

- [ ] **Step 4: Run focused and full backend tests.**

Run: `resume-backend/.venv/Scripts/python.exe -m pytest tests/test_job_match_api.py -q`
Run: `resume-backend/.venv/Scripts/python.exe -m pytest -q`

### Task 3: Add model setup, matching, onboarding, and workflow controls to the dashboard

**Files:**
- Modify: `premium-dashboard.html`
- Modify: `scripts/verify-premium-dashboard.mjs`

**Interfaces:**
- Produces `refreshAIStatus()`, `requireAI(feature)`, `openAISetupModal()` and `submitAISetup()`.
- Produces `requestJobMatches(filters)`, `renderJobMatches()`, and `openMatchDetail(roleName)`.
- Persists `resume-dashboard-onboarding` and matching preferences only through the active JWT namespace.

- [ ] **Step 1: Write failing dashboard contract checks.**

```javascript
assert.match(html, /data-page="matching"/, 'sidebar must expose Job Matching');
assert.match(html, /\/api\/job\/match/, 'dashboard must request server-owned matches');
assert.match(html, /function requireAI\b/, 'AI entry points need one configuration guard');
assert.match(html, /resume-dashboard-onboarding/, 'onboarding state must be user scoped');
```

- [ ] **Step 2: Run the verifier and confirm it fails on the missing contracts.**

Run: `node scripts/verify-premium-dashboard.mjs`

- [ ] **Step 3: Implement the smallest coherent UI extension.**

Add the sidebar matching page, filter controls, skeleton, empty guidance, free-limit upgrade state, detail modal, star collection, and delivery prefilling. Add a compact model-connection entry to the existing user menu, with password input, no secret persistence, capability status, and an explicit production-disabled state. Use `requireAI` for job plan generation, assessment generation, AI resume rewrite, and smart-fill suggestions; show the model entry instead of falling back to fabricated AI output when the API reports `ai_not_configured`.

Add the four-step optional onboarding using the existing modal and account-scoped storage: welcome, resume, evidence, first plan. Add delivery urgency tags, quick status selector, and follow-up memo insertion using the existing `notes` storage field. Add a matching shortcut and favorite button to every career-plan card.

- [ ] **Step 4: Run dashboard and browser checks.**

Run: `node scripts/verify-premium-dashboard.mjs`
Run: `npm.cmd run build:h5` from `resume-miniprogram`

Use Playwright to verify desktop and mobile matching layout, onboarding skip/next, model-gated career plan, free match limit, and no horizontal overflow.

### Task 4: Verify, document, commit, and push

**Files:**
- Modify: `README.md`
- Modify: `resume-backend/.env.example`

- [ ] **Step 1: Document startup and model setup.**

Document `scripts/start-resume-backend.ps1`, the health capability check, and that browser model setup is development-loopback only. State that production configuration belongs in server environment variables and must not expose secrets in the dashboard.

- [ ] **Step 2: Run final checks.**

Run: `node scripts/verify-premium-dashboard.mjs`
Run: `npm.cmd run build:h5`
Run: `resume-backend/.venv/Scripts/python.exe -m pytest -q`
Run: `git diff --check`

- [ ] **Step 3: Inspect desktop and mobile screenshots in one bounded browser pass, run the Impeccable detector, fix discovered issues once, then rerun affected tests.**

Run: `node C:\Users\16102\.codex\skills\impeccable\scripts\detect.mjs --json premium-dashboard.html`

- [ ] **Step 4: Commit and push the complete feature set.**

```text
feat: add job matching and local AI setup
```
