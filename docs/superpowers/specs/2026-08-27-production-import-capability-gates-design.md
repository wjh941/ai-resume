# Production Import And Capability Gates

## Goal

Make resume import usable with the dependencies already present, and make all external-service entry points reflect actual backend configuration instead of exposing dead or Demo-only actions.

## Scope

This iteration covers:

- PDF text extraction through `pypdf`.
- DOC/DOCX text extraction through `python-docx` and a zip/XML fallback for legacy `.docx` files.
- Deterministic, conservative mapping of common resume labels into the existing `ResumePayload` shape.
- Explicit import statuses (`parsed`, `parse_failed`) and safe preview behavior.
- Public capability metadata for SMS, WeChat OAuth, payment, push delivery, job-source matching, and resume import.
- Frontend capability loading that hides or disables unavailable actions with Chinese explanations.
- Regression tests for parser output, malformed files, capability responses, and UI service mapping.

This iteration does not implement provider-specific OAuth, SMS, payment, push, or job-source protocols. Those require real credentials, callback domains, signatures, and provider contracts.

## Design

### Import pipeline

`ResumeImportService.accept_upload` validates extension, MIME type, size, and file signature where applicable, writes the file inside the configured import directory, and calls a parser selected by suffix. The parser returns extracted text and a normalized `ResumePayload`.

Parsing is intentionally conservative: it recognizes labeled lines such as name, phone, email, city, target role, and section headings; unrecognized text is retained in a self-evaluation/notes field rather than guessed into structured data. A file with no meaningful text becomes `parse_failed` and cannot be applied by the editor. Stored files and database rows continue to use the existing TTL cleanup worker.

### Capability contract

The public `/health` response adds a `features` object. Each feature has `enabled`, `mode` (`real`, `demo`, or `disabled`), and a short Chinese `notice`. The server computes these values from settings and never exposes secrets. Existing health fields remain backward compatible.

The frontend adds one small capability client that reads `/health` and exposes typed feature flags. Pages use it only to gate actions; normal authenticated business requests remain unchanged. A failed capability request defaults to disabled for external actions and does not block resume editing or assessment.

### Error handling

Malformed or unsupported documents return a user-safe validation error, remove the temporary file, and leave the current draft unchanged. Provider-disabled actions show a local explanation and do not create an order, enqueue a notification, or redirect to a dead callback.

### Testing

- Unit tests cover parser extraction and malformed input.
- API tests cover import status transitions and public capability flags in development and production settings.
- Frontend tests cover capability response mapping and disabled-action fallback.
- Full backend pytest, frontend Vitest, TypeScript, H5 build, and Dashboard contract checks remain release gates.

## Non-goals

- No provider SDKs or new runtime dependencies.
- No automatic OCR or AI guessing for scanned PDFs.
- No changes to existing route names or authenticated payloads except the import status/preview contract.
