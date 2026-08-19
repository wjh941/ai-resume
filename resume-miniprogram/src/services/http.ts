import type { ApiEnvelope } from "../types/api"
import { clearAuthSession, getAuthToken } from "../stores/session"

const API_BASE_URL = import.meta.env.VITE_RESUME_API_URL || ""

const DEFAULT_ERROR_MESSAGE = "The service is temporarily unavailable. Please try again later."
const RAW_ERROR_PATTERN = /traceback|stack trace|sqlite|sql error|internal server error|at \S+\.\w+ \(/i

export function toUserMessage(reason: unknown, fallback = DEFAULT_ERROR_MESSAGE): string {
  const message = reason instanceof Error ? reason.message : typeof reason === "string" ? reason : ""
  if (!message || message.length > 180 || RAW_ERROR_PATTERN.test(message)) return fallback
  return message
}

export function resolveApiUrl(
  configuredBaseUrl: string,
  platform: string | undefined,
  path: string,
): string {
  const normalizedBaseUrl = configuredBaseUrl.trim().replace(/\/+$/, "")
  if (normalizedBaseUrl) {
    return `${normalizedBaseUrl}${path}`
  }

  if (!platform || platform === "h5") {
    return path
  }

  throw new Error(
    "未配置小程序后端地址，请在 .env.local 中设置 VITE_RESUME_API_URL。",
  )
}

type UniRequest = (options: Record<string, unknown>) => Promise<{ statusCode?: number; data: ApiEnvelope<unknown> | unknown }>

type LoginPromptUni = {
  showModal?: (options: {
    title: string
    content: string
    showCancel?: boolean
    success?: (result: { confirm: boolean }) => void
    fail?: () => void
  }) => void
  reLaunch?: (options: { url: string }) => void
}

let loginPromptActive = false

function promptLogin(): void {
  if (loginPromptActive) return
  loginPromptActive = true
  const uni = (globalThis as typeof globalThis & { uni?: LoginPromptUni }).uni
  if (!uni?.showModal) {
    loginPromptActive = false
    return
  }
  uni.showModal({
    title: "Login required",
    content: "Your session has expired. Please sign in again.",
    showCancel: false,
    success: () => {
      loginPromptActive = false
      uni.reLaunch?.({ url: "/pages/login/index" })
    },
    fail: () => { loginPromptActive = false },
  })
}

export function apiUrl(path: string): string {
  return resolveApiUrl(API_BASE_URL, process.env.UNI_PLATFORM, path)
}

export async function request<T>(path: string, method = "GET", data?: unknown): Promise<T> {
  const requestFn = (globalThis as typeof globalThis & { uni?: { request?: UniRequest } }).uni?.request
  if (!requestFn) throw new Error("当前运行环境不支持网络请求")
  const token = getAuthToken()
  const response = await requestFn({
    url: apiUrl(path),
    method,
    data,
    header: token ? { Authorization: `Bearer ${token}` } : {},
  })
  const envelope = response.data as Partial<ApiEnvelope<T>>
  envelope.message = toUserMessage(envelope.message)
  if (response.statusCode && response.statusCode >= 400) {
    if (response.statusCode === 401) {
      clearAuthSession()
      promptLogin()
    }
    throw new Error(envelope.message || `请求失败（${response.statusCode}）`)
  }
  if (envelope.code !== "ok") throw new Error(envelope.message || "请求失败")
  return envelope.data as T
}
