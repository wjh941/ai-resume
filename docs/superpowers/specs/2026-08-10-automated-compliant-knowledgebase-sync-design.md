# Automated Compliant Knowledgebase Sync Design

## Objective

Extend the local knowledgebase with two auditable expansion modes while preserving all
existing career, resume, CSV, draft and export behavior.

1. Official static synchronization downloads only pre-approved direct static artifacts
   from government-owned hosts and parses only CSV, JSON, or ZIP archives containing CSV
   or JSON.
2. Tavily-assisted discovery uses the Tavily API response only. It never fetches a result
   page itself and accepts only approved government, occupational-standard, and industry
   white-paper domains.

The application must not include recruitment-site crawling, HTML scraping, browser
automation, cookie handling, login bypasses, or bulk job-description collection.

## Source Registry

`official_dataset_source` stores one row per approved source:

- `source_key`, `display_name`, `direct_url`, `allowed_hosts`
- `format` (`csv`, `json`, `zip`)
- `version_strategy` (`etag_last_modified`, `sha256`, `content_version`)
- `parser_kind` (`occupation`, `major`, `employment`)
- `enabled`, `last_version`, `last_checksum`, `last_synced_at`

The registry only accepts HTTPS direct-file URLs. It rejects HTML, PDF, redirects to a
non-allowlisted host, oversize files, and unsupported archive members. A source with no
verified machine-readable direct download is not enabled and is reported as skipped rather
than guessed or scraped.

## Import Data Flow

1. The frontend starts `POST /api/knowledgebase/sync/official`.
2. The backend downloads to a managed cache directory, validates MIME/extension/size and
   computes a checksum.
3. Version metadata and checksum determine whether the source changed.
4. CSV/JSON records are normalized into role or major candidates.
5. Candidates are validated, deduplicated and inserted transactionally as system-standard
   records. Existing user-custom records are never overwritten or deleted.
6. The backend saves detailed source and run audit logs, including skipped and failed
   sources. The API returns aggregate counts and safe status messages, never local paths.

The existing optional Excel import/export remains an administrator tool. It is not required
for the automatic initialization workflow.

## Tavily-Assisted Discovery

The dynamic mode is disabled by default and requires `TAVILY_API_KEY`.

- Queries use role-family and technology seed terms from the local catalog.
- Results must pass an explicit domain allowlist. Recruitment platforms, aggregators and
  domains matching blocked patterns are rejected before parsing.
- Only Tavily-provided snippets/content are processed; the application does not make
  follow-up HTTP requests to result pages.
- AI creates structured candidates with source URLs, confidence and a `dynamic_discovery`
  provenance label.
- A candidate can enrich missing information on an existing system record, but never
  overwrites user-custom records. Conflicts are logged and skipped.
- Scheduled sync is configurable, disabled by default and protected by a process-local
  lock. Manual refresh uses the same service.

## Data Model

Add:

- `official_dataset_source`
- `knowledge_sync_run`
- `knowledge_sync_item`

Extend role and major catalog records with non-breaking provenance fields:

- `catalog_origin`: `seed`, `official_dataset`, `dynamic_discovery`, `manual`, `excel`
- `source_key`
- `source_version`
- `source_url`
- `updated_at`

Legacy seed data receives `catalog_origin=seed`. User-created data receives
`catalog_origin=manual`; all synchronization writes refuse to overwrite it.

## APIs And UI

Backend endpoints:

- `GET /api/knowledgebase/sources`
- `POST /api/knowledgebase/sync/official`
- `POST /api/knowledgebase/sync/dynamic`
- `GET /api/knowledgebase/sync/runs`
- `PATCH /api/knowledgebase/sources/{source_key}`

The existing knowledgebase CRUD and optional Excel endpoints remain available.

The knowledgebase page adds:

- `一键初始化完整岗位库`
- status cards for enabled / skipped / failed sources
- a dynamic mode switch, manual refresh action and source policy explanation
- import run history and count summaries

No API key is sent to the frontend. The settings screen exposes provider status and the
environment variable name only.

## Testing And Operations

Tests use local fixture files and a mocked HTTP transport. They prove:

- unsupported URLs and HTML/PDF are rejected
- CSV, JSON and ZIP import paths are parsed correctly
- unchanged checksums are skipped
- duplicates are ignored
- manual records are preserved
- blocked Tavily domains never produce records
- API responses expose audit summaries but no local cache paths

Documentation describes source registration, approved file formats, Tavily allowlisting,
environment variables, update scheduling, and the explicit prohibition on web scraping.

