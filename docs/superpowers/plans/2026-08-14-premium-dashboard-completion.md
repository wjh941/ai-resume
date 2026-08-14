# Premium Dashboard Completion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete the missing local-first dashboard capabilities in `premium-dashboard.html` without adding dependencies or backend APIs.

**Architecture:** Keep the dashboard as the only runtime product file. Add DOM-free helpers adjacent to the existing local persistence utilities, then connect each helper through focused render and event adapters. Store every new value in normalized `state.extension`, keep API and Mock flows unchanged, and use an offline verifier to compile and check the inline script contract.

**Tech Stack:** HTML, inline CSS, vanilla JavaScript, native drag-and-drop, `localStorage`, `FileReader`, `Blob`, Node.js built-ins, existing `/api` and `/downloads` routes.

## Global Constraints

- Modify `premium-dashboard.html` as the only runtime product file.
- Preserve direct `file:` Mock fallback and Vite proxy access to `/api` and `/downloads`.
- Add no backend interface, package, CDN, scraper, or runtime dependency.
- Store extension-only data locally and normalize invalid or old values to safe defaults.
- Keep display masking separate from restorable full backups.
- Reuse existing CSS variables and component styles, and support both existing color themes.
- Preserve readiness validation, factual-evidence rules, API wrappers, download behavior, and local persistence.

## File Structure

- Modify: `premium-dashboard.html` — product UI, pure local-state helpers, persisted extension schema, event wiring, and CSS.
- Create: `scripts/verify-premium-dashboard.mjs` — no-dependency offline script compilation and contract verifier; it is not loaded by the product.
- Create: `docs/superpowers/specs/2026-08-14-premium-dashboard-completion-design.md` — accepted feature design.
- Create: `docs/superpowers/plans/2026-08-14-premium-dashboard-completion.md` — this implementation plan.

---

### Task 1: Establish a Testable Extension Core

**Files:**
- Modify: `premium-dashboard.html: extensionDefaults`, `normalizeExtension`, local persistence helpers.
- Create: `scripts/verify-premium-dashboard.mjs`.

**Interfaces:**
- Produces: `safeJsonParse(value, fallback)`, `asArray(value)`, `normalizeExtension(source)`, `storageUsage()`, `checkStorageCapacity()`, `reorderByIds(items, ids, key)`, and `persistExtension()`.
- Consumes: existing `state`, `saveLocal`, `showToast`, and modal helpers only from DOM adapters.

- [ ] **Step 1: Write the failing offline contract verifier**

```js
const required = [
  'safeJsonParse', 'normalizeExtension', 'storageUsage', 'checkStorageCapacity',
  'reorderByIds', 'maskSensitiveText', 'createSnapshot', 'restoreSnapshot'
];
for (const name of required) assert.match(script, new RegExp(`function ${name}\\b`));
assert.doesNotThrow(() => new Function(script));
```

- [ ] **Step 2: Run the verifier and record the expected initial failure**

Run: `node scripts/verify-premium-dashboard.mjs`

Expected: FAIL because `reorderByIds` and the new storage schema are absent.

- [ ] **Step 3: Implement the minimal normalized state core**

```js
function reorderByIds(items, ids, key = item => item.id) {
  const map = new Map(items.map(item => [String(key(item)), item]));
  return [...ids.map(id => map.get(String(id))).filter(Boolean),
    ...items.filter(item => !ids.includes(String(key(item))))];
}
function persistExtension() {
  state.extension = normalizeExtension(state.extension);
  saveLocal('resume-dashboard-extension', state.extension);
}
```

Add bounded `draftOrder`, `favoriteOrder`, `evidenceOrder`, `backupPreparedAt`, `releaseSeen`, `evidenceTags`, `templateSettings.sections`, and a backward-compatible snapshot record shape.

- [ ] **Step 4: Run the verifier and direct-open syntax check**

Run: `node scripts/verify-premium-dashboard.mjs`

Expected: PASS; the verifier reports one valid inline script and every required helper.

- [ ] **Step 5: Commit the extension core**

```powershell
git add premium-dashboard.html scripts/verify-premium-dashboard.mjs
git commit -m "feat: add dashboard extension core"
```

### Task 2: Complete Storage Safety, Backup, and Privacy Output

**Files:**
- Modify: `premium-dashboard.html: storage helpers, privacy page, copy/download paths, reset client flow`.
- Test: `scripts/verify-premium-dashboard.mjs`.

**Interfaces:**
- Consumes: `persistExtension`, `storageUsage`, `reorderByIds`.
- Produces: `createSnapshot(label, scope)`, `restoreSnapshot(id)`, `cleanupExpiredDeliveries()`, `cleanupOldDrafts()`, `maskResume(resume)`, `maskTextExport(text)`, `exportAllBusinessData()`.

- [ ] **Step 1: Add contract assertions for privacy and cleanup helpers**

```js
assert.equal(mask('13800000000'), '138****0000');
assert.equal(mask('name@example.com'), 'n***@example.com');
assert.match(script, /function cleanupExpiredDeliveries\b/);
assert.match(script, /function cleanupOldDrafts\b/);
```

- [ ] **Step 2: Run the verifier and confirm the new helper assertions fail**

Run: `node scripts/verify-premium-dashboard.mjs`

Expected: FAIL because cleanup helpers and the common export masker are absent.

- [ ] **Step 3: Implement capacity, snapshot, reset, and masking paths**

```js
function cleanupExpiredDeliveries(today = todayString()) {
  const removed = state.deliveries.filter(item => item.nextActionAt && item.nextActionAt < today);
  state.deliveries = state.deliveries.filter(item => !removed.includes(item));
  saveLocal('resume-dashboard-deliveries', state.deliveries);
  return removed.length;
}
function maskTextExport(text) {
  const source = String(text || '');
  if (!state.extension.maskSensitive) return source;
  return [state.resume.name, state.resume.phone, state.resume.email]
    .filter(Boolean)
    .reduce((result, value) => result.replaceAll(value, maskSensitiveText(value, true)), source);
}
```

Use browser storage estimates where available and a documented fallback estimate otherwise. The 90% modal must offer full backup, old-draft cleanup, and expired-delivery cleanup. Record a successful backup action before allowing a new `client_id`; use `crypto.randomUUID` with a timestamp/random fallback. Apply masking to resume preview, draft/report copy, text downloads, and assessment planning text, but never modify restorable backup data.

- [ ] **Step 4: Run privacy and import/restore regression checks**

Run: `node scripts/verify-premium-dashboard.mjs`

Expected: PASS; the script confirms masking, snapshot, cleanup, import, and reset handlers exist.

- [ ] **Step 5: Commit the data-safety work**

```powershell
git add premium-dashboard.html scripts/verify-premium-dashboard.mjs
git commit -m "feat: complete local safety and privacy controls"
```

### Task 3: Finish Job Favorites and Discovery

**Files:**
- Modify: `premium-dashboard.html: jobs and favorites pages, filter/search handlers, career route renderer`.
- Test: `scripts/verify-premium-dashboard.mjs`.

**Interfaces:**
- Consumes: `reorderByIds`, `persistExtension`.
- Produces: `filterJobs(items, filters)`, `toggleFavoriteJob(roleName)`, `renderFavorites()`, `renderJobCareerRoute()`, `saveSearchHistory(query)`.

- [ ] **Step 1: Extend the verifier with filtering and ordering assertions**

```js
assert.match(script, /function filterJobs\b/);
assert.match(script, /function saveSearchHistory\b/);
assert.match(script, /data-favorite-sort/);
assert.match(script, /jobSalaryMin/);
```

- [ ] **Step 2: Run the verifier and confirm the favorite-sort contract fails**

Run: `node scripts/verify-premium-dashboard.mjs`

Expected: FAIL because favorite priority drag sorting is absent.

- [ ] **Step 3: Implement favorite prioritization and robust filters**

```js
function saveSearchHistory(query) {
  state.extension.searchHistory = [query,
    ...state.extension.searchHistory.filter(item => item !== query)].slice(0, 30);
  persistExtension();
}
function favoriteJobsInPriorityOrder() {
  return reorderByIds(state.favoriteJobs, state.extension.favoriteOrder, item => item.roleName);
}
```

Clamp malformed salary bounds, keep a filter combination from hiding errors, drag-sort favorites in their page, and generate all three planning cards directly from the favorite order. Keep comparison selection limited to four roles.

- [ ] **Step 4: Run the verifier and manually exercise the job Mock path**

Run: `node scripts/verify-premium-dashboard.mjs`

Expected: PASS; favorites, search history, filters, route cards, and priority attributes are present.

- [ ] **Step 5: Commit job discovery completion**

```powershell
git add premium-dashboard.html scripts/verify-premium-dashboard.mjs
git commit -m "feat: complete local job discovery workflows"
```

### Task 4: Complete Resume Versions, Custom Templates, and Exports

**Files:**
- Modify: `premium-dashboard.html: resume page, preview renderer, draft save/compare/export handlers`.
- Test: `scripts/verify-premium-dashboard.mjs`.

**Interfaces:**
- Consumes: `createSnapshot`, `restoreSnapshot`, `maskResume`, `persistExtension`.
- Produces: `applyTemplateSettings()`, `saveCustomTemplate(name)`, `loadCustomTemplate(name)`, `buildResumeVariants(resume)`, `compareDrafts(first, second)`.

- [ ] **Step 1: Add failing template and variant assertions**

```js
assert.match(script, /function applyTemplateSettings\b/);
assert.match(script, /function buildResumeVariants\b/);
assert.match(script, /data-template-section/);
assert.match(script, /后端部署PDF\/Word解析接口后启用/);
```

- [ ] **Step 2: Run the verifier and confirm missing section controls fail**

Run: `node scripts/verify-premium-dashboard.mjs`

Expected: FAIL because module visibility controls and named template application are absent.

- [ ] **Step 3: Implement local template behavior and version actions**

```js
function applyTemplateSettings(settings = state.extension.templateSettings) {
  const preview = $('#resumePreview');
  preview.style.fontSize = `${settings.fontSize}px`;
  preview.style.padding = `${settings.margin}px`;
  $$('[data-template-section]').forEach(section => {
    section.hidden = settings.sections[section.dataset.templateSection] === false;
  });
}
function buildResumeVariants(resume) {
  return ['应届生版', '实习版', '社招版'].map(version => ({ ...resume, version }));
}
```

Create a snapshot only after a successful save, provide a resume-scope restore that does not overwrite unrelated evidence/deliveries, compare any two drafts by normalized field values, and route Word/PDF through the existing API/Mock export function using a masked display report only where text is downloaded.

- [ ] **Step 4: Run the verifier and resume Mock smoke check**

Run: `node scripts/verify-premium-dashboard.mjs`

Expected: PASS; snapshots, comparison, section controls, parser text, templates, and all variants are present.

- [ ] **Step 5: Commit resume workflow completion**

```powershell
git add premium-dashboard.html scripts/verify-premium-dashboard.mjs
git commit -m "feat: complete resume versions and templates"
```

### Task 5: Complete Evidence Ordering, Attachments, and Tag Management

**Files:**
- Modify: `premium-dashboard.html: evidence page, editor modal, render/filter/import/export handlers`.
- Test: `scripts/verify-premium-dashboard.mjs`.

**Interfaces:**
- Consumes: `reorderByIds`, `persistExtension`.
- Produces: `renderEvidenceTags()`, `assignEvidenceTags(ids, tags)`, `removeEvidenceTag(tag)`, `validateEvidenceImage(file)`, `attachSortable(container, itemSelector, onOrder)`.

- [ ] **Step 1: Add failing evidence-management assertions**

```js
assert.match(script, /function assignEvidenceTags\b/);
assert.match(script, /function validateEvidenceImage\b/);
assert.match(script, /function attachSortable\b/);
assert.match(script, /data-evidence-batch-check/);
```

- [ ] **Step 2: Run the verifier and confirm missing tag/batch behavior fails**

Run: `node scripts/verify-premium-dashboard.mjs`

Expected: FAIL because batch tags and reusable drag handlers are incomplete.

- [ ] **Step 3: Implement evidence-local behavior**

```js
function validateEvidenceImage(file) {
  if (!file?.type?.startsWith('image/')) return '请选择图片文件';
  if (file.size > 1024 * 1024) return '图片不能超过 1 MB';
  return '';
}
function assignEvidenceTags(ids, tags) {
  const selected = new Set(ids.map(String));
  state.evidence = state.evidence.map(item => selected.has(String(item.id))
    ? { ...item, tags: [...new Set([...item.tags, ...tags])] } : item);
  saveLocal('resume-dashboard-evidence', state.evidence);
}
```

Support multi-image attachment records with per-file type/size validation, attachment deletion, visible thumbnails in evidence detail, category and tag CRUD, batch assignment, and category/tag filters. Use the same native sort helper and persist the result immediately.

- [ ] **Step 4: Run the verifier and evidence import/export regression check**

Run: `node scripts/verify-premium-dashboard.mjs`

Expected: PASS; ordering, attachment validation, tags, batch selectors, and filtering hooks are present.

- [ ] **Step 5: Commit evidence completion**

```powershell
git add premium-dashboard.html scripts/verify-premium-dashboard.mjs
git commit -m "feat: complete evidence organization workflows"
```

### Task 6: Complete Delivery Calendar, Interview Notes, and Statistics

**Files:**
- Modify: `premium-dashboard.html: delivery page, delivery render/export handlers, extension panel`.
- Test: `scripts/verify-premium-dashboard.mjs`.

**Interfaces:**
- Consumes: `persistExtension`, `maskTextExport`.
- Produces: `calendarMonthDays(year, month)`, `deliveryStats(deliveries)`, `interviewNotesKey(deliveryId, questionId)`, `deliveryCsvRow(item)`.

- [ ] **Step 1: Add failing calendar/statistics contracts**

```js
assert.match(script, /function calendarMonthDays\b/);
assert.match(script, /function interviewNotesKey\b/);
assert.match(script, /class="delivery-chart"/);
assert.match(script, /deliveryCsvRow\b/);
```

- [ ] **Step 2: Run the verifier and confirm the month-grid contract fails**

Run: `node scripts/verify-premium-dashboard.mjs`

Expected: FAIL because the current calendar only lists dated records.

- [ ] **Step 3: Implement calendar, notes, charts, and complete export**

```js
function interviewNotesKey(deliveryId, questionId) {
  return `${String(deliveryId)}:${String(questionId)}`;
}
function calendarMonthDays(year, month) {
  const first = new Date(year, month, 1);
  const cells = Array(first.getDay()).fill(null);
  const count = new Date(year, month + 1, 0).getDate();
  return cells.concat(Array.from({ length: count }, (_, index) => index + 1));
}
```

Make calendar navigation month-based, decorate today and overdue entries, place due-today records at the top, select a delivery before saving interview notes, calculate application/month, interview pass, and Offer rates from all local records, and export company, role, city, status, dates, source, notes, linked draft, and interview notes as UTF-8 CSV compatible with Excel.

- [ ] **Step 4: Run the verifier and delivery Mock smoke check**

Run: `node scripts/verify-premium-dashboard.mjs`

Expected: PASS; month cells, bound-note keys, CSS chart, stats, and complete export fields are present.

- [ ] **Step 5: Commit delivery completion**

```powershell
git add premium-dashboard.html scripts/verify-premium-dashboard.mjs
git commit -m "feat: complete delivery planning dashboard"
```

### Task 7: Complete Assessment Archives and Planning Documents

**Files:**
- Modify: `premium-dashboard.html: assessment render/archive modal and persistence handlers`.
- Test: `scripts/verify-premium-dashboard.mjs`.

**Interfaces:**
- Consumes: `persistExtension`, `maskTextExport`.
- Produces: `compareAssessments(first, second)`, `assessmentPlanningText(result)`, `saveAssessmentQuestion(text)`.

- [ ] **Step 1: Add failing assessment archive assertions**

```js
assert.match(script, /function compareAssessments\b/);
assert.match(script, /function assessmentPlanningText\b/);
assert.match(script, /function saveAssessmentQuestion\b/);
assert.match(script, /data-compare-assessment-a/);
```

- [ ] **Step 2: Run the verifier and confirm selectable comparison fails**

Run: `node scripts/verify-premium-dashboard.mjs`

Expected: FAIL because only the latest two reports are compared.

- [ ] **Step 3: Implement arbitrary comparison and text generation**

```js
function compareAssessments(first, second) {
  return {
    scoreDelta: Number(first.score || 0) - Number(second.score || 0),
    roles: [asArray(first.result?.recommended_roles), asArray(second.result?.recommended_roles)]
  };
}
function assessmentPlanningText(result) {
  return maskTextExport(['score', 'signals', 'strengths', 'roles', '7/30/90 plan'].join('\n'));
}
```

Render two archive selectors, normalize duplicated custom questions, save questions through `persistExtension`, and expose both copy and `.txt` download using the generated plan text.

- [ ] **Step 4: Run the verifier and assessment Mock smoke check**

Run: `node scripts/verify-premium-dashboard.mjs`

Expected: PASS; archive selectors, custom-question persistence, comparison, copy, and download handlers are present.

- [ ] **Step 5: Commit assessment completion**

```powershell
git add premium-dashboard.html scripts/verify-premium-dashboard.mjs
git commit -m "feat: complete assessment archives"
```

### Task 8: Complete Shared Sorting, Theme, Release, and Configuration Surfaces

**Files:**
- Modify: `premium-dashboard.html: CSS, footer, privacy page, shortcut and Tavily controls, initialization`.
- Test: `scripts/verify-premium-dashboard.mjs`.

**Interfaces:**
- Consumes: `attachSortable`, `persistExtension`, `exportAllBusinessData`, `importAllBusinessData`.
- Produces: `validateShortcuts(config)`, `openChangelog()`, `renderReleaseFooter()`, `saveSearchConfiguration()`.

- [ ] **Step 1: Add failing shared-experience assertions**

```js
assert.match(script, /function validateShortcuts\b/);
assert.match(script, /function openChangelog\b/);
assert.match(script, /function renderReleaseFooter\b/);
assert.match(script, /resume-dashboard-search-provider/);
assert.match(script, /data-draft-sort/);
```

- [ ] **Step 2: Run the verifier and confirm version/sort contracts fail**

Run: `node scripts/verify-premium-dashboard.mjs`

Expected: FAIL because draft sort and the release footer/changelog are absent.

- [ ] **Step 3: Implement the minimal shared UI layer**

```js
function validateShortcuts(config) {
  const values = Object.values(config).map(value => String(value || '').toLowerCase()).filter(Boolean);
  return values.length === new Set(values).size ? '' : '快捷键不能重复';
}
function renderReleaseFooter() {
  $('#releaseFooter').innerHTML = `<button class="btn small" id="openChangelogBtn">v${DASHBOARD_VERSION}</button>`;
}
```

Apply drag-sort to drafts and favorites using the evidence helper, add keyboard validation for modifier-compatible one-key bindings, persist Tavily switch/provider/key only locally, add explicit dark-theme tokens for calendar/chart/thumbnail/modal/list states, render a clickable footer version, and provide a static changelog modal covering this release.

- [ ] **Step 4: Run the verifier in both persisted-theme states**

Run: `node scripts/verify-premium-dashboard.mjs`

Expected: PASS; shared sort, configuration, dark-theme selectors, version footer, and changelog handler are present.

- [ ] **Step 5: Commit shared experience completion**

```powershell
git add premium-dashboard.html scripts/verify-premium-dashboard.mjs
git commit -m "feat: finish dashboard release experience"
```

### Task 9: Run Full Regression and Browser Delivery Checks

**Files:**
- Modify: `premium-dashboard.html` only if a failing verification identifies a defect.
- Test: `scripts/verify-premium-dashboard.mjs`, `resume-miniprogram` tests/build, `resume-backend` tests.

**Interfaces:**
- Consumes: all helpers and views from Tasks 1–8.
- Produces: verified single-file Mock and Vite proxy behavior.

- [ ] **Step 1: Run the offline verifier**

Run: `node scripts/verify-premium-dashboard.mjs`

Expected: PASS; syntax, function contract, required controls, local storage keys, Mock fallback, and no forbidden API routes are reported.

- [ ] **Step 2: Run existing frontend regression checks**

Run: `npm.cmd run test:unit` from `resume-miniprogram`

Expected: PASS; all Vitest tests pass.

- [ ] **Step 3: Run H5 build regression**

Run: `npm.cmd run build:h5` from `resume-miniprogram`

Expected: PASS; the build exits successfully.

- [ ] **Step 4: Run backend regression checks**

Run: `.\.venv\Scripts\python.exe -m pytest tests -v` from `resume-backend`

Expected: PASS; all backend tests pass.

- [ ] **Step 5: Perform browser smoke checks**

Run: open `premium-dashboard.html` directly and through the local Vite server; exercise storage-warning/backup, mask, favorite drag-sort, resume template/snapshot, evidence attachment/tag, delivery calendar/note/chart/export, assessment comparison, shortcuts, and changelog.

Expected: no uncaught console exception; direct open uses Mock fallback and Vite continues to call only existing proxy routes.

- [ ] **Step 6: Inspect final diff and commit verified delivery**

Run `git diff --check` and `git status --short`, then stage `premium-dashboard.html`, `scripts/verify-premium-dashboard.mjs`, and `docs/superpowers`; commit with `feat: complete premium dashboard workflows` only after all checks pass.

## Plan Self-Review

- Spec coverage: Tasks 1–2 cover data safety, backup, masking, and identity reset; Task 3 covers jobs; Task 4 covers resume versions/templates; Task 5 covers evidence; Task 6 covers delivery; Task 7 covers assessment; Task 8 covers global release/configuration; Task 9 covers dual-mode verification.
- Placeholder scan: no deferred implementation markers are used; every task has concrete interfaces, commands, and expected results.
- Interface consistency: state mutations pass through `persistExtension`, ordering uses `reorderByIds`, masking uses `maskTextExport`, and final validation uses the same offline verifier introduced in Task 1.
