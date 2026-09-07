# README Usage Guide Design

## Goal

Update the repository README so a new user can understand what the product does, which frontend to choose, and how to complete the main job-search workflow without reading source code first.

## Scope

- Cover the FastAPI backend, the Uni-App WeChat mini-program/H5 frontend, and the standalone Web workspace.
- Keep the existing developer setup, environment, privacy, deployment, and testing sections.
- Add a user-facing feature map and an ordered usage guide near the beginning of the README.
- Add one Mermaid flowchart for the primary workflow: sign in, capture evidence, assess and plan, generate and edit a resume, track applications, and review progress.
- Describe demo, AI, network-search, payment, and export limitations accurately and without implying automatic job applications or fabricated experience.

## Proposed README Structure

1. Product positioning and frontend selection.
2. Feature map grouped by preparation, career decisions, execution, and review/account.
3. Main workflow with numbered steps and expected outputs.
4. Mermaid flowchart for the end-to-end workflow.
5. Quick-start commands and local URLs for backend, H5, mini-program, and Web.
6. Existing technical sections retained below the quick-start material.

## Content Rules

- Use Chinese user-facing copy consistent with labels in `web-frontend/src/components/WebSidebar.vue` and `resume-miniprogram/src/pages.json`.
- Distinguish Web workspace routes from mini-program pages; do not claim that one frontend replaces the other.
- Call out manual confirmation for generated or imported resume content and the fact that applications are tracked manually.
- State that local/demo capability, AI provider configuration, payment demo mode, and optional market search affect available results.
- Prefer task-oriented wording: what to enter, what the system returns, and what the user should confirm next.

## Acceptance Criteria

- A new reader can identify the main features and choose Web, H5, or WeChat mini-program.
- The workflow diagram renders in common Markdown viewers that support Mermaid.
- Commands and ports match package scripts and current README setup instructions.
- No product behavior, API contract, dependency, or source code changes are introduced.
- README remains valid Markdown and passes a whitespace/diff check.
