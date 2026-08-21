import { expect, it, vi } from "vitest"

import { loadOverview } from "../lib/dashboard"

it("aggregates application, draft, and incomplete task counts from existing APIs", async () => {
  const request = vi.fn()
    .mockResolvedValueOnce({ items: [{ id: "application-1" }, { id: "application-2" }] })
    .mockResolvedValueOnce([{ id: "draft-1" }])
    .mockResolvedValueOnce({ items: [{ status: "open" }, { status: "completed" }] })

  await expect(loadOverview(request)).resolves.toEqual({
    applicationCount: 2,
    draftCount: 1,
    openTaskCount: 1,
  })
})
