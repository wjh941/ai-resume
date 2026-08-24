# Web Functional Completion Design

Date: 2026-08-24

## Scope

This iteration improves `web-frontend` only. `resume-miniprogram` H5 remains unchanged. Existing API contracts, authentication behavior, Chinese copy, and backend business rules remain authoritative; the Web client adds missing screens and wires existing backend endpoints without duplicating business decisions in the browser.

The work is split into dependency-ordered vertical slices:

1. Complete the existing workbench loop.
2. Add an experience-evidence workspace.
3. Add membership and order visibility before gated features.
4. Add career assessment.
5. Add job comparison and action follow-up.

No new backend endpoints are required for the planned slices. If an endpoint response is insufficient for a screen, the client will show the supported state rather than fabricate data or silently fall back to a mock.

## Current Gaps

- Resume view lists drafts but does not open, copy, delete, or continue editing a draft.
- Applications view creates and lists records but does not expose the existing timeline, reminder, edit, status progression, or deletion APIs.
- Jobs view can query and favorite a role, but does not expose evidence suggestions or resume-readiness feedback.
- Existing backend evidence, assessment, comparison, membership, and order APIs have no independent Web views or navigation entry points.
- VIP limits and upgrade notices are only visible inside API responses; the Web shell has no persistent entitlement or order context.

## User Flows

### Slice 1: Workbench loop

The existing sidebar keeps its current views and gains completion actions inside the relevant views. A user can open a draft in a Web-resident editor workspace backed by `GET /api/draft/{id}` and `POST /api/draft/save`, continue editing, copy or delete a draft, create an application, edit its fields, advance its status, add timeline events, save interview reminders, and delete a record. Every mutation updates local view state after the API confirms success and keeps the existing list visible while the request is pending. The editor does not redirect into H5.

### Slice 2: Evidence workspace

Add an `经历证明` view with a list, create/edit form, verified marker, and delete action. The form maps directly to the existing evidence schema. A role context can request evidence suggestions; the view links each suggestion back to its source evidence and can request resume readiness for the current draft. Empty, loading, unauthorized, validation, and API error states are explicit.

### Slice 3: Membership and orders

Add a `会员与订单` view that loads VIP information and package list, presents package benefits and current entitlement, creates an order, supports the existing demo payment callback only when the backend allows it, and lists the user’s orders. Payment errors such as expired order, unavailable channel, invalid signature, and demo-disabled are rendered as actionable notices. The client never treats order creation as paid until the callback response confirms payment.

### Slice 4: Career assessment

Add a `职业测评` view that loads questions, preserves answers locally while navigating the form, submits once, and renders the returned report. The report mode selector reflects the backend’s simplified/professional projection; upgrade notices link to the membership view. The disclaimer from the API remains visible and the UI does not present the result as medical or guaranteed employment advice.

### Slice 5: Job comparison

Add a `岗位对比` view reachable from career recommendations and the jobs workflow. A user selects the supported number of roles, submits `/api/career/compare`, and sees score breakdown, strengths, gaps, risk notes, and action plans. The view respects the backend’s membership comparison limit and surfaces the server message when the limit is exceeded. A selected weekly target can continue to the existing applications workflow where the current route supports it.

## Architecture

### Navigation

`WebSidebar` remains the single navigation source. New views receive stable `WorkspaceView` keys and are rendered through the existing keyed out-in transition in `App.vue`. The sidebar marks future modules as normal destinations only when their slice is implemented; no dead links are added.

### API layer

Add typed functions under `web-frontend/src/lib` grouped by domain: `evidence`, `membership`, `assessment`, and `career`. They all call `requestApi`, preserve the existing envelope/error behavior, and expose backend response types rather than `unknown` objects. Existing view requests are moved into domain helpers only when doing so does not change payloads or URLs.

### Components

Reuse `AsyncButton`, `LoadingSpinner`, existing form styles, and the current transition/skeleton tokens. Add only narrowly scoped components that remove repeated behavior, such as a status badge, package/order row, evidence form, and assessment question card. Components must remain presentational; API calls and state ownership stay in views or domain composables.

### State ownership

Each view owns its fetch and mutation state. Pending keys are local to the affected row or action so one slow request does not disable unrelated work. All async mutations clear state in `finally`, including rejected and aborted requests. The global session is cleared only by the existing auth/session layer on 401.

## Error, Permission, and Empty States

- `401`: use the existing session cleanup and show the current login-expired path.
- `403`: keep the page mounted, explain the permission/entitlement boundary, and link to membership when an upgrade is relevant.
- `404`: show a recoverable not-found state for draft/evidence/order resources.
- `409`: show the backend conflict text, especially expired orders or membership package conflicts.
- Network/5xx: preserve local form input, clear pending state, and expose retry.
- Empty collections: explain the next useful action without introducing mock records.

## Responsive Interaction

Desktop keeps the current workbench density. On narrow widths, forms collapse to one column, row actions wrap below the record body, comparison items become a vertical sequence, and order/package actions remain full-width. Existing transition and reduced-motion tokens apply to all new views. No animation is added to every list item; motion is reserved for route changes, async feedback, and high-frequency actions.

## Testing and Acceptance

- Add API helper tests for each new domain function: URL, method, payload, response projection, and error propagation.
- Add view-level tests for pending cleanup, duplicate-submit protection, 401/403/409 rendering, empty states, and membership-gated results.
- Preserve and rerun all existing Web tests and H5 tests.
- Build Web and H5 after every implementation slice; H5 should remain unchanged and continue to pass unchanged tests/build.
- Acceptance requires the five flows above to work against the running local backend with no mock fallback, stable loading surfaces, and no permanent pending state after rejection or cancellation.

## Explicit Non-goals

- No changes to H5 pages, H5 routes, or H5 API behavior.
- No new backend business rules, payment provider integration, or real payment credentials.
- No real-time job marketplace or external job scraping.
- No automatic employment guarantee, medical/psychological assessment claims, or fabricated evidence.
