# Job Opportunity Result Depth Design

Date: 2026-08-26

## Goal and Scope

The existing Web 岗位机会 page already receives structured role intelligence and a layered report, but the UI hides most of it (`skills.slice(0, 8)`, `responsibilities.slice(0, 4)`) and does not explain how to use the information. This iteration improves the result reading and action flow only. `/api/job/query`, request payloads, report tiers, mock data, routes, and existing business handlers remain unchanged.

## Result Information Architecture

When a result exists, the page presents:

1. A role verdict: role name, concise summary, and an explicit “参考范围” notice.
2. A decision grid: hard requirements, core skills, bonus skills, and responsibility map. All returned items are available; no arbitrary slicing hides requirements.
3. A salary table that preserves the backend keys and adds a visible verification reminder, without implying live salary data.
4. A career route showing the returned progression from entry to senior/lead roles.
5. A “面试核验清单” derived from existing responsibilities and requirements. Each prompt asks for a concrete example, tool/method, outcome, or evidence source; it does not invent candidate facts.
6. Next actions: simplified mode keeps the service-provided three actions; professional mode exposes the service-provided evidence list and complete action list. Existing upgrade notices stay visible for locked detail.

The layout uses progressive disclosure for long content: high-signal sections are visible, while interview prompts and professional evidence can be expanded. Empty arrays render a clear “暂未提供” state rather than a blank region.

## Data Derivation Contract

The Web view adds typed computed projections only:

- `allSkills = required_skills + bonus_skills` (de-duplicated for display).
- `interviewChecks` maps each returned responsibility/requirement to a deterministic question template.
- `reportEvidence` and `reportActions` read existing `report.evidence`, `report.actions`, `report.mode`, and `report.upgrade_notice` fields when present.

No new API call, field, mock response, or persistence is introduced. The same result remains usable when older responses omit `report` or optional arrays.

## Verification

- Add source-contract tests proving all returned job fields are rendered, no slice truncation remains, and professional/locked report states are represented.
- Run Web unit tests/build, backend job-query tests, `git diff --check`, and a local API/HTTP smoke check.
