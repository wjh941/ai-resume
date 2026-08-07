# Career Growth and Match Report Design

## Goal

Extend the existing AI career consultation flow with an actionable three-stage career route, a transparent job-match report for every resume review, more explicit job-risk guidance, and optional user-supplied requirements. Preserve all existing job-analysis, identity-plan, CSV-independent resume-draft, and PDF text-extraction behavior.

## Scope

- Keep the current five identity codes and all existing response fields.
- Add a structured `career_growth_route` to the job consultation response:
  - `初级`, `中级`, `高级` stages.
  - Each stage has role name, years reference, core skills, responsibilities, and assessment criteria.
- Add `custom_requirement_notes` to job consultation and resume review responses.
- Add a required `job_match_report` to each resume review:
  - integer score from 0 to 100;
  - score basis;
  - matching advantages;
  - missing skills;
  - highlighted priority gaps with learning direction, project practice, and practice tasks.
- Accept an optional `custom_requirement` in job consultation and resume-review requests.
- Keep all resume statements grounded in user input. Unknown facts remain `[待确认]`.
- Expand the existing `隐性软要求`, `行业前景`, and `岗位避雷点` analysis entries. Risk entries use `【避雷】` or `【高频坑】` prefixes for the UI to highlight.

## Backend Design

`app/schemas/consultation.py` receives four new response models:

- `CareerGrowthStage`
- `CareerGrowthRoute`
- `PrioritySkillGap`
- `JobMatchReport`

`JobConsultationRequest` and `ResumeReviewRequest` gain an optional `custom_requirement` with blank-input normalization. `JobConsultationResponse` gains `career_growth_route` and `custom_requirement_notes`. `ResumeReviewResponse` gains `job_match_report` and `custom_requirement_notes`.

`app/services/career_consultation.py` builds a deterministic mock growth route from the role and known skills. The mock job-match score uses a disclosed 20/60/20 formula:

- 20 points for non-empty, usable resume material;
- up to 60 points for target-keyword coverage;
- up to 20 points for supporting-skill coverage.

The report never treats an inferred or fabricated fact as evidence. It records unmatched target skills as gaps and marks recommendations as learning tasks, not completed experience.

`app/services/ai_client.py` keeps the same OpenAI-compatible transport and expands the JSON prompts to require all new fields, the three stages, explicit risks, and preservation of user-provided custom requirements.

## Frontend Design

The existing job-search page retains its query, identity selection, resume review, PDF upload, and career-tools layout. It adds:

- one optional `补充需求` input next to the role query;
- a `职业晋升路线` block after job analysis;
- a `人岗匹配分析报告` block after every resume review;
- priority skill-gap cards visually marked `【需提升】`;
- a concise `已纳入你的补充要求` block when the user has provided additional requirements;
- risk-item styling for list rows containing `【避雷】` or `【高频坑】`.

The page passes the same supplementary requirement to both the job-analysis request and the resume-review request. Existing identity-specific plans, three-month plans, and blank-resume recovery content remain intact.

## Error Handling and Compatibility

- Omitted `custom_requirement` remains valid for old frontend callers.
- Existing clients can still read original response fields. New frontend code reads the new fields.
- Invalid blank custom requirements return the existing validation error envelope.
- The demo-mode market notice remains visible. No output claims that estimated salary or market data is live verified data.

## Tests

- API tests assert that job analysis returns exactly three complete growth stages, stronger risk markers, and custom-requirement notes.
- API tests assert every resume review returns a 0-100 score, gaps, safe `[待确认]` content, and custom-requirement notes.
- AI-client prompt tests assert all new required JSON keys and safety constraints are requested.
- Frontend build and unit suite verify the new type and API mappings compile without changing existing flows.
