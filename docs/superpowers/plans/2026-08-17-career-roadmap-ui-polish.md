# Career Roadmap and Dashboard Polish Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete the four-stage, user-scoped career roadmap contract and polish the existing operational dashboard into one consistent, responsive interface without changing its business foundations.

**Architecture:** The existing JWT-owned `/api/job/plan` route remains the sole career data source. The AI contract will require four paid roadmap stages while the existing server-side Free projection returns only a redacted technical preview. The single dashboard stylesheet receives a token overlay and shared state rules; the existing native HTML and vanilla JavaScript rendering functions remain the UI implementation surface.

**Tech Stack:** FastAPI, Pydantic, SQLite repositories, existing OpenAI-compatible client, pytest, vanilla HTML/CSS/JavaScript, Node verifier.

**Status:** Completed 2026-08-17. The checklist is retained as the execution record; contract, UI, browser, build, and regression verification all ran before release.

## Global Constraints

- Preserve existing JWT authentication, SQLite user isolation, LLM integration, membership/payment behavior, and resume, evidence, and delivery flows.
- Only the JWT `sub` identifies server-side data; the career-plan request contains neither `user_id` nor `client_id`.
- Keep one standalone `premium-dashboard.html`, Mock/Vite compatibility, and no external CDN, chart library, stylesheet, or dependency.
- Retain Sprint, Safe, and Backup cards. Keep user interaction state in the existing JWT-scoped local-storage namespace.
- Do not add referrals, campaigns, coupons, recurring billing, enterprise subscriptions, or customer service features.

---

### Task 1: Enforce the Four-Stage Detailed Roadmap Contract [Complete]

**Files:**

- Modify: `resume-backend/app/schemas/career.py`
- Modify: `resume-backend/app/services/ai_client.py`
- Modify: `resume-backend/tests/test_job_plan_api.py`

**Interfaces:**

- Detailed `JobPlanResponse` contains technical and management tracks with `entry`, `junior`, `mid`, and `senior` nodes in that order.
- Brief server projections remain redacted, technical-only, and limited to two preview nodes.

- [ ] **Step 1: Add a focused failing contract test**

```python
def test_detailed_job_plan_has_four_ordered_nodes_per_track(api_client, auth_headers):
    headers = auth_headers("13900000002")
    grant_vip(api_client, "basic")
    response = api_client.post("/api/job/plan", headers=headers,
                               json={"role_name": "Data Engineer", "expand_detail": True})
    tracks = response.json()["data"]["promotion_tracks"]
    assert all([node["level"] for node in track["nodes"]] == ["entry", "junior", "mid", "senior"] for track in tracks)
```

- [ ] **Step 2: Run the focused test and observe failure**

Run: `resume-backend/.venv/Scripts/python.exe -m pytest tests/test_job_plan_api.py -q`

Expected: the existing fixture has only entry, junior, and senior nodes.

- [ ] **Step 3: Validate detailed plans and strengthen the AI prompt**

```python
@model_validator(mode="after")
def validate_roadmap_stages(self):
    if self.report_scope == "detailed":
        expected = ["entry", "junior", "mid", "senior"]
        if any([node.level for node in track.nodes] != expected for track in self.promotion_tracks):
            raise ValueError("detailed promotion tracks must contain entry, junior, mid, senior nodes")
    return self
```

Update the OpenAI-compatible prompt to name all six report dimensions, require the exact status vocabulary and both tracks, and use `expand_detail` to request concise versus full evidence-grounded content. Update the deterministic AI fixture to return four valid nodes per track.

- [ ] **Step 4: Verify the API contract**

Run: `resume-backend/.venv/Scripts/python.exe -m pytest tests/test_job_plan_api.py -q`

Expected: PASS, including Free redaction and Basic detailed output.

- [ ] **Step 5: Commit the backend contract**

```bash
git add resume-backend/app/schemas/career.py resume-backend/app/services/ai_client.py resume-backend/tests/test_job_plan_api.py
git commit -m "feat: complete career roadmap contract"
```

### Task 2: Complete Frontend Roadmap Normalization and Interaction State [Complete]

**Files:**

- Modify: `premium-dashboard.html`
- Modify: `scripts/verify-premium-dashboard.mjs`

**Interfaces:**

- `defaultPromotionTracks(roleName)` creates four stages per track: `entry`, `junior`, `mid`, `senior`.
- `normalizeCareerPlan(plan, roleName)` accepts full server plans and produces an interactive native roadmap without exposing paid data from a Free cache.

- [ ] **Step 1: Add failing dashboard assertions**

```javascript
const fallbackTracks = sandbox.defaultPromotionTracks('Data Engineer');
assert.deepEqual(fallbackTracks[0].nodes.map(node => node.level), ['entry', 'junior', 'mid', 'senior']);
assert.equal(fallbackTracks[1].nodes.length, 4);
```

- [ ] **Step 2: Run the verifier and observe failure**

Run: `node scripts/verify-premium-dashboard.mjs`

Expected: FAIL because the fallback currently skips the `mid` stage.

- [ ] **Step 3: Add the smallest normalization and visual update**

Make both fallback tracks use four concise stages and retain the existing per-user task, track-selection, and comparison-history keys. Use one native browser tooltip per roadmap node and keep all nodes keyboard-operable buttons. Preserve the current membership check before management-roadmap and node-task detail access.

- [ ] **Step 4: Verify dashboard helpers**

Run: `node scripts/verify-premium-dashboard.mjs`

Expected: PASS with all previous cache-isolation, Free-projection, and helper checks intact.

- [ ] **Step 5: Commit the dashboard contract**

```bash
git add premium-dashboard.html scripts/verify-premium-dashboard.mjs
git commit -m "feat: complete four-stage career roadmap"
```

### Task 3: Apply the Shared Operational Visual System [Complete]

**Files:**

- Modify: `premium-dashboard.html`
- Modify: `scripts/verify-premium-dashboard.mjs`

**Interfaces:**

- Root variables expose three radius tiers, three elevation tiers, six type tiers, fixed spacing tiers, a unified 0.24 second interaction curve, and semantic status colors.
- Shared `card`, `btn`, `input`, table, modal, collapse, and mobile rules consume those tokens.

- [ ] **Step 1: Add failing static style assertions**

```javascript
for (const hook of ['--radius-sm:', '--shadow-modal:', '--type-page:', ':focus-visible', '.btn:active', 'prefers-reduced-motion']) {
  assert.match(html, new RegExp(hook.replace(/[.*+?^${}()|[\\]\\]/g, '\\$&')));
}
```

- [ ] **Step 2: Run the verifier and observe failure**

Run: `node scripts/verify-premium-dashboard.mjs`

Expected: FAIL because the shared token and interaction hooks are absent.

- [ ] **Step 3: Implement tokens and component-state polish**

Define only existing-style business-blue, teal, amber, and red semantic variables; alias old tokens where needed so unrelated templates remain stable. Apply the shared transition to buttons, cards, inputs, dropdowns, collapse content, and modal entry. Add keyboard focus, input focus, disabled, table-row hover, scrollbar, selection, reduced-motion, and no-backdrop-filter fallback states. Keep no hover-only feature and use structural mobile grids rather than viewport-scaled type.

- [ ] **Step 4: Verify desktop, tablet, and mobile renderings**

Run: `node scripts/verify-premium-dashboard.mjs`

Run: `npm.cmd run build:h5`

Use the running Vite page at 1440px, 900px, and 390px to inspect menu, modal, roadmap, comparison, and long tag wrapping; fix only concrete overlap or overflow findings.

- [ ] **Step 5: Commit the visual polish**

```bash
git add premium-dashboard.html scripts/verify-premium-dashboard.mjs
git commit -m "style: polish dashboard interaction system"
```

### Task 4: Release Verification and Push [Complete; pushed to feature/ai-resume-demo]

**Files:**

- Modify only files required by concrete verification findings.

- [ ] **Step 1: Run the complete verification set**

Run: `resume-backend/.venv/Scripts/python.exe -m pytest -q`

Run: `node scripts/verify-premium-dashboard.mjs`

Run: `npm.cmd run build:h5`

Run: `git diff --check`

Expected: all commands exit zero and the diff has no whitespace errors.

- [ ] **Step 2: Run the final interface inspection**

Run: `node C:/Users/16102/.codex/skills/impeccable/scripts/detect.mjs --json premium-dashboard.html`

Inspect the connected Vite page at desktop and mobile breakpoints. Confirm no clipping, overlap, broken modal, or inaccessible focus state.

- [ ] **Step 3: Commit and push the verified release**

```bash
git add premium-dashboard.html resume-backend/app/schemas/career.py resume-backend/app/services/ai_client.py resume-backend/tests/test_job_plan_api.py scripts/verify-premium-dashboard.mjs docs/superpowers/plans/2026-08-17-career-roadmap-ui-polish.md
git commit -m "feat: polish interactive career roadmap"
git push origin feature/ai-resume-demo
```

## Plan Self-Review

- Coverage: Task 1 covers the standardized, detailed LLM contract and paid-only complete roadmap; Task 2 covers four-stage native visualization and existing user-scoped interaction state; Task 3 covers the global visual, animation, responsive, and browser-surface requirements; Task 4 covers regression and browser verification before delivery.
- No placeholders: every task names its files, command, API surface, expected result, and required behavior.
- Type consistency: the backend returns `JobPlanResponse`; the dashboard `normalizeCareerPlan` consumes its `promotion_tracks`; `defaultPromotionTracks` provides the same ordered stage levels when offline.
