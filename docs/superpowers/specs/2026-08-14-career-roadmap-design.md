# Interactive Career Roadmap Design

## Goal

Extend the existing Sprint / Safe / Backup career-planning surface with structured AI analysis, actionable promotion-roadmap interactions, and a user-to-job competency comparison. Preserve JWT ownership, membership enforcement, current job planning, and all existing dashboard navigation.

## Selected Approach

- Add one authenticated `POST /api/job/plan` route. The route gets the user identity only from the JWT dependency, gathers that user's career profile, verified evidence, latest resume draft, and saved assessment, then calls the configured LLM for a validated structured plan.
- The `expand_detail` request flag selects a concise or detailed LLM prompt. Free users always receive the concise response and a short roadmap. Basic and Premium users receive detailed six-section analysis, complete roadmap tooltips, and full competency comparison data.
- Keep the established `full_job_report` entitlement as the server-side capability for detailed plans and comparisons. The dashboard performs a display precheck, while the backend remains authoritative.
- Use native CSS and Vanilla JS only. The roadmap uses a two-track horizontal node list, progress fills, standard `title`-style hover details, and click handlers that append a task to an existing 7 / 30 / 90-day plan.
- Store roadmap task completion, comparison history, and generated plan cache with existing user-scoped local-storage helpers. Keys resolve to `resume-dashboard:{jwt-sub}:{business-key}` and never migrate legacy unscoped data.

## Product Surface

- Audience and mode: an authenticated job seeker operating a compact, information-dense planning dashboard.
- Existing three-tier cards remain the primary information hierarchy. Each card now contains an analysis refresh action, a competency comparison action, a technical/management route toggle, and visual 7 / 30 / 90-day task blocks.
- The six report sections are collapsible `details` cards to preserve scanability. They cover market context, responsibilities, hard-skill gaps, soft competencies, career value, and risks.
- The comparison modal is two-column on desktop and stacks on mobile. Matched, partial, and missing competencies use the dashboard's green, blue, and amber semantic tag system. Missing-skills actions create a prefilled, unverified evidence item and navigate to the evidence library.
- The interface uses the incumbent dashboard variables, shadow, radius, typography, dark theme, and compact controls. It adds no external assets, charts, or stylesheet files.

## Data and Failure States

- `/api/job/plan` returns validated structured data for all six sections, promotion tracks, competency comparison items, and 7 / 30 / 90-day actions. It does not accept `user_id` in request data.
- If cloud generation is unavailable, the dashboard keeps the existing authenticated API behavior and falls back only to an in-memory display plan so local UI preview remains usable. The fallback is never persisted as server truth.
- Free users see a concise plan and a clear upgrade affordance for detailed report content, complete promotion nodes, and the full comparison modal. Basic and Premium users retain full records locally under their account namespace.
- Clicking a roadmap node deduplicates its generated learning task before saving and recalculates completion progress. An overdue task requires an explicit due date and is highlighted only when incomplete.

## Boundaries

- No change to JWT encoding, authentication routes, payment orders, existing tier definitions, resume/export flows, delivery flows, or evidence CRUD contracts.
- No real market-data feed, third-party chart library, referral, coupon, promotion, recurring charge, or enterprise functionality.
- `expand_detail` is a cost-control switch, not a client-side permission mechanism. The server determines whether it is honored.

## Verification

- Backend tests prove authentication is required, the JWT user is the only user data source, `expand_detail` is downgraded for Free, Basic receives the detailed response, and LLM failure maps to the existing friendly response shape.
- Dashboard verifier exercises pure plan normalization, task progress, namespaced persistence keys, and evidence-draft construction, and checks the route, interaction handlers, and six-section rendering hooks.
- Release verification runs backend tests, dashboard verifier, H5 build, whitespace/syntax checks, one Impeccable detector pass, and a code-review pass before commit and push.
