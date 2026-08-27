# Production Import And Capability Gates Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Ship real text extraction for resume uploads and configuration-driven capability gates for external services.

**Architecture:** Add a small backend parser module that returns the existing resume payload, keep import persistence in the current repository/service, and extend the public health contract with non-sensitive feature flags. The frontend consumes those flags through one typed service and leaves core editing available when optional capabilities are unavailable.

**Tech Stack:** FastAPI, pypdf, python-docx, Pydantic, Vue 3, Vitest, pytest.

## Global Constraints

- Do not add dependencies; `pypdf` and `python-docx` are already required.
- Preserve existing routes and authenticated payloads except the documented import status/preview behavior.
- Write and run a failing regression test before production-code changes.
- Do not expose provider credentials or raw parser exceptions to clients.
- Keep user-visible text in Simplified Chinese.

---

### Task 1: Implement conservative PDF/DOCX text extraction

**Files:**
- Create: `resume-backend/app/services/resume_parser.py`
- Modify: `resume-backend/app/services/resume_imports.py`
- Test: `resume-backend/tests/test_resume_parser.py`

**Interfaces:**
- Produces `parse_resume_file(path: Path, suffix: str) -> ParsedResume` with `text` and `resume` fields.
- `ParsedResume.resume` is the existing normalized resume dictionary.

- [ ] Add tests for labeled plain text extraction, PDF extraction, DOCX extraction, and malformed/empty files.
- [ ] Run the focused pytest file and confirm the parser import or assertions fail.
- [ ] Implement suffix dispatch using `pypdf` and `python-docx`, conservative label parsing, and a meaningful-content check.
- [ ] Run the focused tests and the existing resume import tests.

### Task 2: Make import statuses and editor behavior explicit

**Files:**
- Modify: `resume-backend/app/repositories/resume_imports.py`, `app/services/resume_imports.py`, `app/api/drafts.py`
- Modify: `resume-miniprogram/src/services/resume-import-api.ts`, `src/pages/resume-editor/index.vue`
- Test: `resume-backend/tests/test_phase10_resume_imports.py`, `resume-miniprogram/src/tests/phase10-services.spec.ts`

Return `parsed` only when meaningful content exists; return a safe `parse_failed` response for malformed/empty files, preserve TTL cleanup, and ensure the editor leaves the existing draft untouched. Keep file validation and cleanup behavior unchanged.

### Task 3: Add public capability metadata

**Files:**
- Modify: `resume-backend/app/api/system.py`, `resume-backend/main.py`
- Create: `resume-miniprogram/src/services/capability-api.ts`
- Test: `resume-backend/tests/test_capabilities_api.py`, `resume-miniprogram/src/tests/capability-api.spec.ts`

Add non-sensitive `features` to the public `/health` response. Each feature returns `enabled`, `mode`, and a Chinese `notice` for resume import, SMS, WeChat OAuth, payment, push, and job matching. Frontend mapping must default optional features to disabled when the health request fails.

### Task 4: Gate external-service UI actions

**Files:**
- Modify: `resume-miniprogram/src/pages/login/index.vue`, `src/pages/membership/index.vue`, `src/pages/job-collection/index.vue`
- Test: focused frontend service/page source contracts where existing suites support them.

Load capabilities without blocking the page. Hide or disable phone login, WeChat login, demo payment, and job-alert switches when the corresponding feature is unavailable, while showing a concise Chinese notice. Resume editing and career assessment remain usable.

### Task 5: Verify release gates

Run backend pytest, frontend Vitest, frontend typecheck, H5 build, Dashboard contract checks, and `git diff --check`. Review the diff for secrets, raw parser errors, accidental route changes, and English user-facing strings.
