# Account Privacy Lifecycle

Phase 6 introduces a visible privacy lifecycle without performing irreversible
account actions. It is intended for local development and product review.

## Data scope

The Account page lists the personal-data categories currently used by the
application:

- account profile and mock phone-login identity;
- resume drafts, generated content, and export history;
- career-plan inputs and reports;
- job favourites and matching-alert preference;
- membership and demo-order records.

## Available actions

- **Request data export** calls `POST /api/account/data-export` and returns a
  `not_started` acknowledgement.
- **Request account deletion** calls `POST /api/account/deletion-request` and
  returns a `requested` acknowledgement after an explicit confirmation.

Neither action removes records or creates a downloadable archive in this
phase. This keeps existing database data recoverable while the privacy
workflow is reviewed.

## Follow-up requirements

Before enabling real deletion or exports, implement verified-identity checks,
auditable request tracking, an export-job store with expiring download links,
retention rules, and a recoverable deletion window. The implementation must
also be reviewed against the product's applicable privacy and retention
obligations.
