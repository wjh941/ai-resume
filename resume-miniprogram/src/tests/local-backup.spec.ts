import { describe, expect, it } from "vitest"

import { createEmptyDraft } from "../types/resume"
import { parseLocalBackup, serializeLocalBackup } from "../utils/local-backup"

describe("local backup", () => {
  it("round-trips resume and career planner state without sharing references", () => {
    const draft = createEmptyDraft()
    draft.resume.basic.name = "Backup user"
    const serialized = serializeLocalBackup(
      { activeJob: null, draft },
      {
        profile: null,
        result: null,
        selectedTier: "stable",
        selectedRole: null,
        comparisonRoleNames: ["Data Engineer"],
        weeklyTarget: null,
      },
    )

    const backup = parseLocalBackup(serialized)
    draft.resume.basic.name = "Changed after export"

    expect(backup.version).toBe(1)
    expect(backup.resume.draft.resume.basic.name).toBe("Backup user")
    expect(backup.career.comparisonRoleNames).toEqual(["Data Engineer"])
  })

  it("rejects incompatible or malformed backup files", () => {
    expect(() => parseLocalBackup("not-json")).toThrow("backup")
    expect(() => parseLocalBackup(JSON.stringify({ version: 2 }))).toThrow("backup")
  })
})
