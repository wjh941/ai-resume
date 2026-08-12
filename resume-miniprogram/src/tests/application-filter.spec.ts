import { describe, expect, it } from "vitest"

import { filterApplications } from "../utils/application-filter"
import type { ApplicationRecord } from "../types/application"

const items: ApplicationRecord[] = [
  {
    id: "application-1",
    clientId: "client-a",
    company: "[待确认]",
    roleName: "数据工程师",
    city: "上海",
    source: "官网",
    status: "applied",
    appliedAt: "2026-08-12",
    nextActionAt: "2026-08-15",
    interviewNotes: "",
    draftId: null,
    notes: "",
    createdAt: "2026-08-12T00:00:00+00:00",
    updatedAt: "2026-08-12T00:00:00+00:00",
  },
  {
    id: "application-2",
    clientId: "client-a",
    company: "Example",
    roleName: "数据分析师",
    city: "",
    source: "内推",
    status: "interview",
    appliedAt: "2026-08-11",
    nextActionAt: "2026-08-13",
    interviewNotes: "记录真实问题",
    draftId: null,
    notes: "",
    createdAt: "2026-08-11T00:00:00+00:00",
    updatedAt: "2026-08-11T00:00:00+00:00",
  },
]

describe("application status filter", () => {
  it("filters only the requested status while retaining all items for all", () => {
    expect(filterApplications(items, "all")).toHaveLength(2)
    expect(filterApplications(items, "interview")).toEqual([items[1]])
  })
})
