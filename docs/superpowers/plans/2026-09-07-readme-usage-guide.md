# README Usage Guide Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expand `README.md` with an accurate, user-facing feature map, dual-frontend usage guide, and Mermaid end-to-end workflow while preserving existing technical documentation.

**Architecture:** Keep the README as a single entry point. Add concise user guidance near the top, using labels and route names already present in the Web sidebar and mini-program page registry; leave deployment, privacy, AI, and testing details in their existing sections.

**Tech Stack:** Markdown, Mermaid flowchart syntax, PowerShell command examples, Vue/Uni-App route labels sourced from the repository.

## Global Constraints

- Cover the FastAPI backend, Uni-App WeChat mini-program/H5 frontend, and standalone Web workspace.
- Do not change product behavior, API contracts, dependencies, or source code.
- Keep claims bounded by current demo, AI provider, payment, export, and optional search capabilities.
- Explicitly state that generated/imported resume content requires user confirmation and applications are tracked manually.
- Commands and ports must match current package scripts and existing README setup.

---

### Task 1: Verify product surface and documentation anchors

**Files:**
- Read: `README.md`
- Read: `web-frontend/src/components/WebSidebar.vue`
- Read: `web-frontend/src/App.vue`
- Read: `resume-miniprogram/src/pages.json`
- Read: `web-frontend/package.json`
- Read: `resume-miniprogram/package.json`

**Interfaces:**
- Produces the canonical list of Web workspace views, mini-program pages, commands, and local ports used by Task 2.

- [x] **Step 1: Record canonical labels and ports**

Confirm the Web groups/views, mini-program page paths, backend port `8000`, H5 port `5186`, and standalone Web port `5174` from the files above.

- [x] **Step 2: Check existing README sections**

Identify which setup, privacy, AI, deployment, and testing sections must remain unchanged while locating the insertion point for the new user guide.

- [x] **Step 3: Commit no code**

Keep this audit read-only; the only deliverable is the verified source context for the README edit.

### Task 2: Add the user-facing feature and usage guide

**Files:**
- Modify: `README.md`

**Interfaces:**
- Consumes: canonical labels and ports from Task 1.
- Produces: Chinese sections for frontend selection, feature map, numbered workflow, Mermaid diagram, and quick-start orientation.

- [x] **Step 1: Add the frontend selection section**

Explain the roles of `web-frontend`, `resume-miniprogram` H5, and WeChat mini-program in a compact comparison table. Keep the backend as a shared service.

- [x] **Step 2: Add the grouped feature map**

Group the delivered capabilities under `准备资料`, `职业决策`, `求职执行`, and `复盘与账户`, including the corresponding Web view or mini-program page names where helpful.

- [x] **Step 3: Add the numbered main workflow**

Document the expected input, output, and next action for sign-in, evidence capture, assessment/planning, resume generation/editing, application tracking, and review. Include confirmation and privacy boundaries.

- [x] **Step 4: Add the Mermaid flowchart**

Use a fenced `mermaid` block with explicit decision branches for missing evidence and unavailable AI/capabilities. Keep the terminal path at manual confirmation and application follow-up, never automatic submission.

- [x] **Step 5: Add a user-oriented quick-start note**

Point readers to the existing backend/H5/Web/mini-program commands and local URLs without duplicating or contradicting the detailed setup sections below.

- [x] **Step 6: Commit the README update**

```powershell
git add README.md
git commit -m "docs: add readme usage guide"
```

### Task 3: Validate the documentation handoff

**Files:**
- Verify: `README.md`

**Interfaces:**
- Consumes: completed README from Task 2.
- Produces: evidence that the document is internally consistent, renderable Markdown, and limited to the requested documentation scope.

- [x] **Step 1: Check required sections and diagram**

```powershell
rg -n "功能与使用指南|主要使用流程|mermaid|web-frontend|resume-miniprogram|8000|5186|5174" README.md
```

Expected: all required anchors are present and the Mermaid fence is closed.

- [x] **Step 2: Check links and whitespace**

```powershell
git diff --check HEAD~1..HEAD
```

Expected: no whitespace errors; existing relative documentation links remain intact.

- [x] **Step 3: Review scope and status**

```powershell
git status --short -- README.md
git diff --stat HEAD~1..HEAD
```

Expected: only `README.md` is changed by the implementation commit.
