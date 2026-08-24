import { existsSync } from "node:fs"
import { fileURLToPath } from "node:url"
import { describe, expect, it } from "vitest"

describe("isExpandableText", () => {
  it("uses the configured threshold after trimming", async () => {
    const moduleUrl = new URL("../lib/expandable-text.ts", import.meta.url)

    expect(existsSync(fileURLToPath(moduleUrl))).toBe(true)
    const { isExpandableText } = await import(moduleUrl.href)

    expect(isExpandableText(" 数据分析师 ", 18)).toBe(false)
    expect(isExpandableText("岗".repeat(19), 18)).toBe(true)
    expect(isExpandableText("x".repeat(96), 96)).toBe(false)
    expect(isExpandableText("x".repeat(97), 96)).toBe(true)
  })
})
