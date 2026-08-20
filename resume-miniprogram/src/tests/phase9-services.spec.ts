import { beforeEach, describe, expect, it } from "vitest"

import { createApplicationTimelineEvent, listApplications } from "../services/application-api"
import { createResumeVersion, listResumeVersions } from "../services/resume-version-api"
import { generateCareerTasks, updateCareerTask } from "../services/career-task-api"

const calls: Array<{ url: string; method: string; data?: unknown }> = []

beforeEach(() => {
  calls.length = 0
  ;(globalThis as typeof globalThis & { uni: unknown }).uni = {
    request: async (options: { url: string; method?: string; data?: unknown }) => {
      calls.push({ url: options.url, method: options.method || "GET", data: options.data })
      if (options.url.includes("/api/applications")) {
        return {
          statusCode: 200,
          data: { code: "ok", data: {
            items: [{
              id: "application-1", client_id: "client-a", company: "示例公司", role_name: "数据工程师",
              city: "上海", source: "官网", status: "interview", applied_at: null, next_action_at: null,
              interview_notes: "", draft_id: null, notes: "", contact_info: "张老师", attachment_ref: "材料.zip",
              next_interview_at: "2026-08-25T10:00:00+00:00", timeline: [],
              created_at: "2026-08-20T00:00:00+00:00", updated_at: "2026-08-20T00:00:00+00:00",
            }],
          } },
        }
      }
      if (options.url.includes("/versions")) {
        return { statusCode: 200, data: { code: "ok", data: { items: [{ id: "version-1", note: "投递前", is_active: true, created_at: "2026-08-20T00:00:00+00:00" }] } } }
      }
      return { statusCode: 200, data: { code: "ok", data: { items: [{ id: "task-1", plan_id: "current", title: "整理作品集", description: "", due_date: null, status: "pending", link_to_application_id: null, link_to_evidence_id: null, created_at: "2026-08-20T00:00:00+00:00", updated_at: "2026-08-20T00:00:00+00:00" }] } } }
    },
  }
})

describe("Phase9 service mappings", () => {
  it("maps delivery fields and forwards an interview date filter", async () => {
    const [application] = await listApplications("client-a", undefined, "2026-08-25")
    await createApplicationTimelineEvent("application-1", {
      title: "一面", description: "记录重点", occurredAt: "2026-08-20T10:00:00+00:00",
    })

    expect(application.contactInfo).toBe("张老师")
    expect(application.nextInterviewAt).toBe("2026-08-25T10:00:00+00:00")
    expect(calls[0].url).toContain("interview_date=2026-08-25")
    expect(calls[1]).toMatchObject({ url: expect.stringContaining("/api/applications/application-1/timeline"), method: "POST" })
  })

  it("creates and lists named resume snapshots", async () => {
    await createResumeVersion("draft-1", "投递前")
    const versions = await listResumeVersions("draft-1")

    expect(calls[0]).toMatchObject({ url: expect.stringContaining("/api/draft/draft-1/versions"), method: "POST", data: { note: "投递前" } })
    expect(versions[0]).toMatchObject({ id: "version-1", isActive: true })
  })

  it("generates and updates career tasks", async () => {
    const tasks = await generateCareerTasks("current", { sevenDay: ["整理作品集"], thirtyDay: [], ninetyDay: [] })
    await updateCareerTask(tasks[0].id, { status: "completed", dueDate: "2026-08-30" })

    expect(calls[0]).toMatchObject({ url: expect.stringContaining("/api/career/tasks/generate"), method: "POST" })
    expect(calls[1]).toMatchObject({ url: expect.stringContaining("/api/career/tasks/task-1"), method: "PATCH" })
  })
})
