# Phase6 Auth and Account Design

## Goal

Connect the existing JWT backend authentication boundary to the mini-program, then add reversible account, job-collection, and membership UI skeletons without changing existing business APIs or deleting user data.

## Decisions

- Store the JWT and minimal account identity in the existing `uni` storage adapter. `http.ts` reads that one source of truth and adds a Bearer header to every request.
- A 401 clears the saved session and opens a single re-login prompt before routing to the phone-login page. It does not retry requests automatically.
- Phone login keeps the existing development SMS behavior: the backend remains the authority for whether a demo code is exposed, and no real provider is added.
- New account endpoints return a data-scope manifest and acknowledgement-only deletion/export requests. They perform no deletion or file generation.
- Favorite jobs and the one per-user subscription setting live in new SQLite tables keyed by JWT user id. They are local intent records only; no external jobs are fetched or sent.
- Member and order pages call the existing membership endpoints. The only checkout action retains the existing `demo` callback path.

## Compatibility and Safety

- Existing tables, migrations, response envelopes, and endpoint paths remain unchanged. New schema uses `CREATE TABLE IF NOT EXISTS` only.
- New routes join the existing business-router authentication wrapper; all user-specific records are queried by JWT-derived `user_id`.
- Account deletion and account export have explicit TODO comments at the service boundary. They acknowledge a request and never make an irreversible change.

## Verification

- Backend smoke: send demo code, phone login, protected request, token invalidation/401, and logout.
- Backend route coverage: account skeleton responses, favorite ownership, subscription persistence, and existing payment mock behavior.
- Frontend unit coverage: saved token header injection, 401 session clearing and login routing, local session state.
- Full backend/frontend suites and H5 build must pass. The H5 dev server remains on `127.0.0.1:5186` and proxies API requests to the backend default `127.0.0.1:8000`.
