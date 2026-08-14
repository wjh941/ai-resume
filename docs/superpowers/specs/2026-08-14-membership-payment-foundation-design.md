# Membership and Payment Foundation Design

## Goal

Add the second-stage commercial foundation without altering JWT authentication, user isolation, existing data flows, or the SQLite transition strategy.

## Selected Approach

- A compact SQLite membership repository owns the current entitlement (`user_vip`) and immutable payment history (`order_record`). `user_id` is read exclusively from the JWT dependency.
- Three packages map to Free, Basic, and Premium entitlement: monthly and quarterly activate Basic; annual activates Premium. Amounts are stored as integer cents.
- An authenticated callback is the only fulfillment point. In demo mode it accepts the `demo` channel; production rejects simulated completion until a signed WeChat Pay or Alipay branch is configured.
- Backend feature checks are authoritative. The dashboard caches a per-user display copy of VIP status, pre-checks expensive/restricted actions, and opens its existing-style upgrade modal on a `vip_required` response.

## Product Surface

- Audience and mode: an authenticated individual job seeker operating a dense job-search dashboard.
- Primary tasks: understand the current plan, compare packages, complete a clearly labeled simulated purchase in demo mode, and inspect order history.
- Visual direction: retain the existing neutral business dashboard, page topology, CSS variables, card treatment, dark theme, and compact navigation. Membership pages add no new visual system.
- Main states: logged out uses existing login interception; Free shows remaining draft allowance and restricted feature guidance; Basic and Premium display expiry; empty order history explains that no purchase has been made; demo completion reports success and refreshes entitlement.

## Boundaries

- No real payment collection, recurring deduction, coupons, referrals, campaigns, enterprise plans, support tickets, or cloud database migration.
- WeChat Pay and Alipay are documented configuration branches only. Auto-renew is a stored preference only and never charges the user.
- Existing exports continue to use current services. Free and Basic exports add different watermarks; Premium is watermark-free.
- Existing local cache remains as a transitional layer and is scoped by the authenticated user. Membership cache follows the same namespacing rule.

## Verification

- API tests prove unauthenticated rejection, package retrieval, order ownership, demo fulfillment, expiry downgrade, free draft cap, comparison cap, and export watermark selection.
- The existing dashboard verifier plus static checks prove membership routes, API wrappers, and privilege response handling are wired.
- Final smoke checks use the local FastAPI and Vite endpoints in both a logged-in demo state and a restricted Free state.
