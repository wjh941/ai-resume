import type { ApiEnvelope } from "../types/api"
import { clearAuthSession, getAuthToken } from "../stores/session"

const API_BASE_URL = import.meta.env.VITE_RESUME_API_URL || ""

const DEFAULT_ERROR_MESSAGE = "服务暂时不可用，请稍后重试。"
const RAW_ERROR_PATTERN = /traceback|stack trace|sqlite|sql error|internal server error|at \S+\.\w+ \(/i
// 按后端错误码给出统一中文提示；后端 message 已中文化时优先展示后端原文。
const CODE_ERROR_MESSAGES: Record<string, string> = {
  validation_error: "提交的信息格式有误，请检查后重试。",
  database_error: "数据处理暂时失败，请稍后重试。",
  not_found: "内容不存在或已被删除。",
  ai_not_configured: "AI 服务尚未配置，可先使用精简版功能。",
  ai_rate_limited: "AI 请求过于频繁，请稍后再试。",
  ai_timeout: "AI 生成耗时较长已中断，请稍后重试。",
  ai_unavailable: "AI 服务暂时不可用，请稍后重试。",
  ai_auth_failed: "AI 服务密钥无效，请联系管理员。",
  ai_balance_exhausted: "AI 服务额度不足，请联系管理员。",
  ai_invalid_response: "AI 返回内容格式异常，请稍后重试。",
  vip_required: "该功能需要升级会员后使用。",
}
const CONFIGURATION_HINTS: Array<[RegExp, string]> = [
  [/sms delivery is not configured/i, "当前环境未配置 SMS 登录，请联系服务管理员。"],
  [/wechat.*not configured|https whitelisted redirect/i, "微信登录需要已配置的 HTTPS 回调域名。"],
  [/payment channel.*not configured/i, "当前未配置支付服务，请选择其他可用方式。"],
  [/export could not be generated|export output path/i, "导出文件无法保存，请重试或联系服务支持。"],
]

const DEFAULT_TIMEOUT_MS = 15000
const GET_RETRY_DELAY_MS = 150

export type ApiErrorKind = "network" | "http" | "auth" | "business" | "unsupported"

/** 分类错误：network/服务器故障可重试或进入离线队列；business（参数、校验）重试无意义。 */
export class ApiRequestError extends Error {
  readonly kind: ApiErrorKind
  readonly statusCode?: number
  readonly code?: string

  constructor(kind: ApiErrorKind, message: string, options: { statusCode?: number; code?: string } = {}) {
    super(message)
    this.name = "ApiRequestError"
    this.kind = kind
    this.statusCode = options.statusCode
    this.code = options.code
  }
}

export function isRetryableApiError(reason: unknown): boolean {
  if (!(reason instanceof ApiRequestError)) return false
  return reason.kind === "network" || reason.kind === "http"
}

export function toUserMessage(reason: unknown, fallback = DEFAULT_ERROR_MESSAGE): string {
  if (reason instanceof ApiRequestError && reason.code) {
    const mapped = CODE_ERROR_MESSAGES[reason.code]
    if (mapped) {
      // 校验类错误的后端 detail 已是可执行的中文（如“仅支持 PDF 或 DOCX 格式的文件”），优先展示。
      const detail = reason.message || ""
      if (reason.code === "validation_error" && detail && detail.length <= 180 && !RAW_ERROR_PATTERN.test(detail) && /[\u4e00-\u9fff]/.test(detail)) {
        return detail
      }
      return mapped
    }
  }
  const message = reason instanceof Error ? reason.message : typeof reason === "string" ? reason : ""
  if (!message || message.length > 180 || RAW_ERROR_PATTERN.test(message)) return fallback
  return CONFIGURATION_HINTS.find(([pattern]) => pattern.test(message))?.[1] || message
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
    title: "登录状态已失效",
    content: "请重新登录后继续使用。",
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

export type QueryParams = Record<string, string | number | boolean | undefined | null>

/** 统一查询串构建：跳过 undefined/null/空串，值统一 encodeURIComponent，避免各调用点手拼遗漏编码。 */
export function buildQuery(params: QueryParams): string {
  const pairs = Object.entries(params)
    .filter(([, value]) => value !== undefined && value !== null && value !== "")
    .map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(String(value))}`)
  return pairs.length ? `?${pairs.join("&")}` : ""
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

function classifyResponse(statusCode: number | undefined, body: unknown): {
  kind: ApiErrorKind
  statusCode?: number
  code?: string
  message: string
} {
  const status = statusCode ?? 0
  const envelope = (body && typeof body === "object" && !Array.isArray(body)
    ? body as Partial<ApiEnvelope<unknown>>
    : null)
  const message = envelope ? toUserMessage(envelope.message) : DEFAULT_ERROR_MESSAGE

  if (status === 401) return { kind: "auth", statusCode: status, code: envelope?.code, message }
  if (status >= 500) return { kind: "http", statusCode: status, code: envelope?.code, message }
  if (status >= 400) {
    // 后端业务信封（validation_error、ai_not_configured 等）按业务错误分类，提示可读原因。
    return { kind: "business", statusCode: status, code: envelope?.code, message: message || `请求失败（${status}）` }
  }
  return { kind: "http", statusCode: status, message }
}

async function requestOnce<T>(
  requestFn: UniRequest,
  path: string,
  method: string,
  data?: unknown,
  timeoutMs = DEFAULT_TIMEOUT_MS,
): Promise<T> {
  const token = getAuthToken()
  let response: { statusCode?: number; data: ApiEnvelope<unknown> | unknown }
  try {
    response = await requestFn({
      url: apiUrl(path),
      method,
      data,
      timeout: timeoutMs,
      header: token ? { Authorization: `Bearer ${token}` } : {},
    })
  } catch (error) {
    // 传输层失败（断网、超时、DNS 等）：可重试，也可进入离线队列。
    throw new ApiRequestError("network", toUserMessage(error))
  }

  const status = response.statusCode ?? 0
  if (status >= 400) {
    const classified = classifyResponse(status, response.data)
    if (classified.kind === "auth") {
      clearAuthSession()
      promptLogin()
    }
    throw new ApiRequestError(classified.kind, classified.message, {
      statusCode: classified.statusCode,
      code: classified.code,
    })
  }

  const body = response.data
  if (!body || typeof body !== "object" || Array.isArray(body)) {
    // 网关/代理可能返回 HTML 错误页等非 JSON 内容。
    throw new ApiRequestError("http", DEFAULT_ERROR_MESSAGE, { statusCode: status })
  }
  const envelope = body as Partial<ApiEnvelope<T>>
  if (envelope.code !== "ok") {
    throw new ApiRequestError("business", toUserMessage(envelope.message) || "请求失败", {
      statusCode: status,
      code: envelope.code,
    })
  }
  return envelope.data as T
}

export const SLOW_REQUEST_TIMEOUT_MS = 120_000

export async function request<T>(
  path: string,
  method = "GET",
  data?: unknown,
  options?: { query?: QueryParams; timeoutMs?: number },
): Promise<T> {
  const requestFn = (globalThis as typeof globalThis & { uni?: { request?: UniRequest } }).uni?.request
  if (!requestFn) throw new ApiRequestError("unsupported", "当前运行环境不支持网络请求")
  const fullPath = options?.query ? `${path}${buildQuery(options.query)}` : path
  try {
    return await requestOnce<T>(requestFn, fullPath, method, data, options?.timeoutMs)
  } catch (error) {
    // 仅 GET 幂等请求自动重试一次，覆盖瞬时抖动；POST/PUT/DELETE 不重试。
    if (method === "GET" && isRetryableApiError(error)) {
      await sleep(GET_RETRY_DELAY_MS)
      return requestOnce<T>(requestFn, fullPath, method, data, options?.timeoutMs)
    }
    throw error
  }
}
