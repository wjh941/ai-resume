# Automated Compliant Knowledgebase Sync Implementation Plan

## Goal

Implement audited official static-dataset synchronization and a domain-restricted Tavily
discovery mode without adding website crawling or changing current resume workflows.

## Task 1: Foundation And Official Sync Service

**Files:** create catalog sync schemas, repository and service modules; modify database
initialization, configuration and tests.

1. Add failing tests for source validation, unchanged-version skip, CSV/JSON/ZIP parsing,
   duplicate handling and manual-record preservation.
2. Add source/run/item tables and provenance columns with SQLite migrations.
3. Implement an HTTPS direct-file registry, bounded download client, version comparison,
   cache storage and transactional import pipeline.
4. Seed only verified direct machine-readable sources. Keep unavailable sources disabled
   with an explicit reason rather than using publication pages or guessed URLs.
5. Run focused backend tests and commit.

## Task 2: Dynamic Discovery And APIs

**Files:** create sync API/router and Tavily discovery service; modify application setup and
configuration; add API tests.

1. Add failing tests proving blocked domains, disabled keys and manual records are safe.
2. Implement domain allowlist/blocklist filtering over Tavily API response data only.
3. Normalize dynamic candidates, retain source evidence and use non-overwriting upserts.
4. Add manual official sync, dynamic refresh, source status and audit-log endpoints.
5. Run focused backend tests and commit.

## Task 3: Knowledgebase And Settings UI

**Files:** knowledgebase page, settings page, service/types, page registration and frontend
tests.

1. Add failing frontend tests for run-status mapping and disabled dynamic controls.
2. Add one-click official initialization, sync history, source status, dynamic toggle and
   manual refresh UI.
3. Preserve optional Excel management and manual role/major CRUD.
4. Drive all API addresses through environment-based runtime configuration.
5. Build H5 and MP-Weixin and commit.

## Task 4: Resume, Provider And Migration Enhancements

**Files:** resume risk/version/Markdown modules, provider profile modules, SQL migration
scripts and associated tests.

1. Use expanded catalog provenance in matching explanations without introducing market
   claims.
2. Add deterministic risk checks, version snapshots and Markdown export.
3. Add non-secret model provider profile switching, with secrets resolved only from
   environment variables.
4. Add MySQL and PostgreSQL schema baseline/migration scripts.
5. Run focused backend tests and commit.

## Task 5: Documentation And Full Verification

**Files:** README and operational/deployment documents.

1. Document the static source policy, disabled-source workflow and no-scraping boundary.
2. Document Tavily setup, allowlists, scheduling and data provenance.
3. Run backend tests, frontend unit tests, H5 build and MP-Weixin build.
4. Commit all documentation and push `feature/ai-resume-demo` without merge or PR.

