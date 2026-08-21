# Web And H5 Frontend Design

## Goal

Keep one current project checkout and expose two clearly separate frontend products:

- `resume-miniprogram`: the existing Uni-App source, retained for WeChat Mini Program builds and H5 preview.
- `web-frontend`: a standalone browser-first job-management application. It uses the existing FastAPI API without changing existing API contracts.

## Repository Consolidation

The `feature/ai-resume-demo` checkout at commit `02009d1` is the latest published project version. It becomes the sole retained checkout at `D:/Projects/ai-resume-miniprogram`.

The old `master` checkout and the linked feature worktree are not retained as separate copies. The feature branch remains available locally and on `origin`, so the cleanup is reversible through Git history. `D:/Projects/16102` is out of scope because it is unrelated to this project.

## Web Frontend

Create a separate Vite-powered Vue 3 application in `web-frontend` with its own package manifest and development server. It will not reuse the Uni-App rendering layer and will not replace the Mini Program.

The Web application uses a desktop-first application shell with a compact left navigation, top status area, and a responsive content canvas. It will provide dedicated views for dashboard, resume editing, career planning, job opportunities, application tracking, annual employment insights, and account settings. User-facing text remains Simplified Chinese.

The first iteration uses the established `8000` backend endpoints and shared JWT token rules. The standalone Web app stays on a separate development port, while the existing H5 preview keeps its current `5186` contract. API failures show friendly Chinese messages and do not reveal server stack traces.

## Interaction And Presentation

The visual language follows the project-wide modern job-workspace direction: neutral surfaces, modest corner radii, clear typography hierarchy, restrained shadows, consistent hover/focus states, and motion that respects reduced-motion preferences. Report-producing areas support the existing concise and professional tier concept without weakening backend authorization.

## Verification

- Existing backend tests continue to pass.
- Existing Uni-App unit tests and H5 build continue to pass.
- The standalone Web application builds successfully and can authenticate against the existing local API.
- A manual browser smoke check verifies that Web and H5 are independently reachable and neither changes the API port contract.

## Non-Goals

- No replacement of the WeChat Mini Program or its H5 preview.
- No removal of Git history or remote branches.
- No API, database-schema, or authentication breaking change.
