import { beforeEach, describe, expect, it } from "vitest"

import { listApplications } from "../services/application-api"

const calls: Array<{ url: string; data?: unknown }> = []

beforeEach(() => {
  calls.length = 0
  ;(globalThis as typeof globalThis & { uni: unknown }).uni = {
    request: async (options: Record<string, unknown>) => {
      calls.push({ url: String(options.url), data: options.data })
      return {
        statusCode: 200,
        data: {
          code: "ok",
          data: {
            items: [{
              id: "application-1",
              client_id: "client-a",
              company: "[待确认]",
              role_name: "数据工程师",
              city: "上海",
              source: "官网",
              status: "interview",
              applied_at: "2026-08-12",
              next_action_at: "2026-08-15",
              interview_notes: "记录真实问题",
              draft_id: "draft-1",
              notes: "",
              created_at: "2026-08-12T00:00:00+00:00",
              updated_at: "2026-08-12T00:00:00+00:00",
            }],
          },
        },
      }
    },
  }
})

describe("application tracker API mapping", () => {
  it("maps snake_case records and forwards a status filter", async () => {
    const items = await listApplications("client-a", "interview")

    expect(items[0]).toMatchObject({
      id: "application-1",
      clientId: "client-a",
      roleName: "数据工程师",
      nextActionAt: "2026-08-15",
      interviewNotes: "记录真实问题",
    })
    expect(calls[0].url).toContain("client_id=client-a")
    expect(calls[0].url).toContain("status=interview")
  })
})
