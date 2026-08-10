import { beforeEach, describe, expect, it } from "vitest"

import {
  checkResumeReadiness,
  getEvidenceSuggestions,
  listEvidence,
} from "../services/evidence-api"
import { createEmptyResume } from "../types/resume"

type CapturedRequest = { url: string; data?: unknown }

const calls: CapturedRequest[] = []

beforeEach(() => {
  calls.length = 0
  ;(globalThis as typeof globalThis & { uni: unknown }).uni = {
    request: async (options: Record<string, unknown>) => {
      const url = String(options.url)
      calls.push({ url, data: options.data })
      if (url.includes("/api/resume/evidence-suggestions")) {
        return {
          statusCode: 200,
          data: {
            code: "ok",
            data: {
              items: [{
                source_evidence_id: "evidence-1",
                source_title: "Data pipeline",
                target_section: "project",
                title: "Data pipeline",
                role: "Data Engineer related experience",
                description: "Action: built validation",
                risk_note: "",
              }],
            },
          },
        }
      }
      if (url.includes("/api/resume/readiness")) {
        return {
          statusCode: 200,
          data: {
            code: "ok",
            data: {
              ready: false,
              blocking_items: ["姓名"],
              warning_items: ["存在 [待确认] 内容"],
            },
          },
        }
      }
      return {
        statusCode: 200,
        data: {
          code: "ok",
          data: {
            items: [{
              id: "evidence-1",
              client_id: "client-a",
              kind: "project",
              title: "Data pipeline",
              context: "",
              actions: "Built validation",
              outcome: "",
              proof_note: "",
              verified: true,
              created_at: "2026-08-10T00:00:00+00:00",
              updated_at: "2026-08-10T00:00:00+00:00",
            }],
          },
        },
      }
    },
  }
})

describe("evidence API mapping", () => {
  it("maps snake_case evidence records from the backend", async () => {
    const evidence = await listEvidence("client-a")

    expect(evidence).toEqual([{
      id: "evidence-1",
      clientId: "client-a",
      kind: "project",
      title: "Data pipeline",
      context: "",
      actions: "Built validation",
      outcome: "",
      proofNote: "",
      verified: true,
      createdAt: "2026-08-10T00:00:00+00:00",
      updatedAt: "2026-08-10T00:00:00+00:00",
    }])
    expect(calls[0].url).toContain("/api/evidence?client_id=client-a")
  })

  it("maps suggestions and readiness results without mutating the resume", async () => {
    const resume = createEmptyResume()
    const [suggestions, report] = await Promise.all([
      getEvidenceSuggestions("client-a", "Data Engineer"),
      checkResumeReadiness(resume),
    ])

    expect(suggestions[0].sourceEvidenceId).toBe("evidence-1")
    expect(suggestions[0].targetSection).toBe("project")
    expect(report).toEqual({
      ready: false,
      blockingItems: ["姓名"],
      warningItems: ["存在 [待确认] 内容"],
    })
    expect(resume).toEqual(createEmptyResume())
  })
})
