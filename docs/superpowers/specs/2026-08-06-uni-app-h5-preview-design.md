# Uni-App H5 Preview Design

## Goal

Make the current Uni-App frontend viewable in a local browser without changing
resume business behavior, API contracts, draft persistence, or the WeChat Mini
Program target.

## Selected Approach

Use the official Uni-App Vite plugin and match the existing Uni-App alpha
release with its required Vite 5.2.8 toolchain. Add explicit scripts for both
H5 preview and WeChat Mini Program compilation.

The local H5 server listens on `127.0.0.1:5173` and proxies `/api` and
`/downloads` to the existing FastAPI server at `127.0.0.1:8000`. The API
service keeps its absolute backend URL for non-H5 platforms and uses the
same-origin proxy only when compiled for H5.

## Scope

- Add `@dcloudio/vite-plugin-uni` and `@dcloudio/uni-h5` at
  `3.0.0-alpha-5020320260803001`.
- Align `vite` to `5.2.8`, required by the matching Uni-App Vite plugin.
- Add `dev:h5`, `build:h5`, `dev:mp-weixin`, and `build:mp-weixin` scripts.
- Configure the Uni Vite plugin and development proxy.
- Restore the minimal Uni-App bootstrap files required by the official
  compiler: a non-empty app script and an H5 `index.html` entry.
- Exclude the Uni compiler plugin from Node-only Vitest runs.
- Verify the build, existing unit tests, browser H5 startup, and the existing
  FastAPI health endpoint.

## Constraints

- Do not change API endpoints, request or response payloads, draft data,
  resume content behavior, or backend business code.
- Do not remove the WeChat Mini Program target.
- Keep the H5 proxy local-only; it is a development convenience, not a
  production deployment setting.
- Do not push, merge, or create a pull request as part of this work.
