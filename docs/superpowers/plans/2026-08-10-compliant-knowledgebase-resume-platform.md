# Compliant Knowledgebase Resume Platform Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add compliant local knowledgebase management, richer resume controls, configurable AI profiles, and deployable environment configuration without any recruitment-site scraping.

**Architecture:** FastAPI owns Excel/TXT validation, SQLite persistence, import audit logs, resume versions and safe provider profiles. Uni-App consumes explicit management APIs and selects non-secret settings. SQL baseline scripts make the schema portable to MySQL and PostgreSQL.

**Tech Stack:** FastAPI, SQLite, `openpyxl`, Python standard library, Uni-App Vue 3, Pinia, Vitest, pytest.

## Global Constraints

- Never add recruitment-site crawling, HTTP scraping, browser automation, login bypasses, cookie handling or batch JD collection.
- Only import local `.xlsx` and `.txt` files supplied by the operator.
- Provider API keys remain server environment variables and are never persisted or returned.
- Preserve existing CSV, drafts, job query, export and career planner contracts.

### Task 1: Knowledgebase schemas, repository and Excel/TXT service

**Files:** create `app/schemas/knowledgebase.py`, `app/repositories/knowledgebase.py`, `app/services/knowledgebase_excel.py`, `app/services/official_text_parser.py`; modify `db.py`, `requirements.txt`; test `tests/test_knowledgebase_api.py`.

- [ ] Add failing tests for template generation, invalid Excel preview, valid commit and offline TXT parsing.
- [ ] Add `knowledge_import_log` schema and repositories for roles/majors with pagination and audit logging.
- [ ] Implement `openpyxl` workbook template, preview validation and transactional commit.
- [ ] Implement local-file-only text parser and CLI command accepting a local path.
- [ ] Run focused tests and commit `feat: add compliant knowledgebase import services`.

### Task 2: Knowledgebase API and admin UI

**Files:** create `app/api/knowledgebase.py`, `pages/knowledgebase/index.vue`, `types/knowledgebase.ts`, `services/knowledgebase-api.ts`; modify `main.py`, `pages.json`, job-search entry; test backend and frontend mapper.

- [ ] Add failing API tests for CRUD, export, template and import endpoints.
- [ ] Register routes and error handlers without exposing filesystem paths in responses.
- [ ] Implement paginated role/major cards, manual create/edit/delete, template download and import preview/confirm UI.
- [ ] Build H5 and MP-Weixin; commit `feat: add knowledgebase management UI`.

### Task 3: Resume risk, versions and Markdown export

**Files:** create `services/resume_risk.py`, `services/export_markdown.py`, `repositories/resume_versions.py`; modify draft schemas/repository/API, export API, db; test `test_resume_risk.py`, `test_resume_versions_api.py`, `test_exports_api.py`.

- [ ] Add failing deterministic risk and version restore tests.
- [ ] Add `resume_version` snapshots on save and explicit named snapshots.
- [ ] Add list, restore and simple field-level comparison APIs.
- [ ] Add Markdown export through the existing temporary download service.
- [ ] Run focused tests and commit `feat: add resume risks versions and markdown export`.

### Task 4: Matching quality and AI provider profiles

**Files:** create `schemas/ai_profiles.py`, `repositories/ai_profiles.py`, `api/ai_profiles.py`; modify career recommender, configuration, AI client and main; test profile switching and no-secret responses.

- [ ] Add `ai_provider_profile` persistence for non-secret settings and seed mock/OpenAI-compatible profiles.
- [ ] Add environment-variable key resolution and profile selection per request/application configuration.
- [ ] Add score reasons for skills, courses and verified local source; keep neutral market score without authorized source.
- [ ] Add deterministic risk input to AI rewrite prompts; reject responses that change immutable resume facts as before.
- [ ] Run tests and commit `feat: add provider profiles and resume matching safeguards`.

### Task 5: Configuration UI, environment files and database scripts

**Files:** create `pages/settings/index.vue`, `types/settings.ts`, `services/settings-api.ts`, `src/config/runtime.ts`, `.env.example`, `.env.development`, `docs/database/*.sql`; modify `http.ts`, pages and README.

- [ ] Add test covering environment API base selection.
- [ ] Implement settings UI showing profile/model/Base URL and key environment variable name, without a key input.
- [ ] Replace hard-coded API address with environment-driven runtime config.
- [ ] Add complete SQLite-aligned MySQL/PostgreSQL baseline scripts with indexes and JSON storage mappings.
- [ ] Build both front-end targets and commit `feat: add deploy configuration and database migrations`.

### Task 6: Documentation and full verification

**Files:** modify `README.md`; create `docs/compliant-knowledgebase-operations.md`, `docs/deployment.md`.

- [ ] Document Excel columns, source labels, local TXT format, preview/commit workflow and prohibited scraping behaviors.
- [ ] Document backend/H5/MP deployment and MySQL/PostgreSQL migration procedure.
- [ ] Run `pytest tests -v`, `npm run test:unit`, `npm run build:h5`, `npm run build:mp-weixin`.
- [ ] Commit `docs: document compliant knowledgebase operations` and push the branch.
