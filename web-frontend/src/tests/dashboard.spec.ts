import { expect, it, vi } from "vitest"

import { buildOverviewState, loadOverview, selectFocusAction } from "../lib/dashboard"

it("chooses the earliest incomplete due task before other candidates", () => {
  const state = buildOverviewState({ applications: [{ id: "app-1", company: "Acme", role_name: "Operations", next_action_at: "2099-03-04" }], drafts: [{ id: "draft-1", job_title: "Operations", resume: { basic: { name: "Name", phone: "1", email: "a@b.cn", city: "City" }, job: { target_role: "Operations" } } }], tasks: [{ id: "task-late", title: "Prepare interview", status: "pending", due_date: "2099-03-12" }, { id: "task-soon", title: "Add project results", status: "pending", due_date: "2099-03-01" }] })
  expect(state.focus.kind).toBe("task")
  expect(state.focus.id).toBe("task-soon")
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
  expect(second.title).toContain("Action")
})

it("aggregates application, draft, and incomplete task counts from existing APIs", async () => {
  const request = vi.fn().mockResolvedValueOnce({ items: [{ id: "application-1" }, { id: "application-2" }] }).mockResolvedValueOnce([{ id: "draft-1" }]).mockResolvedValueOnce({ items: [{ status: "open" }, { status: "completed" }] })
  await expect(loadOverview(request)).resolves.toMatchObject({ applicationCount: 2, draftCount: 1, openTaskCount: 1 })
})

it("aggregates counts when all dashboard lists are returned directly as arrays", async () => {
  const request = vi.fn().mockResolvedValueOnce([{ id: "application-1" }, { id: "application-2" }]).mockResolvedValueOnce([{ id: "draft-1" }, { id: "draft-2" }]).mockResolvedValueOnce([{ status: "open" }, { status: "completed" }])
  await expect(loadOverview(request)).resolves.toMatchObject({ applicationCount: 2, draftCount: 2, openTaskCount: 1 })
})
