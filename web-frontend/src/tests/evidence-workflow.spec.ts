import { describe, expect, it } from "vitest"

import { removeEvidence, replaceEvidence, toggleVerified } from "../lib/evidence-workflow"
import type { EvidenceRecord } from "../lib/evidence"

const evidence = (id: string, verified = false): EvidenceRecord => ({ id, clientId: "u-1", kind: "project", title: "项目", context: "背景", actions: "行动", outcome: "结果", proofNote: "", verified, createdAt: "t1", updatedAt: "t1" })

describe("evidence workflow helpers", () => {
  it("replaces a saved evidence item after editing", () => {
    expect(replaceEvidence([evidence("e-1"), evidence("e-2")], evidence("e-1", true))[0].verified).toBe(true)
  })

  it("keeps verification changes immutable", () => {
    const original = evidence("e-1")
    expect(toggleVerified(original, true).verified).toBe(true)
    expect(original.verified).toBe(false)
  })

  it("removes only the confirmed evidence item", () => {
    expect(removeEvidence([evidence("e-1"), evidence("e-2")], "e-1").map((item) => item.id)).toEqual(["e-2"])
  })
})
