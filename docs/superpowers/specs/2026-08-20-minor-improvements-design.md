# Minor Improvements Design

## Goal

Polish the existing H5 interface, enrich local mock job listings, improve
print-oriented PDF layout, and provide a first-login onboarding tour without
changing existing business workflows, database schema, or established APIs.

## Constraints

- All new visible UI copy is Simplified Chinese except technical proper nouns.
- Existing API request and response contracts remain compatible. An additive
  mock-listing field is permitted only in the local job-match response.
- No real SMS, payment, external job source, or database-backed onboarding
  state is introduced.
- The onboarding completion state is frontend-only and scoped by user ID.
- PDF export routes, formats, and renderer selection remain unchanged.

## UI Refinement

The incumbent blue-gray operating interface remains intact. `App.vue` keeps a
small shared set of spacing, radius, shadow, and transition tokens. The login,
account, job-search, and new onboarding surfaces use those tokens rather than
introducing a second visual system.

Buttons receive short hover, press, disabled, and focus transitions. The
existing login mode tabs use an explicit active-state transition. Job suggestion
rows and the onboarding panel use a single enter/leave transition; media queries
disable nonessential motion when the user requests reduced motion. Cards retain
a restrained radius and a single soft elevation treatment, keeping the layout
dense enough for repeated operational use.

## First-Login Onboarding

A reusable `OnboardingTour` component presents three steps:

1. 完善简历
2. 生成职业规划
3. 管理投递

The component provides previous, next, skip, complete, and current-workflow
navigation actions. Login always lands on the job-search page, so that page
checks a frontend `uni` storage key shaped as
`resume_demo_onboarding_v1:{userId}` after authentication. A missing key opens
the tour once. Completion and skip both persist the flag, preventing later
automatic popups. The Account page adds `重新查看新手引导`, which opens the same
component without clearing the saved flag.

No user table field, migration, backend endpoint, or API request is necessary.
The key is deliberately per user and per device; clearing local application data
can cause the tour to appear again on that device.

## Local Mock Job Listings

A focused static dataset adds representative entries for software development,
data science, administration, and finance. Each entry contains a clearly local
mock company name, city, salary range, responsibilities, requirements, and a
match-score reference. `JobMatcher` consults this dataset for matching role
names and retains its existing calculated score for candidate-specific ranking.

The existing job-match response gains an additive `responsibilities` array. For
roles without a sample, the matcher derives a concise local placeholder from the
catalog so all returned items remain renderable. The frontend displays the
sample content as local reference material and does not claim live vacancies.

## PDF Print Layout

The existing HTML-based renderer stays in place. Base template CSS uses
print-oriented A4 margins, a compact readable body size, controlled section and
entry spacing, CJK-safe long-word wrapping, and pagination guards for headings
and entries. The Playwright path explicitly prefers CSS page sizing so the
template's A4 and margin rules are applied consistently. No export endpoint or
filename behavior changes.

## Validation

- Frontend unit tests cover onboarding key behavior, automatic eligibility, and
  manual reopening without resetting completion.
- Backend tests cover mock listing fields, additive responsibilities, and PDF
  CSS/renderer options that prevent clipping.
- Existing backend and frontend suites run in full, followed by the H5
  production build.
