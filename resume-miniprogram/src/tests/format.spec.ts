import { describe, expect, it } from "vitest"

import { formatDateTime, splitIsoDateTime, toIsoDateTime, todayIsoDate } from "../utils/format"

describe("splitIsoDateTime", () => {
  it("splits an ISO datetime into picker values", () => {
    // +08:00 明确时区，避免测试依赖运行环境时区
    expect(splitIsoDateTime("2026-08-25T09:30:00+08:00")).toEqual({
      date: expect.stringMatching(/^\d{4}-\d{2}-\d{2}$/),
      time: expect.stringMatching(/^\d{2}:\d{2}$/),
    })
  })

  it("returns empty date and default time for blank or invalid values", () => {
    expect(splitIsoDateTime(null)).toEqual({ date: "", time: "09:00" })
    expect(splitIsoDateTime("")).toEqual({ date: "", time: "09:00" })
    expect(splitIsoDateTime("not-a-date")).toEqual({ date: "", time: "09:00" })
  })
})

describe("toIsoDateTime", () => {
  it("composes a backend-parseable ISO string", () => {
    expect(toIsoDateTime("2026-08-25", "09:30")).toBe("2026-08-25T09:30:00+08:00")
  })
})

describe("formatDateTime", () => {
  it("round-trips an ISO value through local formatting", () => {
    const value = "2026-08-25T09:30:00+08:00"
    const formatted = formatDateTime(value)
    const parsed = new Date(value)
    const pad = (n: number) => String(n).padStart(2, "0")
    expect(formatted).toBe(
      `${parsed.getFullYear()}-${pad(parsed.getMonth() + 1)}-${pad(parsed.getDate())} ${pad(parsed.getHours())}:${pad(parsed.getMinutes())}`,
    )
  })

  it("keeps the original text when unparseable and honors the fallback", () => {
    expect(formatDateTime("无法解析的时间")).toBe("无法解析的时间")
    expect(formatDateTime(null, "尚未设置")).toBe("尚未设置")
    expect(formatDateTime(undefined, "")).toBe("")
  })
})

describe("todayIsoDate", () => {
  it("returns a YYYY-MM-DD string", () => {
    expect(todayIsoDate()).toMatch(/^\d{4}-\d{2}-\d{2}$/)
  })
})
