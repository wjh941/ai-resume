import { describe, expect, it } from "vitest"

import { decideTemplateSelection } from "../utils/template-selection"

describe("template readiness decision", () => {
  it("blocks missing required resume information before template navigation", () => {
    expect(
      decideTemplateSelection({
        ready: false,
        blockingItems: ["姓名"],
        warningItems: [],
      }),
    ).toEqual({ blocked: true, requiresWarningConfirmation: false })
  })

  it("requires an explicit confirmation for warnings without blocking items", () => {
    expect(
      decideTemplateSelection({
        ready: true,
        blockingItems: [],
        warningItems: ["项目经历含有 [待确认] 内容"],
      }),
    ).toEqual({ blocked: false, requiresWarningConfirmation: true })
  })
})
