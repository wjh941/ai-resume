import { describe, expect, it } from "vitest"

import { formatDateTime, templateLabel } from "../lib/format"

describe("formatDateTime", () => {
  it("round-trips an ISO value through local formatting", () => {
    const value = "2026-08-21T12:34:56.789000+00:00"
    const formatted = formatDateTime(value)
    const parsed = new Date(value)
    const pad = (n: number) => String(n).padStart(2, "0")
    expect(formatted).toBe(
      `${parsed.getFullYear()}-${pad(parsed.getMonth() + 1)}-${pad(parsed.getDate())} ${pad(parsed.getHours())}:${pad(parsed.getMinutes())}`,
    )
  })

  it("keeps unparseable text and honors the fallback", () => {
    expect(formatDateTime("not-a-date")).toBe("not-a-date")
    expect(formatDateTime(null, "时间待同步")).toBe("时间待同步")
    expect(formatDateTime(undefined)).toBe("")
  })
})

describe("templateLabel", () => {
  it("maps known template ids to Chinese labels", () => {
    expect(templateLabel("business")).toBe("商务模板")
    expect(templateLabel("technology")).toBe("技术模板")
    expect(templateLabel("graduate")).toBe("毕业生模板")
    expect(templateLabel("analytics")).toBe("分析模板")
  })

  it("keeps unknown ids and applies the fallback for blanks", () => {
    expect(templateLabel("future-template")).toBe("future-template")
    expect(templateLabel(null)).toBe("默认模板")
    expect(templateLabel("", "未选择")).toBe("未选择")
  })
})
