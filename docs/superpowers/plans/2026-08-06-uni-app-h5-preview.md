# Uni-App H5 Preview Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a browser-accessible H5 preview command while retaining the
existing WeChat Mini Program compilation target.

**Architecture:** The official Uni-App Vite plugin compiles the existing
`src/` application for both H5 and WeChat. H5 development calls FastAPI
through a Vite proxy; other Uni-App targets keep using the existing absolute
local API address.

**Tech Stack:** Uni-App Vue 3, Vite 5.2.8, `@dcloudio/vite-plugin-uni`,
`@dcloudio/uni-h5`, TypeScript, Vitest, FastAPI.

## Global Constraints

- Preserve all existing resume business logic, API contracts, CSV-unrelated
  functionality, draft persistence, and WeChat Mini Program compatibility.
- Use exact Uni-App package version `3.0.0-alpha-5020320260803001`.
- Use Vite `5.2.8`, matching the official Uni-App Vite plugin peer dependency.
- H5 preview runs on `127.0.0.1:5173`; FastAPI remains on `127.0.0.1:8000`.
- H5 proxies only `/api` and `/downloads` to FastAPI.
- Do not push, merge, or create a pull request.

---

### Task 1: Configure And Verify H5 Preview

**Files:**
- Modify: `resume-miniprogram/package.json`
- Modify: `resume-miniprogram/package-lock.json`
- Modify: `resume-miniprogram/vite.config.ts`
- Modify: `resume-miniprogram/src/services/http.ts`
- Modify: `resume-miniprogram/src/App.vue`
- Create: `resume-miniprogram/index.html`

**Interfaces:**
- Produces `npm run dev:h5` for browser preview on `127.0.0.1:5173`.
- Produces `npm run build:h5` for a non-interactive H5 build check.
- Produces `npm run dev:mp-weixin` and `npm run build:mp-weixin` for the
  retained Mini Program target.

- [ ] **Step 1: Verify the missing preview command fails**

Run:

```powershell
cd resume-miniprogram
npm run build:h5
```

Expected: FAIL because `build:h5` does not exist.

- [ ] **Step 2: Add matching Uni-App build dependencies and scripts**

Set the following package values:

```json
{
  "scripts": {
    "dev:h5": "uni -p h5",
    "build:h5": "uni build -p h5",
    "dev:mp-weixin": "uni -p mp-weixin",
    "build:mp-weixin": "uni build -p mp-weixin"
  },
  "dependencies": {
    "@dcloudio/uni-h5": "3.0.0-alpha-5020320260803001"
  },
  "devDependencies": {
    "@dcloudio/vite-plugin-uni": "3.0.0-alpha-5020320260803001",
    "vite": "5.2.8"
  }
}
```

Run `npm install` to update `package-lock.json`.

- [ ] **Step 3: Add Uni-App Vite configuration**

Configure `vite.config.ts` with `uni()` from `@dcloudio/vite-plugin-uni`,
`host: "127.0.0.1"`, `port: 5173`, `strictPort: true`, and local proxy entries
for `/api` and `/downloads` targeting `http://127.0.0.1:8000`.
Enable `uni()` only outside Vitest so Node-only unit tests do not invoke the
application compiler.

- [ ] **Step 3a: Restore required application bootstrap files**

Replace the empty `script setup` block in `src/App.vue` with:

```ts
<script lang="ts">
export default {}
</script>
```

Create `index.html` with a `#app` root element and
`<script type="module" src="/src/main.ts"></script>` for the H5 entry.

- [ ] **Step 4: Route H5 requests through the local proxy**

Keep the existing absolute API base URL for Mini Program builds. For H5
builds only, use an empty base URL so existing request paths such as
`/api/job/query` are routed through the Vite proxy.

- [ ] **Step 5: Verify build and tests**

Run:

```powershell
cd resume-miniprogram
npm run test:unit
npm run build:h5
npm run build:mp-weixin
```

Expected: all commands exit successfully.

- [ ] **Step 6: Start and verify the preview**

Start FastAPI on `127.0.0.1:8000`, start `npm run dev:h5 -- --host 127.0.0.1`,
wait for `http://127.0.0.1:5173` to respond, then open the URL in the browser.

- [ ] **Step 7: Commit**

```powershell
git add resume-miniprogram/package.json resume-miniprogram/package-lock.json resume-miniprogram/vite.config.ts resume-miniprogram/src/services/http.ts docs/superpowers/specs/2026-08-06-uni-app-h5-preview-design.md docs/superpowers/plans/2026-08-06-uni-app-h5-preview.md
git commit -m "feat: add uni-app h5 preview"
```
