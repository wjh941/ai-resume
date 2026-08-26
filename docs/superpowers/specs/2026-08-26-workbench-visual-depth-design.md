# Web Workbench Visual Depth Design

Date: 2026-08-26

## Intent

Make the existing Web frontend feel like a calm, refined job-search
workbench: clear hierarchy, warmer color balance, visible but restrained
surface depth, and tactile feedback that helps users understand what can be
acted on. This is an interaction and visual-system pass only.

## Scope

- Keep every existing route, view, API call, request payload, mock dataset,
  Chinese UI string, loading/error state, and business workflow unchanged.
- Change only the shared Web visual layer and existing presentation hooks.
- Keep the H5 implementation untouched.
- Use native CSS transitions and existing Vue/Lucide components; add no UI or
  animation dependency.

## Direction

The reference is the composition discipline of 21st.dev dashboard patterns:
one coherent shell, a small number of purposeful metric/action surfaces, and
dense records where comparison matters. The implementation will remain
product-specific rather than copying third-party code or branding.

### Considered approaches

1. Card-heavy bento redesign: rejected because repeated framed cards would
   reduce scanning density and make the workbench feel like a marketing page.
2. **Layered operating canvas (selected):** use a bright canvas, neutral rail,
   cobalt action hierarchy, restrained coral/teal semantic accents, and one
   shared elevation tier for true interactive surfaces.
3. Full palette replacement: rejected because it would create unnecessary
   contrast risk and destabilize the existing dark theme.

## System changes

- Centralize panel, hover, and dark-theme shadow values in `base.css`.
- Give the shell four readable roles: canvas, navigation rail, tool panel, and
  data surface. Borders remain the primary separator; shadows are reserved for
  tool panels and pointer hover feedback.
- Apply a small visual lift only to high-value interactive surfaces on devices
  that support hover. Invalid/error states keep their semantic border and do
  not lift.
- Use balanced heading wrapping and deliberate spacing to make each view's
  current task obvious without changing copy or markup structure.
- Keep mobile layouts flat and touch-friendly; hover-only rules must not run on
  coarse pointers. Reduced-motion users receive the same state hierarchy with
  transitions disabled.

## Verification

- Add one focused source contract for the shared visual tokens and hover scope.
- Run full Web and H5 unit suites, both production builds, `git diff --check`,
  and the Impeccable detector over changed UI targets.
- Start the Web dev server on an available port and verify the served document
  is the project shell, not another local service.

