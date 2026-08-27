import { expect, it, vi } from "vitest"

import { buildOverviewState, loadOverview, selectFocusAction } from "../lib/dashboard"

it("chooses the earliest incomplete due task before other candidates", () => {
  const state = buildOverviewState({ applications: [{ id: "app-1", company: "Acme", role_name: "Operations", next_action_at: "2099-03-04" }], drafts: [{ id: "draft-1", job_title: "Operations", resume: { basic: { name: "Name", phone: "1", email: "a@b.cn", city: "City" }, job: { target_role: "Operations" } } }], tasks: [{ id: "task-late", title: "Prepare interview", status: "pending", due_date: "2099-03-12" }, { id: "task-soon", title: "Add project results", status: "pending", due_date: "2099-03-01" }] })
  expect(state.focus.kind).toBe("task")
  expect(state.focus.id).toBe("task-soon")
})

it("exposes the application next-action date as a Chinese due label", () => {
  const state = buildOverviewState({ applications: [{ id: "app-1", company: "Acme", role_name: "Operations", next_action_at: "2099-03-04" }], drafts: [], tasks: [] })
  expect(state.focus.kind).toBe("application")
  expect(state.focus.dueLabel).toBe("截止：2099-03-04")
})

it("falls back to starter actions and exposes progress states for empty data", () => {
  const state = buildOverviewState({ applications: [], drafts: [], tasks: [] })
  expect(state.focus.target).toBe("resume")
  expect(state.focusOptions).toHaveLength(3)
  expect(state.progress.map((item) => item.state)).toEqual(["not-started", "not-started", "not-started"])
  expect(state.hasWorkspaceData).toBe(false)
})

it("rotates focus deterministically and puts missing fields behind generic copy", () => {
  const input = { applications: [], drafts: [{ id: "draft-1" }], tasks: [{ id: "task-1", status: "pending" }] }
  const first = selectFocusAction(input, 0)
  const second = selectFocusAction(input, 1)
  expect(first.id).not.toBe(second.id)
  expect(second.title).toContain("行动")
})

it("sorts valid dates first, invalid dates last, then by id", () => {
  const state = buildOverviewState({ applications: [], drafts: [], tasks: [{ id: "z", status: "pending", due_date: "invalid" }, { id: "b", status: "pending" }, { id: "a", status: "pending", due_date: "2099-01-02" }, { id: "c", status: "pending", due_date: "2099-01-01" }] })
  expect(state.focus.id).toBe("c")
  expect(state.continuations.map((item) => item.id)).toEqual(["a", "b", "z"])
})

it("marks terminal applications complete and requires every resume field", () => {
  const complete = buildOverviewState({ applications: [{ id: "offer", status: "offer" }, { id: "closed", status: "closed" }, { id: "rejected", status: "rejected" }], drafts: [{ id: "draft", resume: { basic: { name: "N", phone: "P", email: "E", city: "C" }, job: { target_role: "R" } } }], tasks: [{ id: "done", status: "completed" }] })
  expect(complete.progress.map((item) => item.state)).toEqual(["completed", "completed", "completed"])
  const incomplete = buildOverviewState({ applications: [], drafts: [{ id: "draft", resume: { basic: { name: "N" } } }], tasks: [] })
  expect(incomplete.progress[0].state).toBe("in-progress")
})

it("excludes the selected focus from ordered continuations", () => {
  const state = buildOverviewState({ applications: [{ id: "app", company: "公司", role_name: "岗位", next_action_at: "2099-01-01" }], drafts: [], tasks: [{ id: "task", title: "任务", status: "pending", due_date: "2099-01-02" }] })
  expect(state.focus.id).toBe("task")
  expect(state.continuations.map((item) => item.id)).toEqual(["app"])
})

it("aggregates application, draft, and incomplete task counts from existing APIs", async () => {
  const request = vi.fn().mockResolvedValueOnce({ items: [{ id: "application-1" }, { id: "application-2" }] }).mockResolvedValueOnce([{ id: "draft-1" }]).mockResolvedValueOnce({ items: [{ status: "open" }, { status: "completed" }] })
  await expect(loadOverview(request)).resolves.toMatchObject({ applicationCount: 2, draftCount: 1, openTaskCount: 1 })
})

it("aggregates counts when all dashboard lists are returned directly as arrays", async () => {
  const request = vi.fn().mockResolvedValueOnce([{ id: "application-1" }, { id: "application-2" }]).mockResolvedValueOnce([{ id: "draft-1" }, { id: "draft-2" }]).mockResolvedValueOnce([{ status: "open" }, { status: "completed" }])
  await expect(loadOverview(request)).resolves.toMatchObject({ applicationCount: 2, draftCount: 2, openTaskCount: 1 })
})
