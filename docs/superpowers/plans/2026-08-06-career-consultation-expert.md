# Career Consultation Expert Implementation Plan

## Scope

Implement the staged identity-based job consultant and resume text review
experience. Preserve the existing job query, resume draft, template, export,
and cached job intelligence behavior.

## Steps

1. Add consultation schemas and route tests.
   - Define identity, section, job consultation, and resume review models.
   - Add tests for valid responses, exact eight-section count, identity
     validation, and review output separation.

2. Add backend consultation methods.
   - Extend the AI client protocol and mock provider with deterministic
     role-aware consultation and safe resume review output.
   - Add OpenAI-compatible strict JSON prompts for the same schema.
   - Register a separate consultation router without modifying old endpoint
     semantics.

3. Add frontend consultation state and API client.
   - Persist the selected identity locally.
   - Add typed API mappings and a small pure flow helper.
   - Unit test identity labels and first-query transition.

4. Refactor the job search page into stages.
   - First query renders only the required identity prompt.
   - Identity selection renders eight job sections and the tailored action plan.
   - Resume text review renders only issues, rewrite examples, and keywords.
   - Retain the existing resume generation action after job analysis.

5. Verify and deliver.
   - Run backend tests, frontend unit tests, H5 build, and WeChat build.
   - Perform code review and fix important findings.
   - Commit locally and push `feature/ai-resume-demo` only. Do not merge,
     rebase, or create a pull request.
