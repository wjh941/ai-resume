# Overview Continuation Direct Entry Design

## Context

The Web workspace overview already selects a primary focus and lists up to three continuation items. Resume continuation items currently navigate only to the resume list, forcing the user to locate the same draft again. The overview also has an accessible live status for the primary focus, but continuation actions do not report their outcome.

## Goal

Reduce friction between the overview and the user's next action by opening a known resume draft directly in the existing editor, while making the action feedback explicit and accessible.

## Scope

Modify only the Web overview flow and its tests:

- `web-frontend/src/views/OverviewView.vue`
- `web-frontend/src/App.vue`
- `web-frontend/src/tests/dashboard.spec.ts`
- `web-frontend/src/tests/interaction.spec.ts`

Do not change backend APIs, response shapes, database persistence, dependencies, or the existing editor implementation.

## Architecture And Data Flow

`loadOverview` already returns continuation items with `kind`, optional `id`, `title`, and `target`. `OverviewView` will add one local `openContinuation` handler:

- For a `resume` item with an `id`, set the live action status and emit the existing `open-draft` event with that id.
- For all other continuation kinds, set the live action status and emit the existing `navigate` event with the item's target.
- For starter actions without an id, keep the existing navigation behavior.

`App.vue` will declare the existing `open-draft` listener on the dynamically rendered overview component and assign the id to its existing `editingDraftId` state. The current editor mount, save, and cancel behavior remains unchanged.

## Interaction And Visual Behavior

- Resume continuation actions use the label `继续编辑`; task and application actions retain `继续`.
- Each continuation button gets an `aria-label` containing the item title and action, so repeated buttons remain distinguishable to assistive technology.
- The existing `focusStatus` live region is reused for continuation feedback. It reports the selected action before navigation or editor opening.
- Existing 44px touch targets, three-column desktop layout, single-column mobile layout, spacing, and color tokens remain unchanged.
- If a resume continuation has no id, it falls back to the resume list route instead of emitting an invalid editor event.

## Testing

- `dashboard.spec.ts` continues to verify continuation ordering, focus exclusion, and draft ids.
- `interaction.spec.ts` verifies the overview emits `open-draft`, contains the continuation routing branch, uses accessible labels, and updates the live status.
- Run the complete Web Vitest suite, production build, and `git diff --check` before acceptance.

## Acceptance Criteria

1. Clicking a continuation resume item with an id opens that exact draft in the existing editor.
2. Clicking task/application continuation items navigates to their existing target views.
3. Missing-id resume items do not emit `open-draft` and navigate to the resume list.
4. Continuation actions produce readable live feedback without adding a network request.
5. Existing overview loading, error, empty, focus rotation, and responsive behavior remain intact.
6. All Web tests, build, and whitespace checks pass.

## Non-Goals

- No new dashboard endpoint or historical analytics.
- No streak counters, local persistence, or cross-device engagement model.
- No visual redesign of the overview or resume editor.
