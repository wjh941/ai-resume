import { ApiRequestError, ApiTimeoutError } from "./api"

function isNetworkError(reason: unknown): boolean {
  if (reason instanceof ApiRequestError && reason.status === 0) return true
  if (reason instanceof TypeError) return true
  return reason instanceof Error && /failed to fetch|fetch failed|network|load failed/i.test(reason.message)
}

export function getApiErrorMessage(reason: unknown, fallback: string): string {
  if (reason instanceof ApiTimeoutError) return "请求超时，请稍后重试"
  if (reason instanceof ApiRequestError && reason.status === 401) return "登录已过期，请重新登录后继续"
  if (reason instanceof ApiRequestError && reason.status === 403) return "当前功能暂不可用，请查看会员权益"
  if (isNetworkError(reason)) return "网络连接失败，请检查网络后重试"
  return fallback
}
