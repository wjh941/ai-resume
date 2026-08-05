# AI岗位查询与智能简历生成小程序 Design

## Goal

Build a locally runnable personal-demo application that helps a user:

1. Query a target role and receive structured role intelligence.
2. Enter and save resume data as editable drafts.
3. Apply AI-assisted wording improvements without inventing facts.
4. Preview one of four resume templates.
5. Export a `.docx` or `.pdf` file from the backend.

The project lives at `D:\Projects\ai-resume-miniprogram`. It has no payment,
membership, crawler, admin console, or real account system.

## Product Decisions

- A generated `client_id` stored in Uni-App local storage identifies the demo
  user. There is no login or WeChat authorization.
- The frontend uses Uni-App with Vue 3, TypeScript, Pinia, and `uni-ui`.
- The backend uses FastAPI, SQLite, Pydantic, and a JSON payload per draft.
- The default AI provider mode is `mock`. `ark` and `openai_compatible` are
  enabled only when their environment configuration is present.
- PDF export uses Playwright Chromium as the default renderer. WeasyPrint is
  implemented as an optional fallback adapter, not a required Windows runtime
  dependency.
- Generated backend files return a short-lived download URL. The mini-program
  first downloads and opens the file directly; the URL is retained as an H5
  fallback.

## Repository Layout

```text
ai-resume-miniprogram/
├─ resume-miniprogram/                 # Uni-App frontend
│  ├─ src/
│  │  ├─ pages/
│  │  ├─ components/
│  │  ├─ stores/
│  │  ├─ services/
│  │  ├─ types/
│  │  └─ utils/
│  ├─ pages.json
│  ├─ manifest.json
│  ├─ package.json
│  └─ vite.config.ts
├─ resume-backend/                     # FastAPI backend
│  ├─ app/
│  │  ├─ api/
│  │  ├─ schemas/
│  │  ├─ services/
│  │  ├─ repositories/
│  │  ├─ templates/
│  │  └─ static/
│  ├─ tests/
│  ├─ temp/
│  ├─ .env.example
│  ├─ requirements.txt
│  └─ main.py
├─ docs/
│  ├─ local-development.md
│  ├─ wechat-build-and-release.md
│  └─ server-deployment.md
├─ scripts/
│  └─ start.bat
└─ README.md
```

## Frontend

### Stack

- Uni-App Vue 3 composition API.
- TypeScript for API payloads and form data.
- Pinia stores for the active role, active resume draft, and local `client_id`.
- `uni-ui` form, popup, list, and icon components.

### Pages

#### 1. Job Search

- Job title input and `查询岗位情报` action.
- Structured result sections: salary by experience, responsibilities,
  hard requirements, required skills, bonus skills, and career route.
- `以此岗位生成简历` creates the active job context and navigates to the
  resume form.

#### 2. Resume Form

- A controlled form whose editable value is the canonical `ResumePayload`.
- Education, employment/internship, and project records are arrays with
  add/delete controls.
- Reusable section components prevent repeated page-level array logic.
- `保存草稿`, `AI智能优化简历`, and `下一步选择模板` actions are fixed at the
  bottom of the page.
- Client validation runs before API submission: required name/contact/city,
  valid mobile format, valid email, and valid date ranges.

#### 3. Template Picker

- Four card previews:
  - `business`
  - `technology`
  - `graduate`
  - `analytics`
- Each card renders the active resume payload through a compact preview
  component rather than a static image.
- The selected template is saved to the active draft before navigation to
  the editor.

#### 4. Resume Editor

- The preview is built from section components driven by one normalized resume
  state object.
- Text editing opens an inline editor popup; it does not attempt a desktop
  WYSIWYG implementation inside the mini-program.
- Education, experience, and project order uses touch-friendly move-up and
  move-down controls. This is more reliable in WeChat Mini Program than
  generic HTML drag-and-drop and still provides explicit ordering.
- Section switches hide a section from preview and export without deleting
  its underlying draft data.
- AI rewrite supports `light` and `deep` modes.
- Save, Word export, PDF export, and draft-list navigation remain available.

#### 5. Draft Manager

- List current client's drafts with job title, template name, and updated time.
- Edit opens the existing draft.
- Copy creates a new draft through a dedicated backend endpoint.
- Delete uses a confirmation dialog.

### Frontend Persistence

- `client_id` is a UUID generated once and stored by `uni.setStorageSync`.
- The active unsaved form is checkpointed to local storage after meaningful
  form changes.
- Backend drafts are the authoritative persisted records after a successful
  save.

## Backend

### Application Structure

- `api/`: HTTP route modules.
- `schemas/`: Pydantic request and response contracts.
- `repositories/`: SQLite-only persistence code.
- `services/`: AI, job-cache, export, and temp-file lifecycle services.
- `templates/`: HTML/CSS resume templates and DOCX template assets.
- `static/downloads/`: short-lived generated files served through tokenized
  paths.

### SQLite Schema

```sql
CREATE TABLE user_draft (
    id TEXT PRIMARY KEY,
    client_id TEXT NOT NULL,
    job_title TEXT NOT NULL,
    template_id TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE template_table (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    config_json TEXT NOT NULL,
    docx_template_path TEXT,
    active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE job_cache (
    normalized_role TEXT PRIMARY KEY,
    provider_mode TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    created_at TEXT NOT NULL
);
```

`payload_json` contains the current resume form, selected role snapshot,
section visibility, and ordered arrays. The schema is versioned inside the
JSON payload so later changes can be migrated without changing historical
columns.

### API

All API responses use:

```json
{
  "code": "ok",
  "data": {},
  "message": ""
}
```

Errors return an HTTP status and a stable error code.

| Method | Endpoint | Purpose |
| --- | --- | --- |
| POST | `/api/job/query` | Query cached or AI-generated role intelligence. |
| POST | `/api/resume/ai-rewrite` | Return a rewritten resume payload or selected sections. |
| GET | `/api/template/list` | Return the four seeded template definitions. |
| POST | `/api/draft/save` | Create or update a draft. |
| GET | `/api/draft/list` | List drafts by `client_id`. |
| GET | `/api/draft/{id}` | Read a draft by id and `client_id`. |
| POST | `/api/draft/{id}/copy` | Create a draft copy for the same client. |
| DELETE | `/api/draft/{id}` | Delete a draft for the same client. |
| POST | `/api/export/word` | Render `.docx` and return file metadata. |
| POST | `/api/export/pdf` | Render `.pdf` and return file metadata. |
| GET | `/downloads/{token}` | Serve an unexpired generated file. |
| GET | `/health` | Local startup health check. |

### AI Provider Contract

`AIClient` exposes:

```python
async def query_job(role_name: str) -> JobIntelligence: ...
async def rewrite_resume(
    resume: ResumePayload,
    job: JobIntelligence,
    mode: Literal["light", "deep"],
) -> ResumePayload: ...
```

Provider implementations:

- `MockAIClient`: deterministic fixture-like output for local demo and tests.
- `ArkAIClient`: OpenAI-compatible chat-completions transport configured by
  `AI_BASE_URL` and `AI_API_KEY`.
- `OpenAICompatibleClient`: same transport with a configurable model name.

The provider is selected by `AI_PROVIDER=mock|ark|openai_compatible`.
Unexpected model output is validated by Pydantic. Invalid or non-JSON role
responses produce a clear API error and do not poison `job_cache`.

### Prompt Rules

Job intelligence prompts require a strict JSON object matching
`JobIntelligence`.

Resume rewrite prompts require:

- preserve factual employers, dates, education, certificates, and project
  identities;
- improve clarity and ATS keyword relevance;
- allow quantified phrasing only when the source data includes a metric or
  the model marks a suggested metric as `needs_user_confirmation`;
- limit final content to a practical one- or two-page resume length.

The backend rejects a rewrite that changes immutable factual fields.

### Exports

- A single normalized `ResumePayload` plus template config feeds both renderers.
- Word export uses `python-docx` with four template-specific formatting
  adapters.
- PDF export renders an HTML template through Playwright. Browser files are
  stored under `D:\Projects\ai-resume-miniprogram\.cache\playwright` in local
  development.
- `PDF_RENDERER=playwright|weasyprint` selects the renderer.
- Output files are named:

```text
{姓名}-{求职岗位}-简历.docx
{姓名}-{求职岗位}-简历.pdf
```

- User-controlled filename parts are normalized to remove filesystem-invalid
  characters.
- Generated files are stored under `temp/downloads/<token>/` and deleted by a
  startup cleanup plus a periodic cleanup task after the configured expiry.

## Operational Configuration

`.env.example`:

```dotenv
APP_ENV=development
APP_HOST=127.0.0.1
APP_PORT=8000
DATABASE_PATH=./data/resume_demo.db
AI_PROVIDER=mock
AI_API_KEY=
AI_BASE_URL=https://ark.cn-beijing.volces.com/api/v1
AI_MODEL=
CACHE_EXPIRE_DAY=7
TEMP_FILE_PATH=./temp
EXPORT_FILE_EXPIRE_MINUTES=60
PDF_RENDERER=playwright
PLAYWRIGHT_BROWSERS_PATH=D:/Projects/ai-resume-miniprogram/.cache/playwright
```

`start.bat` will:

1. Create or reuse `.venv`.
2. Install backend dependencies.
3. Install Playwright Chromium in the configured D-drive cache when missing.
4. Initialize SQLite template rows.
5. Start FastAPI on `http://127.0.0.1:8000`.

The Uni-App frontend is started separately through HBuilderX or the package
manager development script, then compiled with the WeChat Mini Program target.

## Testing

- Backend tests use a temporary SQLite file and `MockAIClient`.
- API tests cover job-cache hit/expiry, draft CRUD/copy/isolation, validation,
  rewrite fact protection, and expired-download rejection.
- Export tests validate generated Word files and filenames. PDF tests run only
  when the local Playwright browser is installed; otherwise they are marked
  skipped with an explicit reason.
- Frontend unit tests cover validators, draft state, and ordering utilities.
- An end-to-end local smoke flow covers job query, resume save, template
  selection, and both export endpoints in mock mode.

## Delivery Order

1. Backend foundation: schemas, SQLite, templates seed, mock AI, job cache,
   draft CRUD, and tests.
2. Uni-App foundation: application shell, API client, client id, job page,
   multi-record form, local checkpointing, and draft management.
3. Template preview/editor: four templates, editing popup, ordering,
   visibility switches, and AI rewrite mode.
4. Export and documentation: Word/PDF exports, short-lived download flow,
   Windows start script, deployment documentation, and final smoke tests.

## Explicit Non-Goals

- Payment, membership, points, or an admin portal.
- Crawling or scraping recruitment websites.
- WeChat authorization or a complex account system.
- A desktop-class drag-and-drop editor inside the mini-program.
- MySQL in the first demo. A repository abstraction keeps a later migration
  practical.
