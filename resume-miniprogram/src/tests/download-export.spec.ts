import { beforeEach, describe, expect, it } from "vitest"

import { requestPdfExport, requestWordExport } from "../services/export-api"
import { downloadExport } from "../utils/download-export"

const requestCalls: Array<{ url: string; method?: string; data?: unknown }> = []
const downloadCalls: Array<{ url: string }> = []
const saveCalls: Array<{ tempFilePath: string }> = []
const clipboardCalls: string[] = []
const toastCalls: string[] = []

beforeEach(() => {
  requestCalls.length = 0
  downloadCalls.length = 0
  saveCalls.length = 0
  clipboardCalls.length = 0
  toastCalls.length = 0
  ;(globalThis as typeof globalThis & { window?: unknown }).window = undefined
  ;(globalThis as typeof globalThis & { uni: Record<string, unknown> }).uni = {
    request: async (options: Record<string, unknown>) => {
      requestCalls.push({
        url: String(options.url),
        method: String(options.method),
        data: options.data,
      })
      return {
        statusCode: 200,
        data: {
          code: "ok",
          data: {
            filename: "resume.docx",
            download_url: "/downloads/token",
            expires_at: "2026-08-13T01:00:00Z",
          },
        },
      }
    },
    setClipboardData: ({ data }: { data: string }) => {
      clipboardCalls.push(data)
    },
    showToast: ({ title }: { title: string }) => {
      toastCalls.push(title)
    },
  }
})

describe("export requests", () => {
  it("requests a Word export for the saved draft", async () => {
    await requestWordExport("client-a", "draft-1")

    expect(requestCalls[0]).toMatchObject({
      url: "/api/export/word",
      method: "POST",
      data: { client_id: "client-a", draft_id: "draft-1" },
    })
  })

  it("requests a PDF export for the saved draft", async () => {
    const result = await requestPdfExport("client-a", "draft-1")

    expect(requestCalls[0].url).toBe("/api/export/pdf")
    expect(result).toEqual({
      filename: "resume.docx",
      downloadUrl: "/downloads/token",
      expiresAt: "2026-08-13T01:00:00Z",
    })
  })
})

describe("downloadExport", () => {
  it("opens the resolved download URL on H5", async () => {
    const opened: string[] = []
    ;(globalThis as typeof globalThis & { window: { open: (...args: string[]) => void } }).window = {
      open: (url: string) => { opened.push(url) },
    }

    await downloadExport("/downloads/token", "resume.docx", "h5")

    expect(opened[0]).toContain("/downloads/token")
    expect(clipboardCalls).toHaveLength(0)
  })

  it("downloads then saves a file on mp-weixin", async () => {
    const uni = (globalThis as typeof globalThis & { uni: Record<string, unknown> }).uni
    uni.downloadFile = (options: { url: string; success: (result: { tempFilePath: string }) => void }) => {
      downloadCalls.push({ url: options.url })
      options.success({ tempFilePath: "wxfile://resume.docx" })
    }
    uni.saveFile = (options: { tempFilePath: string; success: (result: unknown) => void }) => {
      saveCalls.push({ tempFilePath: options.tempFilePath })
      options.success({})
    }

    await downloadExport("/downloads/token", "resume.docx", "mp-weixin")

    expect(downloadCalls).toHaveLength(1)
    expect(saveCalls).toHaveLength(1)
    expect(saveCalls[0].tempFilePath).toBe("wxfile://resume.docx")
    expect(downloadCalls[0].url).toContain("filename=resume.docx")
  })

  it("falls back when mp-weixin reports a failed HTTP status", async () => {
    const uni = (globalThis as typeof globalThis & { uni: Record<string, unknown> }).uni
    uni.downloadFile = (options: {
      url: string
      success: (result: { tempFilePath: string; statusCode: number }) => void
    }) => {
      downloadCalls.push({ url: options.url })
      options.success({ tempFilePath: "wxfile://error.html", statusCode: 500 })
    }
    uni.saveFile = (options: { tempFilePath: string; success: (result: unknown) => void }) => {
      saveCalls.push({ tempFilePath: options.tempFilePath })
      options.success({})
    }

    await downloadExport("/downloads/token?expires=1#fragment", "resume final.docx", "mp-weixin")

    expect(saveCalls).toHaveLength(0)
    expect(clipboardCalls[0]).toContain("filename=resume%20final.docx")
    expect(toastCalls[0]).toContain("filename=resume%20final.docx")
  })

  it("copies a readable fallback URL when a platform download fails", async () => {
    const uni = (globalThis as typeof globalThis & { uni: Record<string, unknown> }).uni
    uni.downloadFile = (options: { fail: (reason: unknown) => void }) => options.fail(new Error("offline"))

    await downloadExport("/downloads/token", "resume.docx", "mp-weixin")

    expect(clipboardCalls[0]).toContain("/downloads/token")
    expect(toastCalls[0]).toContain("下载链接")
  })
})
