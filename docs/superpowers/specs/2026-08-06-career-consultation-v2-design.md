# Career Consultation V2 Design

## Goal

Upgrade the AI resume demo into a structured career-consultation assistant for
interns, graduates, employed candidates, candidates with employment gaps, and
career changers. Preserve existing draft, template, Word/PDF export, and job
intelligence APIs.

## Runtime 404 Resolution

The identity selection UI calls `POST /api/consultation/job-analysis`. The
existing H5 and FastAPI processes were started before that route was added and
did not use reload mode. The runtime fix is to restart the 8000 FastAPI service
and the 5173 H5 service. The endpoint must be verified through the H5 proxy.

## Consultation Session

- `identityCode` is locally persisted and remains selected across app restarts.
- The first role lookup with no saved identity shows only the exact five-option
  identity prompt.
- A new role lookup with a saved identity automatically uses that identity and
  requests job analysis. A visible action allows the user to switch identity.
- Resume paste, PDF text extraction, and standalone advice reuse the saved
  identity and selected role.

## Backend APIs

Existing APIs stay compatible. Extend the consultation namespace:

- `POST /api/consultation/job-analysis`
  - Returns nine ordered job-analysis sections, a detailed identity plan,
    follow-up question, and market data notice.
- `POST /api/consultation/resume-review`
  - Returns issues, rewrite examples, keywords, a copyable safe full-resume
    draft, and a one-minute introduction. It does not return job analysis.
- `POST /api/consultation/advice`
  - Returns structured guidance for interview practice, salary negotiation,
    contract pitfalls, career planning, certificates, job comparison, written
    tests, recruitment channels, and scam screening.
- `POST /api/consultation/resume-pdf-extract`
  - Accepts a PDF, extracts text with `pypdf`, and returns it for explicit
    user review before calling the resume-review endpoint.

## Content Safety and Market Data

- No candidate fact may be fabricated: employers, schools, dates, certificates,
  project identity, or numeric results remain user-supplied or `[待确认]`.
- The mock provider marks output as local market estimates, not real-time
  market data.
- OpenAI-compatible providers receive strict JSON prompts that require
  objective language, risk disclosure, and real-time source attribution only
  when their configured model has web retrieval capability.

## Frontend

The job search page remains the entry page and adds three compact panels:

1. Role consultation with identity selection and nine sections.
2. Resume review with paste and PDF upload/extraction.
3. Career toolkit with a topic picker, optional question input, and structured
   results.

The result panels use short headings and bullet-style content suitable for
mobile reading.

## Test Coverage

- Identity persistence and automatic reuse for a new role.
- Nine fixed job-analysis sections and all five detailed identity-plan profiles.
- Resume-review output includes a safe full-resume draft and introduction.
- Advice topic validation and output.
- PDF text extraction success and invalid file validation.
- H5 proxy regression check for the identity selection endpoint.
