import { beforeEach, describe, expect, it } from "vitest"

import { request } from "../services/http"
import { clearAuthSession, getAuthToken, setAuthSession } from "../stores/session"

const storage = new Map<string, unknown>()
let requestOptions: Record<string, unknown> | undefined
let responseStatus = 200
let modalCount = 0
let reLaunchUrl = ""

beforeEach(() => {
  storage.clear()
  requestOptions = undefined
  responseStatus = 200
  modalCount = 0
  reLaunchUrl = ""
  ;(globalThis as typeof globalThis & { uni: unknown }).uni = {
    getStorageSync: (key: string) => storage.get(key),
    setStorageSync: (key: string, value: unknown) => storage.set(key, value),
    removeStorageSync: (key: string) => storage.delete(key),
    request: async (options: Record<string, unknown>) => {
      requestOptions = options
      return {
        statusCode: responseStatus,
        data: responseStatus === 401
          ? { code: "unauthorized", data: {}, message: "Authentication is invalid or expired" }
          : { code: "ok", data: { ready: true }, message: "" },
      }
    },
    showModal: (options: { success?: (result: { confirm: boolean }) => void }) => {
      modalCount += 1
      options.success?.({ confirm: true })
    },
    reLaunch: (options: { url: string }) => { reLaunchUrl = options.url },
  }
  clearAuthSession()
})

describe("authenticated HTTP session", () => {
  it("adds the saved JWT to protected API requests", async () => {
    setAuthSession("signed-token", { userId: "user-1", phone: "13800138000" })

    await expect(request<{ ready: boolean }>("/api/template/list")).resolves.toEqual({ ready: true })

    expect(requestOptions?.header).toEqual({ Authorization: "Bearer signed-token" })
  })

  it("clears an expired token and routes the user back to login after a 401", async () => {
    setAuthSession("expired-token", { userId: "user-1", phone: "13800138000" })
    responseStatus = 401

    await expect(request("/api/template/list")).rejects.toThrow("Authentication is invalid or expired")

    expect(getAuthToken()).toBeNull()
    expect(modalCount).toBe(1)
    expect(reLaunchUrl).toBe("/pages/login/index")
  })
})
