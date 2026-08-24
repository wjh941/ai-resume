import { describe, expect, it } from "vitest"
import { readFileSync } from "node:fs"

import { runWithLoading } from "../utils/async-state"

describe("runWithLoading", () => {
  it("clears loading after resolve", async () => {
    const states: boolean[] = []
    await expect(runWithLoading((value) => states.push(value), async () => "ok")).resolves.toBe("ok")
    expect(states).toEqual([true, false])
  })

  it("clears loading after rejection", async () => {
    const states: boolean[] = []
    await expect(runWithLoading((value) => states.push(value), async () => { throw new Error("offline") }))
      .rejects.toThrow("offline")
    expect(states).toEqual([true, false])
  })

  it("clears loading after an abort-shaped rejection", async () => {
    const states: boolean[] = []
    await expect(runWithLoading((value) => states.push(value), async () => {
      throw new DOMException("The operation was aborted", "AbortError")
    })).rejects.toMatchObject({ name: "AbortError" })
    expect(states).toEqual([true, false])
  })

  it("keeps existing H5 async controls disabled while pending", () => {
    const assessment = readFileSync(new URL("../pages/career-assessment/index.vue", import.meta.url), "utf8")
    const applications = readFileSync(new URL("../pages/applications/index.vue", import.meta.url), "utf8")
    const planner = readFileSync(new URL("../pages/career-planner/index.vue", import.meta.url), "utf8")
    const membership = readFileSync(new URL("../pages/membership/index.vue", import.meta.url), "utf8")
    const privacy = readFileSync(new URL("../pages/privacy/index.vue", import.meta.url), "utf8")
    const editor = readFileSync(new URL("../pages/resume-editor/index.vue", import.meta.url), "utf8")
    const jobSearch = readFileSync(new URL("../pages/job-search/index.vue", import.meta.url), "utf8")
    const jobCollection = readFileSync(new URL("../pages/job-collection/index.vue", import.meta.url), "utf8")
    const operatorKnowledge = readFileSync(new URL("../pages/operator-knowledge/index.vue", import.meta.url), "utf8")
    expect(assessment).toContain(':loading="submitting" :disabled="submitting"')
    expect(assessment).toContain("<LoadingSpinner")
    expect(applications).toContain("const timelineSaving = ref(false)")
    expect(applications).toContain("const reminderSaving = ref(false)")
    expect(applications).toContain("const pendingDeleteId = ref(\"\")")
    expect(applications).toContain(':loading="timelineSaving" :disabled="timelineSaving"')
    expect(applications).toContain(':loading="reminderSaving" :disabled="reminderSaving"')
    expect(planner).toContain(':loading="taskSaving" :disabled="taskSaving"')
    expect(planner).toContain(':loading="loading" :disabled="loading"')
    expect(membership).toContain(':loading="purchasing" :disabled="purchasing"')
    expect(membership).toContain("<LoadingSpinner")
    expect(privacy).toContain(':loading="backupBusy" :disabled="backupBusy"')
    expect(editor).toContain(':loading="importLoading" :disabled="importLoading || Boolean(exporting)"')
    expect(editor).toContain(':loading="versionLoading" :disabled="versionLoading || Boolean(exporting)"')
    expect(jobSearch).toContain(':loading="marketSearchLoading" :disabled="marketSearchLoading"')
    expect(jobSearch).toContain(':loading="reviewLoading" :disabled="reviewLoading || pdfLoading"')
    expect(jobSearch).toContain(':loading="adviceLoading" :disabled="adviceLoading"')
    expect(jobCollection).toContain(':loading="saving" :disabled="saving"')
    expect(operatorKnowledge).toContain('const versionsLoading = ref("")')
    expect(operatorKnowledge).toContain("<LoadingSpinner")
    expect(operatorKnowledge).toContain(':loading="loading" :disabled="loading || Boolean(versionsLoading) || restoringVersion !== null"')
    expect(operatorKnowledge).toContain(':loading="versionsLoading === item.id"')
    expect(operatorKnowledge).toContain(':loading="restoringVersion === version.version"')
  })
})
