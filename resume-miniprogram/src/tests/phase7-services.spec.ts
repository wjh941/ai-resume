import { beforeEach, describe, expect, it } from "vitest"

import { requestAccountDataExport, requestAccountPrivacyDetails } from "../services/account-api"
import { getJobMatchSubscriptionSettings, setJobMatchSubscriptionSettings } from "../services/job-collection-api"

const calls: Array<{ url: string; method?: string; data?: unknown }> = []

beforeEach(() => {
  calls.length = 0
  ;(globalThis as typeof globalThis & { uni: unknown }).uni = {
    request: async (options: { url: string; method?: string; data?: unknown }) => {
      calls.push(options)
      const dataByPath: Record<string, unknown> = {
        "/api/account/data-scope": {
          categories: ["resume_drafts"],
          retention_note: "Anonymized after deletion.",
          privacy_policy_hint: "Export before deletion.",
        },
        "/api/account/data-export": {
          status: "ready", message: "Your data export is ready.", download_url: "/api/account/data-export",
        },
        "/api/job-collection/subscription": {
          enabled: true, match_filter: "Shanghai, remote", last_notify_at: "2026-08-19T00:00:00+00:00",
        },
      }
      return { statusCode: 200, data: { code: "ok", data: dataByPath[options.url], message: "" } }
    },
  }
})

describe("Phase7 lifecycle service adapters", () => {
  it("maps the privacy policy hint and export download URL", async () => {
    await expect(requestAccountPrivacyDetails()).resolves.toEqual({
      categories: ["resume_drafts"],
      retentionNote: "Anonymized after deletion.",
      privacyPolicyHint: "Export before deletion.",
    })
    await expect(requestAccountDataExport()).resolves.toEqual({
      status: "ready", message: "Your data export is ready.", downloadUrl: "/api/account/data-export",
    })
  })

  it("maps and persists the expanded job subscription settings", async () => {
    await expect(getJobMatchSubscriptionSettings()).resolves.toEqual({
      enabled: true, matchFilter: "Shanghai, remote", lastNotifyAt: "2026-08-19T00:00:00+00:00",
    })
    await expect(setJobMatchSubscriptionSettings(true, "Shanghai, remote")).resolves.toMatchObject({
      enabled: true, matchFilter: "Shanghai, remote",
    })
    expect(calls.at(-1)).toMatchObject({
      url: "/api/job-collection/subscription", method: "PUT", data: { enabled: true, match_filter: "Shanghai, remote" },
    })
  })
})
