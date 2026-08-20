import { beforeEach, describe, expect, it } from "vitest"

import { installGlobalErrorHandler } from "../services/client-error-reporting"

let reLaunchUrl = ""

beforeEach(() => {
  reLaunchUrl = ""
  ;(globalThis as typeof globalThis & { uni: unknown }).uni = {
    getStorageSync: () => "",
    request: async () => ({ statusCode: 200, data: { code: "ok", data: {}, message: "" } }),
    reLaunch: (options: { url: string }) => { reLaunchUrl = options.url },
  }
})

describe("global error recovery", () => {
  it("routes rendering failures to the recovery page without exposing the error", () => {
    const app = { config: {} as { errorHandler?: (reason: unknown, instance: unknown, info: string) => void } }
    installGlobalErrorHandler(app)

    app.config.errorHandler?.(new Error("Traceback secret"), null, "render")

    expect(reLaunchUrl).toBe("/pages/error/index")
  })
})
