# Web Brand Expression Design

## Goal

Give the independent web frontend a recognizable "求职成长" visual identity
without reducing its value as an operational workspace. This is the next visual
iteration after the semantic-token and surface reframe.

## Scope

Change only the interaction and presentation layer in `web-frontend/`.

- Emphasize high-value moments: overview, resume editing, career planning,
  assessment, comparison, insights, and membership.
- Keep resume lists, applications, evidence, orders, and account operations
  flat, dense, and scan-friendly.
- Reuse existing routes, branches, CSS tokens, loading/error states, and
  responsive breakpoints.
- Use native CSS transforms and transitions only.

## Brand Direction

The product should feel like a composed career-growth workspace, not a generic
admin dashboard or a marketing site. The visual system uses cobalt as the
directional colour, coral for sparse editorial accents, and semantic status
colours only for their existing meanings.

Page hierarchy follows three consistent layers:

1. Current stage: a small existing or additive presentational marker at the
   page heading, never a new business status.
2. Key decision: the primary score, recommendation, or progress state receives
   the strongest type and cobalt emphasis.
3. Next action: existing action buttons remain compact and operational.

## Page Treatments

### Overview

The overview becomes a concise growth narrative. The current asymmetric KPI row
remains; the existing action route gains a clearer sequential rhythm through
typography, dividers, and existing action targets. It must not acquire new data
or a chart.

### Resume and Career Work

The resume editor and career plan receive stronger chapter hierarchy using their
existing headings and checkpoint/section state. Existing inputs and task rows
remain practical work surfaces, with no new form fields or save paths.

### Analysis and Membership

Assessment, comparison, insights, and membership preserve their decision
surfaces. Scores, report modes, recommendations, and the existing unique
current membership package may receive a stronger cobalt result treatment.
Ambiguous package matches remain neutral as already implemented.

### Operational Records

Resume lists, applications, evidence, orders, and account tools remain record
surfaces: fine borders, compact rows, visible status tags, and no decorative
elevation. Destructive/error/disabled states stay semantic exceptions.

## Motion and Accessibility

- Use existing motion variables and native transitions only.
- Add motion only to stage/result emphasis and existing section transitions;
  no decorative continuous animation or heavy library.
- Preserve keyboard focus visibility, 44px shell targets, disabled states,
  `prefers-reduced-motion`, dark mode, and mobile layouts.
- All text must retain current Chinese content and have no clipping or viewport
  overflow at desktop, wide desktop, and 390px mobile widths.

## Non-Goals

- No new business modules, pages, data sources, charts, routes, APIs, mocks,
  requests, or payloads.
- No component replacement, lockfile/dependency change, H5 change, or backend
  change.
- No gradients as decoration, glass effects, blurred overlays, or card nesting.

## Verification

- Preserve existing focused and full web workflow tests.
- Build `web-frontend` successfully.
- Use actual browser review in light/dark modes at desktop, ultra-wide desktop,
  and 390px mobile. Inspect overview, editor, a decision result, record list,
  focus, disabled, and reduced-motion states.
- Audit the final diff to ensure changes remain in `web-frontend/`, relevant
  docs, and the iteration changelog only.
