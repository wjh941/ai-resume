# Web And H5 Frontends Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Consolidate the current project into one checkout and add a real, standalone Web frontend without changing the existing Uni-App H5 preview, WeChat Mini Program, or FastAPI API contracts.

**Architecture:** `resume-miniprogram` remains the Uni-App application and continues to own H5 preview on port `5186` and Mini Program builds. A new `web-frontend` Vue 3/Vite application runs on `5174`, proxies business requests to the existing FastAPI service on `8000`, and uses the existing JWT responses and protected APIs. Repository consolidation happens only after all source changes are committed and pushed.

**Tech Stack:** Vue 3, Vite, Vitest, FastAPI, existing JWT authentication, existing Uni-App Vue 3 application.

## Global Constraints

- Keep `resume-miniprogram` untouched as the Mini Program and H5 source; its H5 port remains `127.0.0.1:5186`.
- Keep FastAPI at `127.0.0.1:8000`; do not change, stop, or replace a running backend process.
- The standalone Web frontend runs only on `127.0.0.1:5174` in development.
- Reuse existing `/api` endpoints and `Authorization: Bearer <JWT>` behavior; add no backend API or database changes.
- All Web-facing labels, validation messages, empty states, and error messages are Simplified Chinese.
- Keep `D:/Projects/16102` unchanged because it is not an AI-resume project checkout.

---

### Task 1: Standalone Web Runtime And Authenticated HTTP Client

**Files:**
- Create: `web-frontend/package.json`
- Create: `web-frontend/vite.config.ts`
- Create: `web-frontend/index.html`
- Create: `web-frontend/src/main.ts`
- Create: `web-frontend/src/lib/api.ts`
- Create: `web-frontend/src/lib/session.ts`
- Create: `web-frontend/src/tests/api.spec.ts`

**Interfaces:**
- Consumes: `POST /api/auth/login-phone`, `POST /api/auth/login-password`, `POST /api/auth/register-password`, `GET /api/auth/me`, and `POST /api/auth/logout`.
- Produces: `requestApi<T>(path: string, init?: RequestInit): Promise<T>`, `saveSession(token: string, user: SessionUser): void`, `clearSession(): void`, and `readSession(): Session | null`.

- [ ] **Step 1: Write the failing HTTP client tests**

```ts
import { describe, expect, it, vi } from "vitest"
import { requestApi } from "../lib/api"
import { clearSession, saveSession } from "../lib/session"

describe("requestApi", () => {
  it("adds the saved JWT bearer token", async () => {
    saveSession("jwt-token", { user_id: "u-1", role: "user" })
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({ code: "ok", data: { id: 1 } })))
    vi.stubGlobal("fetch", fetchMock)

    await requestApi("/api/auth/me")

    expect(fetchMock.mock.calls[0][1].headers.Authorization).toBe("Bearer jwt-token")
    clearSession()
  })
})
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd web-frontend; npm run test -- api.spec.ts`

Expected: FAIL because `src/lib/api.ts` and `src/lib/session.ts` do not exist.

- [ ] **Step 3: Implement the minimum client and session storage**

```ts
export async function requestApi<T>(path: string, init: RequestInit = {}): Promise<T> {
  const session = readSession()
  const response = await fetch(path, {
    ...init,
    headers: { "Content-Type": "application/json", ...init.headers, ...(session ? { Authorization: `Bearer ${session.token}` } : {}) },
  })
  if (response.status === 401) clearSession()
  const body = await response.json()
  if (!response.ok || body.code !== "ok") throw new Error(body.detail || body.message || "请求未完成，请稍后重试")
  return body.data as T
}
```

Implement `saveSession`, `readSession`, and `clearSession` around the `resume-web-session` localStorage key. Configure the Vite development proxy for `/api`, `/health`, and `/downloads` to `http://127.0.0.1:8000`.

- [ ] **Step 4: Run focused tests and the Web production build**

Run: `cd web-frontend; npm run test -- api.spec.ts; npm run build`

Expected: the client test passes and Vite emits `web-frontend/dist`.

- [ ] **Step 5: Commit**

```bash
git add web-frontend/package.json web-frontend/vite.config.ts web-frontend/index.html web-frontend/src
git commit -m "feat(web): add standalone runtime and api client"
```

### Task 2: Web Application Shell, Login, And Navigation

**Files:**
- Create: `web-frontend/src/App.vue`
- Create: `web-frontend/src/components/WebSidebar.vue`
- Create: `web-frontend/src/components/WebTopbar.vue`
- Create: `web-frontend/src/components/LoginPanel.vue`
- Create: `web-frontend/src/styles/base.css`
- Create: `web-frontend/src/tests/session.spec.ts`
- Modify: `web-frontend/src/main.ts`

**Interfaces:**
- Consumes: `requestApi`, `saveSession`, `readSession`, and `clearSession` from Task 1.
- Produces: authenticated application state with `activeView` values `overview`, `resume`, `career`, `jobs`, `applications`, `insights`, and `account`.

- [ ] **Step 1: Write the failing session tests**

```ts
import { describe, expect, it } from "vitest"
import { clearSession, readSession, saveSession } from "../lib/session"

describe("session storage", () => {
  it("removes expired or logged-out account state", () => {
    saveSession("token", { user_id: "u-1", role: "operator" })
    clearSession()
    expect(readSession()).toBeNull()
  })
})
```

- [ ] **Step 2: Run the test to verify it fails before implementation**

Run: `cd web-frontend; npm run test -- session.spec.ts`

Expected: FAIL until the session implementation is complete.

- [ ] **Step 3: Implement the browser-first shell and login flow**

```vue
<LoginPanel v-if="!session" @authenticated="session = $event" />
<main v-else class="web-shell">
  <WebSidebar :active-view="activeView" @navigate="activeView = $event" />
  <section class="web-workspace"><WebTopbar :user="session.user" @logout="logout" /><RouterFreeView :name="activeView" /></section>
</main>
```

`LoginPanel` exposes Chinese tabs for phone-code login and account-password login. Use the existing auth endpoints and store the returned JWT only after a successful response. The sidebar remains visible on desktop and becomes a compact horizontal navigation at narrow widths. The base stylesheet defines shared colors, 8px-or-less card radii, focus states, and reduced-motion-safe transitions.

- [ ] **Step 4: Run focused tests and build**

Run: `cd web-frontend; npm run test -- session.spec.ts; npm run build`

Expected: PASS and a production Web bundle without TypeScript errors.

- [ ] **Step 5: Commit**

```bash
git add web-frontend/src
git commit -m "feat(web): add authenticated application shell"
```

### Task 3: Core Job-Seeking Views And Existing API Workflows

**Files:**
- Create: `web-frontend/src/views/OverviewView.vue`
- Create: `web-frontend/src/views/ResumeView.vue`
- Create: `web-frontend/src/views/CareerView.vue`
- Create: `web-frontend/src/views/JobsView.vue`
- Create: `web-frontend/src/views/ApplicationsView.vue`
- Create: `web-frontend/src/views/InsightsView.vue`
- Create: `web-frontend/src/views/AccountView.vue`
- Create: `web-frontend/src/lib/dashboard.ts`
- Create: `web-frontend/src/tests/dashboard.spec.ts`
- Modify: `web-frontend/src/App.vue`

**Interfaces:**
- Consumes: existing `GET /api/applications`, `GET /api/drafts/list`, `GET /api/career/tasks`, `POST /api/job/query`, `POST /api/career/recommend`, `POST /api/career/annual-insights/query`, `GET /api/auth/me`, and `POST /api/auth/logout`.
- Produces: `loadOverview(): Promise<OverviewState>` and clearly separated view components that display actionable data or a Chinese empty state.

- [ ] **Step 1: Write the failing overview aggregation test**

```ts
import { expect, it, vi } from "vitest"
import { loadOverview } from "../lib/dashboard"

it("aggregates the existing dashboard endpoints", async () => {
  const request = vi.fn().mockResolvedValueOnce({ items: [{ id: "a-1" }] }).mockResolvedValueOnce({ items: [] }).mockResolvedValueOnce({ items: [{ status: "open" }] })
  await expect(loadOverview(request)).resolves.toEqual({ applicationCount: 1, draftCount: 0, openTaskCount: 1 })
})
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd web-frontend; npm run test -- dashboard.spec.ts`

Expected: FAIL because `loadOverview` does not exist.

- [ ] **Step 3: Implement focused view workflows**

```ts
export async function loadOverview(request = requestApi) {
  const [applications, drafts, tasks] = await Promise.all([
    request<{ items: { id: string }[] }>("/api/applications"),
    request<{ items: { id: string }[] }>("/api/drafts/list"),
    request<{ items: { status: string }[] }>("/api/career/tasks"),
  ])
  return { applicationCount: applications.items.length, draftCount: drafts.items.length, openTaskCount: tasks.items.filter((task) => task.status !== "completed").length }
}
```

Implement each view as a narrow adapter over existing data:

- `ResumeView`: list resume drafts and provide the existing draft-save/import entry points.
- `CareerView`: show career tasks and career-plan generation controls.
- `JobsView`: query jobs, show match information, and let users open favorites/subscription controls.
- `ApplicationsView`: show application status, upcoming interviews, and timeline entries.
- `InsightsView`: collect job role and year, then present concise or professional annual insight responses returned by the server.
- `AccountView`: display authenticated account details, privacy data scope, and a logout control.

Use Chinese loading, error, and no-data states for every async panel. Keep the report tier request as an additive request parameter only; authorization remains enforced by the server response.

- [ ] **Step 4: Run Web tests and build**

Run: `cd web-frontend; npm run test; npm run build`

Expected: all Web tests pass and build output completes.

- [ ] **Step 5: Commit**

```bash
git add web-frontend/src
git commit -m "feat(web): add job seeking workspace views"
```

### Task 4: Project Entry Documentation And Dual-Frontend Verification

**Files:**
- Modify: `README.md`
- Modify: `resume-miniprogram/.env.example`
- Create: `web-frontend/.env.example`

**Interfaces:**
- Consumes: the H5 `5186`, Web `5174`, and backend `8000` contracts from Tasks 1-3.
- Produces: exact local commands and a clear distinction between Web, H5 preview, and WeChat Mini Program output.

- [ ] **Step 1: Write a command-level documentation validation checklist**

```text
README must name all three local endpoints:
- http://127.0.0.1:8000 for FastAPI
- http://127.0.0.1:5186 for the Uni-App H5 preview
- http://127.0.0.1:5174 for the standalone Web frontend
```

- [ ] **Step 2: Verify the checklist fails against the current documentation**

Run: `rg -n "127\.0\.0\.1:5174|web-frontend" README.md`

Expected: no matches before the documentation update.

- [ ] **Step 3: Document exact startup and environment behavior**

Add separate commands for backend, Mini Program H5, Mini Program build, and standalone Web development/build. Document `VITE_API_BASE_URL` as the Web app's deployment API origin and preserve `VITE_RESUME_API_URL` for Uni-App. State that the Web app is the desktop-browser product and the H5 app is the Mini Program preview path.

- [ ] **Step 4: Run all build and test commands**

Run:

```powershell
cd resume-backend; .\.venv\Scripts\python.exe -m pytest tests -q
cd ..\resume-miniprogram; npm run test:unit; npm run build:h5
cd ..\web-frontend; npm run test; npm run build
```

Expected: all existing backend/H5 tests and all Web tests pass; both frontend production builds succeed.

- [ ] **Step 5: Commit**

```bash
git add README.md resume-miniprogram/.env.example web-frontend/.env.example
git commit -m "docs: document web and h5 frontend entry points"
```

### Task 5: Safely Consolidate To A Single Checkout

**Files:**
- Modify: Git worktree metadata only; no application-source modification.

**Interfaces:**
- Consumes: a clean, committed, pushed `feature/ai-resume-demo` branch with all changes from Tasks 1-4.
- Produces: `D:/Projects/ai-resume-miniprogram` checked out on `feature/ai-resume-demo` and no linked duplicate source checkout.

- [ ] **Step 1: Verify source and remote safety before deletion**

Run:

```powershell
Set-Location D:\Projects\ai-resume-miniprogram\.worktrees\feature-ai-resume-demo
git status --short
git log --oneline origin/feature/ai-resume-demo..HEAD
```

Expected: no status output and no unpushed commits.

- [ ] **Step 2: Verify the retained source revision before moving it**

Run: `git rev-parse HEAD; git branch --show-current`

Expected: a committed `feature/ai-resume-demo` revision containing the Web frontend and documentation commits.

- [ ] **Step 3: Remove only the duplicate linked worktree and make the root checkout current**

Run:

```powershell
Set-Location D:\Projects\ai-resume-miniprogram
git worktree remove .worktrees\feature-ai-resume-demo
git switch feature/ai-resume-demo
git worktree prune
git worktree list
```

Expected: only `D:/Projects/ai-resume-miniprogram` remains in `git worktree list`; it is on `feature/ai-resume-demo`.

- [ ] **Step 4: Smoke-check both frontend entry points without touching the backend**

Run:

```powershell
cd D:\Projects\ai-resume-miniprogram\resume-miniprogram; npm run dev:h5
cd D:\Projects\ai-resume-miniprogram\web-frontend; npm run dev
```

Expected: H5 binds to `127.0.0.1:5186`, Web binds to `127.0.0.1:5174`, and the existing FastAPI health endpoint remains available on `127.0.0.1:8000`.

- [ ] **Step 5: Push the final branch state**

```bash
git push origin feature/ai-resume-demo
```

Expected: `origin/feature/ai-resume-demo` contains the exact source state held by the sole remaining local checkout.

## Self-Review

- Spec coverage: Tasks 1-3 create the standalone Web product, Task 4 preserves and documents distinct Web/H5/backend entry points, and Task 5 reduces the project to one local checkout while leaving unrelated `D:/Projects/16102` alone.
- Placeholder scan: no implementation section relies on an unspecified API or later design decision; all listed Web views map to existing routes.
- Interface consistency: all protected Web calls share `requestApi`, all login flows use the existing auth response shape, and frontend ports are fixed to their documented roles.
