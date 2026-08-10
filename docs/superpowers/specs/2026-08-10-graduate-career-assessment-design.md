# Graduate Career Assessment Design

## Goal

Add a human-centered graduate career assessment feature that combines annual public
employment intelligence, occupational interests, evidence-based strengths and real-world
constraints. The product gives actionable career directions and does not diagnose mental
health, promise employment outcomes or invent a user's experience.

## Compliance Boundary

- Do not implement recruitment-site crawlers, HTML scraping, browser automation, login
  bypasses, cookie handling, batch job-description collection or hidden APIs.
- Annual intelligence is created only from local static official reports/data supplied by
  the operator, the existing approved static-data synchronizer, or operator-authored
  summaries with source and publication date.
- Each annual fact stores its source label, publication date, region scope and confidence
  note. The interface labels it as decision support, not a job-market guarantee.

## Assessment Model

The assessment is a career-preference tool, not a clinical or psychological diagnostic.

1. `interest`: 30 short RIASEC-style work-preference questions. Each answer is scored into
   realistic, investigative, artistic, social, enterprising and conventional interests.
2. `work_style`: 24 work-style questions for structured problem solving, communication,
   collaboration, resilience, learning rhythm and ownership.
3. `strength_evidence`: 20 questions about verified courses, projects, tools, portfolios,
   internships and accomplishments. Unknown content is never treated as evidence.
4. `constraints`: city, salary floor, work type, industry preferences, availability and
   tolerance for travel/overtime.

Each answer uses a five-point agreement scale. Scores provide explainable directional
signals rather than a single personality label.

## Recommendation Model

The recommender combines:

- existing major, skills and role-profile compatibility
- assessment interest and work-style fit
- verified strength evidence
- user constraints
- optional annual public-employment intelligence, weighted only when its scope matches
  the user's graduation year/region/industry

It returns three non-overlapping tiers:

- `冲刺`: good long-term direction with explicit gaps
- `稳妥`: evidence and preferences align well
- `保底`: accessible related direction with transparent trade-offs

Every recommendation includes `why_this_fits`, `why_not_priority`, missing skills,
evidence to build, and a confidence note.

## Actionable Advice

The result contains:

- a supportive plain-language summary that acknowledges strengths and constraints
- 7-day actions: one resume/portfolio correction and one targeted practice
- 30-day actions: a scoped project, targeted applications and mock interview preparation
- 90-day actions: skill evidence, project delivery and progress review milestones
- role-specific resume edits, application channels and interview question practice
- risk flags: unsupported salary expectation, missing evidence, excessive direction spread,
  or a conflict between stated constraints and target roles

Actions specify a tangible outcome, not generic advice such as "improve yourself".

## Data Model And APIs

Add SQLite tables:

- `annual_employment_insight`: year, scope, audience, category, title, content, source
  label, publication date, confidence note and created time.
- `career_assessment`: client ID, assessment version, answers JSON, result JSON and
  updated time.

Add APIs:

- `GET /api/career/assessment/questions`
- `POST /api/career/assessment/submit`
- `GET /api/career/assessment?client_id=...`
- `GET /api/career/annual-insights`
- `POST /api/career/annual-insights` for local operator-created/approved summaries only

The existing career profile and recommendation endpoints remain compatible. A new
`assessment` property is optional in recommendation payloads.

## Frontend

Add a `职业测评` page with four small paged sections, visible progress, optional skip
explanations and no scary or deterministic wording. Add a result view with a fit map,
three career tiers, reasons, risks and 7/30/90-day plan. Add an annual-insight card in
the existing career planner, preserving the current planner workflow.

## Testing

- deterministic tests for category scoring, answer validation and tier reasons
- tests proving empty or unverified answers do not become strengths
- API tests for save/load assessment and annual insight provenance
- frontend tests for answer mapping and action-plan rendering
- full backend tests, frontend unit tests, H5 build and MP-Weixin build before push

