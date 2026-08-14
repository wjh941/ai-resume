# Premium Dashboard Completion Design

## Scope and Constraints

Complete the missing and incomplete items in `premium-dashboard.html` while preserving its existing visual system, browser double-click Mock mode, Vite `/api` and `/downloads` proxy mode, and existing backend API surface. The product remains a standalone HTML file with no runtime dependency or new backend route.

The completed dashboard must keep existing data usable. All extension data remains local to the browser and is normalized defensively so corrupted or older records cannot abort startup.

## Architecture

The page retains its current `state`, rendering functions, modal system, API wrapper, and Mock fallback. New behavior is organized into pure data helpers followed by thin DOM adapters:

- `extension` persistence stores settings, ordering, favorite roles, attachments, custom categories/tags, snapshots, backup metadata, keyboard bindings, and release state.
- Pure helpers normalize imported data, calculate storage use, create and restore snapshots, mask display-only output, filter jobs, reorder IDs, generate calendar/statistics data, and compare resume or assessment versions.
- Rendering functions only turn normalized data into the existing card, list, table, modal, and tag components. Event bindings call the pure helpers and persist through the existing safe local-storage path.

## Local Data and Privacy

Storage usage is estimated from actual localStorage keys and checked at initialization and after local mutations. Reaching 90% opens a recovery modal with full backup and directed cleanup actions for old drafts and expired deliveries. Scheduled automatic snapshots run no more than once every seven days and retain a bounded, restorable history.

Masking is presentation-only. Resume preview, copied reports, and readable text exports use a shared masking formatter whenever enabled. Full backup files deliberately retain the original data so that a backup can be restored; their download action is explicitly identified as sensitive. Resetting `client_id` requires the same full-backup action before generating a fresh random identifier.

## Job and Resume Workflows

Favorites use stable role identifiers and persistent priority order. The jobs page supplies salary, family, city, and difficulty filters, durable search history, and a data-derived promotion route. Favorites can be compared and used to build a three-tier plan without an API call.

Each successful draft save captures a version snapshot. The resume page can compare and restore versions, exposes a non-operational PDF/Word parser placeholder, and creates three truthful variants from the current resume data. Template settings include font size, margins, and section visibility; named templates save and apply those settings only to local preview behavior.

## Evidence and Delivery Workflows

One reusable native drag-sort adapter persists ordering for drafts, evidence, and favorites. Evidence supports validated local image attachments, custom-category CRUD, custom-tag CRUD, batch tagging, and category/tag filtering. Attachments remain data URLs in local storage and are never sent to the backend.

The delivery console renders a real monthly calendar grid, prioritizes today and overdue follow-ups, and stores role-specific interview notes against a selected delivery ID. Delivery statistics are calculated from records and shown with native CSS charts. The existing CSV export is retained and expanded only if required to contain every saved field.

## Assessment and Global Experience

Assessment archives retain multiple reports. The user chooses any two reports for comparison and can generate a mask-aware long-form planning document for copy or download. Custom prompts remain local and feed the questionnaire on reload.

The release surface adds configurable shortcut validation, deep-theme coverage for every new component, persisted Tavily preferences, a static deployment panel, a footer version, and an in-page changelog modal. No key is transmitted unless the existing user-controlled search flow is explicitly enabled.

## Failure Handling and Verification

Malformed local data resolves to safe defaults. Import validates the top-level shape, snapshots the current state first, and reports a non-blocking error. Image type and size failures are rejected before persistence. Invalid shortcut collisions, impossible sort targets, unavailable clipboard access, storage failures, and unavailable API calls retain the existing toast or Mock fallback behavior.

Verification will cover extracted-script syntax and pure-helper contracts, local state restoration, route/mask/fallback checks, existing frontend unit tests and H5 build, backend tests, and a browser interaction smoke test for direct `file:` mode and Vite proxy mode. The verification command outputs will be recorded before claiming completion.
