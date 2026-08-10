import { beforeEach, describe, expect, it } from "vitest"

import {
  getAssessmentQuestions,
  listAnnualInsights,
  submitAssessment,
} from "../services/assessment-api"

type CapturedRequest = { url: string; method?: string; data?: unknown }

const calls: CapturedRequest[] = []

beforeEach(() => {
  calls.length = 0
  ;(globalThis as typeof globalThis & { uni: unknown }).uni = {
    request: async (options: Record<string, unknown>) => {
      calls.push({
        url: String(options.url),
        method: String(options.method),
        data: options.data,
      })
      if (String(options.url).includes("/questions")) {
        return {
          statusCode: 200,
          data: {
            code: "ok",
            data: {
              notice: "Decision support only.",
              items: [
                {
                  key: "interest_investigative_1",
                  group: "interest",
                  dimension: "investigative",
                  title: "Analyze problems.",
                },
              ],
            },
          },
        }
      }
      if (String(options.url).includes("/annual-insights")) {
        return {
          statusCode: 200,
          data: {
            code: "ok",
            data: {
              items: [
                {
                  id: 1,
                  year: 2025,
                  scope: "national",
                  audience: "graduates",
                  category: "trend",
                  title: "Practice evidence",
                  content: "Keep project evidence.",
                  source_label: "Official archive",
                  publication_date: "2025-12-01",
                  confidence_note: "Local static summary.",
                  created_at: "2025-12-01T00:00:00+00:00",
                },
              ],
            },
          },
        }
      }
      return {
        statusCode: 200,
        data: {
          code: "ok",
          data: {
            client_id: "client-a",
            version: 1,
            answers: { interest_investigative_1: 5 },
            result: {
              top_interests: [
                {
                  key: "investigative",
                  label: "Analysis",
                  score: 5,
                  reason: "High response.",
                },
              ],
              work_style_summary: "Structured work.",
              strength_evidence: ["SQL evidence"],
              confidence_note: "Current signal.",
              answered_count: 5,
              action_plan: {
                seven_day: ["Review one project."],
                thirty_day: ["Ship one deliverable."],
                ninety_day: ["Review application feedback."],
              },
            },
            updated_at: "2025-12-01T00:00:00+00:00",
          },
        },
      }
    },
  }
})

describe("assessment API mapping", () => {
  it("maps questions and a submitted snake_case result", async () => {
    const questions = await getAssessmentQuestions()
    const saved = await submitAssessment("client-a", {
      interest_investigative_1: 5,
    })

    expect(questions.items[0]).toMatchObject({
      key: "interest_investigative_1",
      group: "interest",
    })
    expect(saved.clientId).toBe("client-a")
    expect(saved.result.topInterests[0].key).toBe("investigative")
    expect(saved.result.actionPlan.thirtyDay).toEqual(["Ship one deliverable."])
    expect(calls[1]).toMatchObject({
      method: "POST",
      data: {
        client_id: "client-a",
        answers: { interest_investigative_1: 5 },
      },
    })
  })

  it("maps annual insight provenance for source-labelled cards", async () => {
    const insights = await listAnnualInsights(2025)

    expect(insights[0]).toMatchObject({
      sourceLabel: "Official archive",
      publicationDate: "2025-12-01",
      confidenceNote: "Local static summary.",
    })
    expect(calls[0].url).toContain("/api/career/annual-insights?year=2025")
  })
})
