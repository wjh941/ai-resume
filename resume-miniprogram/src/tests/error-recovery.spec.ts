import { beforeEach, describe, expect, it } from "vitest"

import { installGlobalErrorHandler } from "../services/client-error-reporting"

let reLaunchUrl = ""
let reLaunchCount = 0
let reportCount = 0
let pendingReLaunchComplete: (() => void) | undefined

beforeEach(() => {
  reLaunchUrl = ""
  reLaunchCount = 0
  reportCount = 0
  pendingReLaunchComplete = undefined
  ;(globalThis as typeof globalThis & { uni: unknown }).uni = {
    getStorageSync: () => "",
    request: async () => {
      reportCount += 1
      return { statusCode: 200, data: { code: "ok", data: {}, message: "" } }
    },
    reLaunch: (options: { url: string; complete?: () => void }) => {
      reLaunchCount += 1
      reLaunchUrl = options.url
      pendingReLaunchComplete = options.complete
    },
  }
})

function installedHandler() {
  const app = { config: {} as { errorHandler?: (reason: unknown, instance: unknown, info: string) => void } }
  installGlobalErrorHandler(app)
  return (reason: unknown, info: string) => app.config.errorHandler?.(reason, null, info)
}

describe("global error recovery", () => {
  it("routes rendering failures to the recovery page without exposing the error", () => {
    const handleError = installedHandler()

    handleError(new Error("Traceback secret"), "render")

    expect(reLaunchUrl).toBe("/pages/error/index")
  })

  it("deduplicates reports and skips re-navigation while one is in flight", () => {
    const handleError = installedHandler()

    handleError(new Error("boom"), "render")
    handleError(new Error("boom"), "render")
    handleError(new Error("boom"), "render")

    // 导航进行中不重复踢页；同签名错误 60 秒内只上报一次。
    expect(reLaunchCount).toBe(1)
    expect(reportCount).toBe(1)

    // 导航完成后，新的未处理错误仍能进入恢复页。
    pendingReLaunchComplete?.()
    handleError(new Error("boom"), "render")
    expect(reLaunchCount).toBe(2)
  })

  it("caps total reports per session and holds navigation while one is in flight", () => {
    const handleError = installedHandler()

    for (let index = 0; index < 8; index += 1) {
      handleError(new Error(`unique-error-${index}`), "render")
    }

    // 会话上报上限 5 条；首次导航未完成时，后续错误不再重复踢页。
    expect(reportCount).toBe(5)
    expect(reLaunchCount).toBe(1)
  })
})

