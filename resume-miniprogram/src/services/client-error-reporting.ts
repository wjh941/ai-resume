import { apiUrl } from "./http"
import { getAuthToken } from "../stores/session"

type ErrorHandlerApp = {
  config: {
    errorHandler?: (...args: any[]) => void
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

// 会话级去重与阈值（随每次 install 重置）：同签名错误 60 秒内只上报一次，
// 整个会话最多上报 5 条，避免一次渲染抖动造成上报风暴；错误页跳转同样去重，
// 防止反复 reLaunch 把用户踢出当前页。
const DUPLICATE_WINDOW_MS = 60_000
const MAX_REPORTS_PER_SESSION = 5

export function installGlobalErrorHandler(app: ErrorHandlerApp): void {
  let lastErrorSignature = ""
  let lastReportedAt = 0
  let sessionReportCount = 0
  let navigatingToErrorPage = false

  app.config.errorHandler = (reason, _instance, info) => {
    const message = safeMessage(reason)
    const now = Date.now()
    const signature = `${info}:${message}`
    const duplicated = signature === lastErrorSignature && now - lastReportedAt < DUPLICATE_WINDOW_MS
    lastErrorSignature = signature
    lastReportedAt = now
    if (!duplicated && sessionReportCount < MAX_REPORTS_PER_SESSION) {
      sessionReportCount += 1
      void reportClientError({ message, component: info })
    }
    if (navigatingToErrorPage) return
    navigatingToErrorPage = true
    const uni = (globalThis as typeof globalThis & { uni?: { reLaunch?: (options: { url: string; complete?: () => void }) => void } }).uni
    uni?.reLaunch?.({
      url: "/pages/error/index",
      complete: () => { navigatingToErrorPage = false },
    })
  }
}
