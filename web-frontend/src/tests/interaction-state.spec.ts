import { readFileSync } from "node:fs"

import { describe, expect, it } from "vitest"

import { canStartInteraction, pendingLabel } from "../lib/interaction-state"

describe("interaction state helpers", () => {
  it("blocks duplicate interactions while loading", () => {
    expect(canStartInteraction(true)).toBe(false)
    expect(canStartInteraction(false)).toBe(true)
  })

  it("selects the pending label without changing idle copy", () => {
    expect(pendingLabel(true, "保存", "保存中")).toBe("保存中")
    expect(pendingLabel(false, "保存", "保存中")).toBe("保存")
  })

  it("preflights professional job and insight modes against job matching capability", () => {
    const jobs = readFileSync(new URL("../views/JobsView.vue", import.meta.url), "utf8")
    const insights = readFileSync(new URL("../views/InsightsView.vue", import.meta.url), "utf8")
    for (const source of [jobs, insights]) {
      expect(source).toContain("CAPABILITIES_KEY")
      expect(source).toContain("isCapabilityEnabled")
      expect(source).toContain('"jobMatching"')
      expect(source).toContain("capabilityNotice")
      expect(source).toContain("retryCapabilities")
      expect(source).toContain("requestApi")
    }
    expect(jobs).toContain("emit('navigate', 'membership')")
    expect(insights).toContain("emit('navigate', 'membership')")
    expect(jobs).toContain('if (reportMode.value === "professional" && !jobMatchingEnabled.value)')
    expect(insights).toContain('if (reportMode.value === "professional" && !jobMatchingEnabled.value)')
  })

  it("uses the shared capability refresh state for job and insight retries", () => {
    const jobs = readFileSync(new URL("../views/JobsView.vue", import.meta.url), "utf8")
    const insights = readFileSync(new URL("../views/InsightsView.vue", import.meta.url), "utf8")

    for (const source of [jobs, insights]) {
      expect(source).not.toContain("capabilityOverride")
      expect(source).not.toContain("getCapabilities")
      expect(source).toContain("context.refresh()")
      expect(source).toContain("const capabilityRefreshing = computed(() => context.refreshing.value)")
      expect(source).toContain(":loading=\"capabilityRefreshing\"")
      expect(source).not.toContain(":loading=\"context.refreshing\"")
      expect(source).toContain("context.capabilities")
    }
  })

  it("keeps simplified payloads, loading duplicate guards, and backend errors intact", () => {
    const jobs = readFileSync(new URL("../views/JobsView.vue", import.meta.url), "utf8")
    const insights = readFileSync(new URL("../views/InsightsView.vue", import.meta.url), "utf8")
    expect(jobs).toContain('if (loading.value) return')
    expect(insights).toContain('if (loading.value) return')
    expect(jobs).toContain('report_mode: reportMode.value')
    expect(insights).toContain('report_mode: reportMode.value')
    expect(jobs).toContain('catch {')
    expect(insights).toContain('catch {')
    expect(jobs).toContain('<ErrorNotice v-if="error"')
    expect(insights).toContain('<ErrorNotice v-if="error"')
  })
})
