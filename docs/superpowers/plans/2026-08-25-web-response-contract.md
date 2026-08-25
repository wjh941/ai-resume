# Web Response Contract Compatibility Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Web list adapters accept both direct arrays and `{ items }` responses while surfacing malformed shapes through the existing error path.

**Architecture:** Add a strict generic `readItems<T>` helper beside `requestApi`. It returns arrays unchanged, unwraps `{ items }`, and throws `ApiRequestError` with status `0` for invalid shapes. Existing domain adapters call it before their current snake_case-to-camelCase mapping; backend routes remain unchanged.

**Tech Stack:** Vue 3 + TypeScript, Vitest, Vite, native `Error` subclasses.

## Global Constraints

- Preserve existing backend routes, API payloads, response envelopes, mock data, Chinese copy, page structure, and business logic.
- Do not add new business pages, modules, dependencies, or schema-validation libraries.
- Keep direct arrays and `{ items: T[] }` valid; malformed list shapes must be observable errors, not silent empty states.
- Preserve existing network, non-JSON, 204, and `AbortError` handling.

---

### Task 1: Add the shared list-response boundary

**Files:**
- Modify: `web-frontend/src/lib/api.ts`
- Create: `web-frontend/src/tests/response-contract.spec.ts`

**Interfaces:**
- Produces `readItems<T>(payload: T[] | { items?: T[] } | null | undefined): T[]`.
- Reuses `ApiRequestError` from `web-frontend/src/lib/api.ts` with `status === 0` for invalid shapes.

- [ ] **Step 1: Write failing helper tests**

```ts
import { describe, expect, it } from "vitest"
import { ApiRequestError, readItems } from "../lib/api"

describe("readItems", () => {
  it("keeps direct arrays", () => expect(readItems([{ id: "a" }])).toEqual([{ id: "a" }]))
  it("unwraps item envelopes", () => expect(readItems({ items: [{ id: "b" }] })).toEqual([{ id: "b" }]))
  it("rejects malformed list payloads", () => {
    expect(() => readItems({ items: null } as { items?: unknown[] })).toThrow(ApiRequestError)
    expect(() => readItems({})).toThrowError(expect.objectContaining({ status: 0 }))
  })
})
```

- [ ] **Step 2: Run the focused test and verify it fails**

Run: `npm.cmd test -- src/tests/response-contract.spec.ts`

Expected: FAIL because `readItems` is not exported yet.

- [ ] **Step 3: Implement the minimal helper**

```ts
export function readItems<T>(payload: T[] | { items?: T[] } | null | undefined): T[] {
  if (Array.isArray(payload)) return payload
  if (payload && Array.isArray(payload.items)) return payload.items
  throw new ApiRequestError("列表响应格式异常，请稍后重试", 0)
}
```

- [ ] **Step 4: Run the focused test and verify it passes**

Run: `npm.cmd test -- src/tests/response-contract.spec.ts`

Expected: 3 tests pass.

- [ ] **Step 5: Commit the boundary helper**

```bash
git add web-frontend/src/lib/api.ts web-frontend/src/tests/response-contract.spec.ts
git commit -m "feat: add strict web list response adapter"
```

### Task 2: Migrate existing list adapters

**Files:**
- Modify: `web-frontend/src/lib/drafts.ts`
- Modify: `web-frontend/src/lib/dashboard.ts`
- Modify: `web-frontend/src/lib/evidence.ts`
- Modify: `web-frontend/src/lib/applications.ts`
- Modify: `web-frontend/src/lib/career.ts`
- Modify: `web-frontend/src/lib/membership.ts`
- Modify: `web-frontend/src/tests/domain-api.spec.ts`
- Modify: `web-frontend/src/tests/dashboard.spec.ts`

**Interfaces:**
- Each list function keeps its existing public return type.
- Each adapter calls `readItems(await requestApi(...))` before `.map`, `.filter`, or `.length`.

- [ ] **Step 1: Add direct-array and malformed-shape regression cases**

Add direct-array coverage for evidence, applications, career tasks, membership
packages/orders, and draft lists. Add one malformed-shape case asserting
`listEvidence()` rejects with `ApiRequestError` status `0`. Keep existing
request paths and field-name assertions unchanged.

- [ ] **Step 2: Run the affected adapter tests and verify any missing migrations fail**

Run: `npm.cmd test -- src/tests/domain-api.spec.ts src/tests/dashboard.spec.ts`

Expected: FAIL for adapters that still call `.items` directly when their new
direct-array fixtures are exercised.

- [ ] **Step 3: Migrate each adapter to `readItems`**

Use the same pattern without changing endpoint paths:

```ts
const payload = await requestApi<BackendItem[] | { items?: BackendItem[] }>(path)
const items = readItems(payload)
return items.map(fromBackend)
```

For the dashboard, count the result of `readItems` for drafts, applications,
and tasks, then keep the existing completed-task filter.

- [ ] **Step 4: Run affected tests and verify they pass**

Run: `npm.cmd test -- src/tests/domain-api.spec.ts src/tests/dashboard.spec.ts`

Expected: all affected tests pass, including direct-array and malformed-shape
cases.

- [ ] **Step 5: Commit adapter migration**

```bash
git add web-frontend/src/lib web-frontend/src/tests/domain-api.spec.ts web-frontend/src/tests/dashboard.spec.ts
git commit -m "fix: normalize web list response shapes"
```

### Task 3: Record and verify the integration hardening

**Files:**
- Modify: `docs/interaction-upgrade-changelog.md`

- [ ] **Step 1: Append a changelog entry**

Record the shared helper, affected list adapters, strict malformed-shape error,
and the fact that backend routes and payloads were not changed.

- [ ] **Step 2: Run the complete Web verification**

Run: `npm.cmd test`

Expected: all Web test files pass with zero failures.

Run: `npm.cmd run build`

Expected: Vite production build exits with code 0.

Run: `git diff --check`

Expected: no whitespace errors.

- [ ] **Step 3: Confirm clean state and commit documentation**

```bash
git add docs/interaction-upgrade-changelog.md
git commit -m "docs: record web response contract hardening"
git status --short
```

Expected: status output is empty.
