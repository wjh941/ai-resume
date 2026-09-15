# Phase4 Changelog

## Reliability and Safety

- Added standardized API error handling for validation, database, export, and unexpected failures with concise server logging.
- Hardened authenticated export and download handling with identifier validation and storage-bound path checks.
- Prevented empty resume exports from producing downloadable blank/corrupt files.
- Added a detailed health endpoint for database connectivity and export storage readiness.

## Frontend Experience

- Aligned the career-planning and export pages with the existing SaaS dashboard's spacing, card, hover, and responsive layout system.
- Added smoother three-tier career planning and role-comparison state transitions without changing recommendation data or business actions.
- Added reusable notification and export-progress feedback for the touched flows.
- Moved H5 development serving to `http://127.0.0.1:5186`.

## Operations

- Added a production database migration checklist that requires a verified backup before any change is applied.
- Preserved existing API response success shapes and SQLite business table structure; Phase4 changes are non-destructive.

## Verification

- Backend: pytest suite, including export, health, validation, and authorization coverage.
- Frontend: Vitest unit suite and H5 production build.
- Smoke flow: authenticated resume draft creation, career-plan request, export request, and unauthenticated permission interception.
