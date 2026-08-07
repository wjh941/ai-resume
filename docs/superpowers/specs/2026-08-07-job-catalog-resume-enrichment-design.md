# Job Catalog and Resume Enrichment Design

## Goal

Improve the local AI job-search demo so users can search and compare multiple
related roles, choose the exact target role before generating a resume, and
receive detailed but fact-safe resume enrichment and career-toolkit guidance.

## Product Decisions

### Persistent role catalog

- Add a SQLite `job_catalog` table seeded on application startup.
- Store canonical role names, category labels, aliases, and ordering.
- Searching a keyword such as `工程师` returns matching canonical roles such
  as `数据工程师` and `AI Agent工程师`.
- The catalog is only a discovery index. Role intelligence remains produced by
  the existing `/api/job/query` and consultation flow, so each selected role
  has independent information and cache entries.

### Multi-role search

- The search page renders suggestion buttons below the role input.
- Users may select up to three roles in one consultation session.
- After identity selection, the client loads an independent consultation result
  for every selected role.
- Result tabs let users switch the visible job analysis without losing the
  other selected-role results.
- Existing identity persistence remains unchanged. The first role is stored as
  the pending role for compatibility with existing consultation state.

### Explicit resume target selection

- Clicking “generate resume” never immediately changes the draft.
- A target-role picker is shown for every selected role, including a session
  containing one role.
- The user explicitly confirms one role before the existing template flow is
  entered.
- The selected role becomes the active job intelligence and is used by the
  existing draft/template workflow.

### Fact-safe resume enrichment

- Do not invent employers, schools, dates, certificates, project facts, or
  measured results.
- When a draft has no project experience, role preparation adds one detailed
  practice-project draft whose unknown facts are explicitly marked
  `[待确认]`.
- Role-specific internship drafts are made available as an optional, explicit
  form action. They are never automatically inserted into the resume because a
  company, dates, and responsibilities must come from the user.
- Draft descriptions use a structured “business context / action / tools /
  deliverable / evidence” format and give users enough content to adapt their
  real experience competitively.

### Detailed career toolkit

- Every existing toolkit topic keeps its topic-specific advice.
- Each response additionally includes an identity-aware action checklist,
  copyable language, and a verification/risk section.
- The existing API response shape remains unchanged: the service only expands
  its `sections` collection.

## Interfaces

### Backend

- `GET /api/job/suggestions?q=<keyword>` returns:

  ```json
  {
    "items": [
      { "role_name": "数据工程师", "category": "数据与平台" }
    ]
  }
  ```

- `JobCatalog.search(query: str, limit: int = 8) -> list[JobSuggestion]`
  reads only the local SQLite catalog.
- Existing `/api/job/query`, consultation, CSV-like resume payloads, draft
  persistence, and export interfaces remain unchanged.

### Frontend

- `queryJobSuggestions(query: string): Promise<JobSuggestion[]>` maps the
  backend naming convention to `roleName` and `category`.
- `prepareResumeForJob` remains the entry point for setting job-level fields.
- `createRoleBasedProjectDraft` and `createRoleBasedInternshipDraft` return
  form-compatible draft entries with `[待确认]` placeholders.

## Compatibility and Safety

- Existing draft JSON structures are unchanged.
- Existing job cache entries and generated files are unchanged.
- Empty searches return no suggestions instead of producing a validation error.
- Job queries for canonical suggestions remain normal AI/cache queries, so
  `数据工程师` and `AI Agent工程师` never share a result object.
- The catalog seed uses `INSERT OR IGNORE` so existing local databases remain
  valid and users can keep their data.

## Acceptance Criteria

1. `工程师` suggestions include at least `数据工程师` and `AI Agent工程师`.
2. A user can select two roles, load separate analyses, switch between them,
   and choose one role before creating a resume.
3. Resume preparation enriches blank drafts with detailed, marked practice
   content without creating fictional employer history.
4. Optional internship drafts preserve `[待确认]` placeholders.
5. All career-toolkit topics expose detailed actionable sections.
6. Backend tests, frontend unit tests, H5 build, and WeChat Mini Program build
   pass without changing the existing export behavior.
