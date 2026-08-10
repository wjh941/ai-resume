import { beforeEach, describe, expect, it } from "vitest"

import { listKnowledgeSources, startOfficialKnowledgeSync } from "../services/knowledge-sync-api"

const calls: string[] = []

beforeEach(() => {
  calls.length = 0
  ;(globalThis as typeof globalThis & { uni: unknown }).uni = {
    request: async (options: Record<string, unknown>) => {
      calls.push(String(options.url))
      if (String(options.url).endsWith("/api/knowledgebase/sources")) {
        return {
          statusCode: 200,
          data: {
            code: "ok",
            data: {
              items: [{
                source_key: "moe-major-directory",
                display_name: "教育部高校专业目录",
                direct_url: null,
                allowed_hosts: ["moe.gov.cn"],
                file_format: "json",
                parser_kind: "major",
                enabled: false,
                disabled_reason: "暂无直链",
              }],
            },
          },
        }
      }
      return {
        statusCode: 200,
        data: {
          code: "ok",
          data: {
            run_id: 8,
            mode: "official",
            status: "completed",
            added_roles: 12,
            added_majors: 8,
            skipped_rows: 2,
            errors: [],
          },
        },
      }
    },
  }
})

describe("knowledge sync API mapping", () => {
  it("maps source status without exposing local cache data", async () => {
    const sources = await listKnowledgeSources()

    expect(sources[0]).toMatchObject({
      sourceKey: "moe-major-directory",
      parserKind: "major",
      enabled: false,
    })
    expect(calls[0]).toContain("/api/knowledgebase/sources")
  })

  it("maps the one-click official sync summary", async () => {
    const summary = await startOfficialKnowledgeSync()

    expect(summary).toMatchObject({
      runId: 8,
      addedRoles: 12,
      addedMajors: 8,
      skippedRows: 2,
    })
    expect(calls[0]).toContain("/api/knowledgebase/sync/official")
  })
})
