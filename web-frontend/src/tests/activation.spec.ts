import { describe, expect, it } from "vitest"

import { getActivationSteps } from "../lib/activation"
import type { OverviewState } from "../lib/dashboard"

const emptyOverview: OverviewState = {
  applicationCount: 0,
  draftCount: 0,
  openTaskCount: 0,
  focus: { kind: "resume", title: "创建第一份简历", target: "resume" },
  focusOptions: [{ kind: "resume", title: "创建第一份简历", target: "resume" }],
  progress: [],
  continuations: [],
  hasWorkspaceData: false,
}

describe("getActivationSteps", () => {
  it("returns ordered activation steps for a new account", () => {
    expect(getActivationSteps(emptyOverview)).toEqual([
      { label: "创建第一份简历", target: "resume", state: "current" },
      { label: "制定一项职业行动", target: "career", state: "next" },
      { label: "记录第一条投递", target: "applications", state: "next" },
    ])
  })

  it("marks completed work without hiding the remaining steps", () => {
    const state = { ...emptyOverview, draftCount: 1, openTaskCount: 0, applicationCount: 0, hasWorkspaceData: true }
    expect(getActivationSteps(state).map((step) => step.state)).toEqual(["done", "current", "next"])
  })
})
