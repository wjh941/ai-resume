import { apiUrl } from "./http"
import { getAuthToken } from "../stores/session"

type ErrorHandlerApp = {
  config: {
    errorHandler?: (reason: unknown, instance: unknown, info: string) => void
  }
}

function safeMessage(reason: unknown): string {
  const message = reason instanceof Error ? reason.message : String(reason || "")
  return /traceback|stack trace|sqlite|sql error/i.test(message) ? "页面发生异常" : message.slice(0, 500) || "页面发生异常"
}

export async function reportClientError(payload: { message: string; component: string }): Promise<void> {
  const request = (globalThis as typeof globalThis & { uni?: { request?: (options: Record<string, unknown>) => Promise<unknown> } }).uni?.request
  if (!request) return
  try {
    await request({
      url: apiUrl("/api/system/client-errors"),
      method: "POST",
      data: payload,
      header: getAuthToken() ? { Authorization: `Bearer ${getAuthToken()}` } : {},
    })
  } catch {
    // Error reporting must never trigger another user-facing failure.
  }
}

export function installGlobalErrorHandler(app: ErrorHandlerApp): void {
  app.config.errorHandler = (reason, _instance, info) => {
    void reportClientError({ message: safeMessage(reason), component: info })
    ;(globalThis as typeof globalThis & { uni?: { reLaunch?: (options: { url: string }) => void } }).uni?.reLaunch?.({ url: "/pages/error/index" })
  }
}
