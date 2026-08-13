# Premium Dashboard Expansion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend `premium-dashboard.html` with local-first data safety, job planning, resume versioning, evidence organization, delivery analytics, assessment archives, and configurable desktop interactions without adding backend APIs or external dependencies.

**Architecture:** Keep the existing single HTML document, `state` object, `render*` functions, modal/toast system, API wrapper, and Mock fallback. Add one namespaced `extension` state object persisted through the existing local-storage helpers, pure data utilities that do not touch the DOM, and small render/event adapters for each existing page. New UI uses the current CSS variables and component classes, with a small number of shared classes for calendar, sortable rows, attachment thumbnails, and snapshot cards.

**Tech Stack:** Inline CSS, native HTML, vanilla JavaScript, localStorage, FileReader, Blob/download APIs, native drag-and-drop, existing `/api` and `/downloads` routes only.

## Global Constraints

- Keep `premium-dashboard.html` as the only product file and keep it directly openable with `file:` Mock fallback.
- Keep `const API_BASE_URL = "";` and the current Vite proxy behavior unchanged.
- Add no backend interfaces, no recruiter-site scrapers, no external CDN or runtime dependency.
- Preserve existing CSV/export, draft, evidence, delivery, assessment, API, and Mock workflows.
- Store extension-only data locally; use graceful defaults for old localStorage records.
- Keep pure data utilities independent from `document` so they are portable to UniApp.
- Do not automatically merge, rebase, push, or create a PR.

### Task 1: Local Data Safety and Privacy

**Files:**
- Modify: `premium-dashboard.html` state, local persistence, privacy page, modal/event wiring.
- Test: temporary Node contract script extracting the inline script.

- [ ] Add `extension` defaults for storage usage, masked preview, snapshots, backup history, and client reset metadata.
- [ ] Implement `safeJsonParse`, `storageUsage`, `checkStorageCapacity`, `maskSensitiveText`, `createSnapshot`, `restoreSnapshot`, and `exportFullBackup` as pure helpers.
- [ ] Warn at 90% of the browser quota and offer backup/cleanup actions.
- [ ] Add seven-day automatic snapshot creation and a rollback list, retaining a bounded history.
- [ ] Make all privacy-sensitive display/copy/export text pass through the mask toggle.
- [ ] Require a full backup before client ID reset and generate a fresh random ID.

### Task 2: Job Favorites and Discovery

**Files:**
- Modify: `premium-dashboard.html` jobs page, navigation, job render/search handlers, local persistence.

- [ ] Add a 收藏岗位 page backed by durable local IDs and favorite toggles on every job card.
- [ ] Add salary, industry, city, and difficulty filters with pure `filterJobs` logic and page reset.
- [ ] Save recent search terms, render a clearable search-history panel under the search input, and retain it across refresh.
- [ ] Add a promotion-route card showing upstream/downstream roles and selectable three-tier planning from favorites.
- [ ] Keep the existing formal search/API/mock flow and normalize all new fields with safe fallbacks.

### Task 3: Resume Versions and Templates

**Files:**
- Modify: `premium-dashboard.html` resume page, save/export handlers, local persistence.

- [ ] Create a local snapshot on every successful draft save; render restore and side-by-side comparison controls.
- [ ] Add external parser placeholder with the exact disabled wording and no fake API call.
- [ ] Add local template settings for font size, margins, and section visibility; apply them to preview and save them by template name.
- [ ] Add batch generation for internship, graduate, and experienced-hire variants using existing truthful evidence only.
- [ ] Preserve readiness validation and Word/PDF backend/mock export buttons.

### Task 4: Evidence Ordering, Attachments, and Categories

**Files:**
- Modify: `premium-dashboard.html` evidence page, evidence editor/import/export logic.

- [ ] Add custom category storage and CRUD controls; include category in filtering and evidence cards.
- [ ] Add native drag/drop ordering, persist order immediately, and keep selected IDs stable.
- [ ] Add image attachment FileReader preview stored locally as data URLs with size/type validation.
- [ ] Keep batch import/export and `[待确认]` semantics unchanged.

### Task 5: Delivery Calendar, Interview Bank, and Metrics

**Files:**
- Modify: `premium-dashboard.html` delivery page, local persistence, export controls.

- [ ] Render a month calendar with today and expired follow-ups highlighted; list due items first.
- [ ] Add role-aware Mock interview questions and notes bound to delivery record IDs.
- [ ] Compute monthly applications, interview pass rate, and offer ratio in pure helpers, then render compact charts.
- [ ] Ensure the existing complete delivery backup export contains every field and remains usable offline.

### Task 6: Assessment Archives and Planning Document

**Files:**
- Modify: `premium-dashboard.html` assessment page and local persistence.

- [ ] Add permanent assessment archive normalization, two-report comparison, and restore viewing.
- [ ] Add long-form planning document generation and copy/download actions.
- [ ] Add locally saved custom assessment questions and include them in the questionnaire.

### Task 7: Global Interaction and Release Surface

**Files:**
- Modify: `premium-dashboard.html` shared CSS, privacy page, event delegation, initialization.

- [ ] Add native drag-sort support for drafts, evidence, and favorites through one reusable helper.
- [ ] Add a keyboard shortcut configuration panel with defaults, validation, persistence, and conflict warnings.
- [ ] Complete dark-theme rules for new cards, tables, charts, modals, thumbnails, and calendar states.
- [ ] Add all-data import/export, static deployment extension information, version number, and changelog modal.
- [ ] Add `beforeunload` protection for pending local edits where browser behavior permits.

### Task 8: Verification and Local Delivery

**Files:**
- Modify: `premium-dashboard.html` only after tests identify a defect.
- Test: extracted-script syntax/contract checks, `npm.cmd run test:unit`, `npm.cmd run build:h5`, backend pytest.

- [ ] Run Node syntax check and contract assertions for storage, mask, filters, snapshots, favorites, date/calendar, shortcut, and fallback paths.
- [ ] Run the complete frontend unit suite and H5 build.
- [ ] Run the complete backend suite to confirm no API regression.
- [ ] Run `git diff --check`, inspect `git status --short`, and make one local commit only; do not push or create a PR.

## Verification Checklist

- Every listed feature has an explicit task and a local persistence key.
- No new backend endpoint or external dependency appears in the plan.
- Existing API/mock functions remain the source of truth for server-backed flows.
- All new UI is optional and failure-tolerant; local data corruption cannot abort initialization.
