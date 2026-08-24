# Web Visual Reframe Design

Date: 2026-08-24

## Decision

Reframe `web-frontend` as a bright, professional job-search workspace. The
application keeps its existing Vue component and CSS-token architecture,
routes, APIs, mock data, Chinese product copy, and business
flows. This is a visual-system and interaction-hierarchy change only.

The reference is the composition discipline in the public
[21st.dev dashboard collection](https://21st.dev/community/components/s/dashboard):
one coherent application shell, purposeful KPI and action blocks, dense
records where users compare data, and a small number of visually distinct
surfaces. It is not a request to copy third-party code, layouts, imagery, or
branding.

## Problem

The current Web UI uses forest green for the sidebar, primary state, and many
surface accents. Most pages also rely on the same border-and-card treatment.
This makes navigation, action, status, and content compete at the same visual
weight. Long records remain usable, but the shell feels closed-in and the
overview lacks a clear operating rhythm.

## Goals

- Make every existing Web view feel like part of one clear operating
  workspace, while giving overview, editor, record, and analysis surfaces
  distinct visual roles.
- Replace the forest-led palette with warm white, graphite, cobalt blue, and
  restrained coral emphasis.
- Reduce unnecessary framed-card repetition. Use elevation only for true
  tools, compact decision blocks, dialogs, and repeated comparison items.
- Preserve scanning density on records and wide tables; do not turn every
  business view into a marketing composition.
- Keep dark mode coherent and responsive layouts stable from small windows to
  ultrawide screens.
- Preserve all previously delivered loading, pending, validation,
  accessibility, and reduced-motion behavior.

## Non-goals

- No new business page, route, API call, mock fixture, workflow, or user
  capability.
- No component-library or animation-library dependency.
- No new decorative gradients, glass panels, oversized hero art, generic bento
  grids on every page, or copied 21st.dev assets/code.
- No changes to existing Chinese business content. Only existing control
  placement and style may change.

## Visual Language

### Color roles

Centralize the semantic palette in `web-frontend/src/styles/base.css`.

| Role | Light token direction | Use |
| --- | --- | --- |
| Canvas | cool warm-white / very pale blue-gray | page background |
| Surface | white | controls, drawers, forms, data surfaces |
| Ink | graphite | headings and primary text |
| Muted | blue-gray | helper text and secondary labels |
| Primary | cobalt blue | primary actions, active navigation, focus |
| Primary tint | pale blue | selected/hover backgrounds and KPI support |
| Accent | coral | attention, one key status, destructive contrast only where semantically valid |
| Success | green-teal | completed/synced state only |
| Warning | warm amber | review-required state only |
| Danger | accessible red | validation and destructive actions only |

The final values must meet readable contrast in light and dark mode. Blue is
the only general action color. Coral does not become a second primary button
system. Dark mode becomes charcoal/navy with lifted slate surfaces and keeps
the same semantic tokens instead of inverting the light palette literally.

### Typography and geometry

- Retain the installed Chinese-capable system font stack.
- Use a compact page heading scale and tabular figures for metrics.
- Keep `8px` or smaller radii for operational surfaces.
- Prefer flat separators, grouped spacing, and selected-state fills over
  repeated drop shadows. Reserve one soft shadow tier for elevated tools.
- Use icons as supporting anchors for actions/status, never as decoration.

## Application Shell

### Navigation

The sidebar becomes a light, fixed operating rail on desktop: neutral
background, compact brand area, grouped navigation, and an unmistakable blue
active rail/tint. Hover states are subtle and do not move layout. The current
mobile navigation behavior and business destinations remain unchanged.

The top bar becomes a quiet utility strip: page context at left and status,
theme, account, and logout tools at right. The layout must not imitate a
marketing header or introduce a second navigation hierarchy.

### Page frame

The workspace uses a readable max width at desktop sizes, a wider but bounded
content measure for data tables, and consistent vertical section rhythm. Page
headings reserve the strongest type for the page task, not every panel. A
single compact action cluster aligns with each heading when an existing action
exists.

## Component Strategy

### Overview and insight surfaces

Use a restrained KPI strip or asymmetric three-zone grid: one primary task
zone, compact measurable progress, and a next-action zone. Metric tiles use
semantic tinted icon wells and direct linked action affordance; they are not
all treated as floating cards. Existing overview API data and navigation
events remain exactly as they are.

Career planning, assessment, comparison, insights, and membership can use
small bounded decision panels where comparison benefits the user. Their forms,
results, and request semantics remain unchanged.

### Editor and form surfaces

Resume editor, job search, application form, evidence form, account, and
membership controls use a crisp field rhythm: label, input, assistive/error
copy, and related action. Validation, local-save state, loading, inline error
summary, keyboard shortcuts, and focus restoration retain their current
contracts. Form shells are framed tools, not a stack of nested cards.

### Records and data tables

Resume drafts, jobs, applications, evidence, and orders use dense row groups
with clear hover/selection treatment, status chips, fixed action zones, and
subtle alternating structure only when it improves scanning. Keep the existing
progressive rendering, source-authoritative mutations, wide application-table
scroll behavior, and mobile stacked layout. No table behavior or data mapping
changes.

### Empty, loading, and feedback states

Empty states get one clear icon well, concise preserved Chinese copy, and the
existing action only when one already exists. Skeletons maintain final layout
height. Spinner, pending, success, error, disabled, and retry states continue
to use the established shared components; the new palette only improves their
hierarchy.

## Motion and Interaction

- Keep current native transition variables and reduced-motion rules.
- Use 160-240ms opacity, color, and small translate transitions for shell,
  rows, buttons, and surface focus. Do not add global bounce, particles, or
  animated decorative gradients.
- Primary buttons use existing press/ripple feedback in cobalt. Secondary
  actions use a border/tint response. Disabled controls remain visually quiet
  and do not transform.
- Theme switching updates semantic tokens together to avoid flashes.

## Responsive Behavior

- Desktop: 240-260px navigation rail, constrained workspace, optional wide
  data surface where already needed.
- Small desktop/window: collapse spacing before shrinking controls; maintain
  readable action clusters.
- Mobile: retain current stacking and scroll behavior; do not hide required
  controls behind decorative chrome.
- Ultrawide: prevent overextended text lines and avoid stretching cards into
  sparse full-width panels.

## Implementation Boundaries

- Update the existing CSS token layer and currently delivered Web shell/views.
- Prefer shared semantic classes and component-local markup hooks over one-off
  per-page color values.
- Do not touch `resume-miniprogram` in this visual reframe.
- Do not replace `AsyncButton`, `LoadingSpinner`, error handling, checkpoint,
  keyboard, or progressive-list logic. Styling may consume their existing
  classes/attributes.
- Preserve all existing Chinese strings and mock/API contracts byte-for-byte.

## Verification

- Extend or add focused Web tests only when markup/interaction contracts
  change. Existing API/domain tests remain part of regression verification.
- Run Web unit tests and production build.
- Review desktop, small-window, and mobile layouts for text wrapping,
  overflow, focus visibility, dark-mode switch, tables, drawers, loading,
  empty states, and disabled actions.
- Run `git diff --check`; confirm changed paths stay within `web-frontend/`
  and documentation.
- Update `docs/interaction-upgrade-changelog.md` with the visual-system scope
  and verification evidence.
