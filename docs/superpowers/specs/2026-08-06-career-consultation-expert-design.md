# Career Consultation Expert Design

## Goal

Add a staged career consultation experience to the Uni-App resume demo. The
existing job intelligence, resume draft, template, CSV-like data exchange, and
export flows remain available and unchanged.

## User Flow

1. A user enters a role and starts a consultation.
2. The UI shows only the identity prompt and five numbered identity choices.
   It does not request or display job analysis at this stage.
3. Selecting an identity persists the choice in local storage and calls the
   consultation API.
4. The result contains the fixed eight-part job analysis and a plan tailored
   to the selected identity.
5. A user who pastes resume text after selecting an identity receives only
   resume issues, rewrite examples, and keywords. It does not re-render job
   analysis in the resume review result.
6. The existing "generate resume for this role" action remains available after
   job analysis. It still uses the existing resume draft and template flow.

## Backend Contract

New endpoints are isolated from existing endpoints:

- `POST /api/consultation/job-analysis`
  - Input: `role_name`, `identity_code`
  - Output: `job_intelligence`, eight analysis sections, identity plan,
    identity label, and follow-up question.
- `POST /api/consultation/resume-review`
  - Input: `resume_text`, `identity_code`, optional `role_name`
  - Output: identity label, issue annotations, rewrite examples, and keywords.

The existing `POST /api/job/query` and `POST /api/resume/ai-rewrite` contracts
remain unchanged.

## AI Behavior

The mock provider produces deterministic, role-aware Chinese content for local
development. The OpenAI-compatible provider receives a strict JSON prompt that
requires the same structure and does not allow fabricated candidate facts.

Resume review must label any unknown metrics, experience facts, and achievements
as suggestions or placeholders. It must not present invented employer, school,
date, certificate, project identity, or metric information as fact.

## Frontend State

A dedicated Pinia store persists:

- pending role name
- identity code
- identity label

The first role lookup transitions to `identity-selection`. Selecting an
identity transitions to `job-analysis`. Resume review is an independent display
state after an identity has been recorded.

## Validation

- Identity code only accepts `1` through `5`.
- Role name and resume text are trimmed and must be non-empty.
- Job analysis always contains eight sections in its fixed order.
- Job analysis and resume review use distinct response shapes.

## Test Coverage

- Backend endpoint validation and response structure.
- Eight job analysis sections and identity-specific plan content.
- Resume review response separation from job analysis.
- Frontend identity persistence and flow transitions.
- Full backend tests, frontend unit tests, H5 build, and WeChat Mini Program
  build before push.
