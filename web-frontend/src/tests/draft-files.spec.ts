import { beforeEach, describe, expect, it, vi } from "vitest"

import type { ResumePayload } from "../lib/drafts"

vi.mock("../lib/api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../lib/api")>()
  return {
    ...actual,
    requestApi: vi.fn(),
    downloadApi: vi.fn(),
    uploadApi: vi.fn(),
  }
})

import { downloadApi, requestApi, SLOW_REQUEST_TIMEOUT_MS, uploadApi } from "../lib/api"
import { exportDraft, importResumeFile } from "../lib/drafts"

const requestMock = vi.mocked(requestApi)
const downloadMock = vi.mocked(downloadApi)
const uploadMock = vi.mocked(uploadApi)

beforeEach(() => {
  requestMock.mockReset()
  downloadMock.mockReset()
  uploadMock.mockReset()
})

describe("resume export", () => {
  it("requests the export endpoint, then downloads the generated file with the slow timeout", async () => {
    requestMock.mockResolvedValueOnce({ filename: "张三-数据分析师.docx", download_url: "/downloads/abc123", expires_at: "2026-01-01T00:00:00Z" })
    downloadMock.mockResolvedValueOnce(new Blob(["docx-bytes"]))

    const result = await exportDraft("word", "draft-1")

    expect(result.filename).toBe("张三-数据分析师.docx")
    expect(result.blob).toBeInstanceOf(Blob)
    expect(requestMock).toHaveBeenCalledWith("/api/export/word", {
      method: "POST",
      body: JSON.stringify({ draft_id: "draft-1" }),
    }, { timeoutMs: SLOW_REQUEST_TIMEOUT_MS })
    expect(downloadMock).toHaveBeenCalledWith("/downloads/abc123", {}, { timeoutMs: SLOW_REQUEST_TIMEOUT_MS })
  })

  it("maps the pdf format onto the pdf endpoint", async () => {
    requestMock.mockResolvedValueOnce({ filename: "张三-数据分析师.pdf", download_url: "/downloads/def456", expires_at: "2026-01-01T00:00:00Z" })
    downloadMock.mockResolvedValueOnce(new Blob(["%PDF"]))

    await exportDraft("pdf", "draft-2")

    expect(requestMock.mock.calls[0]?.[0]).toBe("/api/export/pdf")
  })
})

describe("resume import", () => {
  const parsedResume = {
    version: 1 as const,
    basic: { name: "张三", phone: "13800138000", email: "z@example.com", city: "北京" },
    job: { target_role: "数据分析师", expected_salary: "", employment_type: "" },
    education: [],
    employment: [],
    projects: [],
    skills: { skills: ["SQL"], certificates: [] },
    self_evaluation: "",
    section_visibility: {
      basic: true, job: true, education: true, employment: true,
      projects: true, skills: true, self_evaluation: true,
    },
  }

  it("uploads the file to the draft import endpoint and maps the parsed resume to camelCase", async () => {
    uploadMock.mockResolvedValueOnce({
      id: "import-1",
      status: "ready",
      original_filename: "旧简历.pdf",
      parsed_resume: parsedResume,
    })
    const file = new File(["pdf-bytes"], "旧简历.pdf", { type: "application/pdf" })

    const preview = await importResumeFile("draft-9", file)

    expect(uploadMock).toHaveBeenCalledWith("/api/draft/draft-9/imports", file, "file", { timeoutMs: SLOW_REQUEST_TIMEOUT_MS })
    expect(preview.originalFilename).toBe("旧简历.pdf")
    expect(preview.parsedResume.job.targetRole).toBe("数据分析师")
    expect(preview.parsedResume.skills.skills).toEqual(["SQL"])
  })
})
