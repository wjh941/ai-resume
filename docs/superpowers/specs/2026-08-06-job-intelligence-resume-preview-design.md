# Job Intelligence And Resume Preview Design

## Goal

Fix the local demo so different roles show different job intelligence and a
user can create a visible, job-targeted resume draft even before every form
field is complete.

## Root Causes

- `MockAIClient.query_job()` returns the same salary, responsibility, skill,
  and career data for every role, changing only `role_name`.
- The resume form's primary action calls `save()` instead of navigating to
  template selection.
- Template selection and resume editor pages are placeholders.

## Selected Approach

### Role-Specific Local Job Intelligence

Keep `AI_PROVIDER=mock` fully offline, but select a deterministic profile from
role-name keywords. The initial profiles are data, frontend, backend, product,
and a generic fallback. Each profile has distinct salary bands,
responsibilities, required skills, bonus skills, and career route.

The mock cache namespace changes from `mock` to `mock-v2`. This avoids serving
the older generic cached payload for seven days while leaving real-provider
cache entries untouched.

### Safe Automatic Completion

`prepareResumeForJob()` fills only empty, non-factual fields:

- target role and draft title use the selected role;
- expected salary uses the job's `1-3_years` market range;
- availability defaults to `可协商`;
- an empty skills array receives `（待确认）`-suffixed job keywords;
- an empty self-evaluation receives a job-targeted, review-required summary.

Education, employment, project history, personal identity, phone, email, and
city are never invented or overwritten. Preview rendering displays empty
identity values as `待补充`; entirely empty factual sections are hidden.

### Resume Creation Flow

The primary resume-form action becomes `智能补全并选择模板`. It prepares the
active draft locally and navigates without forcing a draft save or blocking on
contact-field validation. The separate `保存草稿` action retains its existing
validation and API behavior.

Template selection renders four selectable visual cards. Selecting a template
stores its ID and navigates to a resume preview editor. The editor presents a
complete reading layout for the selected template, allows returning to the
form, and lets the user save the draft once required contact fields are
complete.

## Constraints

- Do not change FastAPI endpoints, database schema, export formats, or draft
  payload structure.
- Do not fabricate or overwrite factual candidate data.
- Existing valid user-entered values always win over auto-completion.
- Keep the four template IDs: `business`, `technology`, `graduate`,
  `analytics`.
- Do not push, merge, or create a pull request.
