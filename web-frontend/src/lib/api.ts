import { clearSession, readSession } from "./session"

export const SESSION_EXPIRED_EVENT = "resume-web-session-expired"
export const DEFAULT_REQUEST_TIMEOUT_MS = 15_000
// AI 生成与文件导出类请求的真实上限，与后端 ai_client 的 120s httpx 超时对齐。
export const SLOW_REQUEST_TIMEOUT_MS = 120_000

type ApiEnvelope<T> = {
  code?: string
  data?: T
  detail?: string
  message?: string
}

export class ApiRequestError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly code = "",
  ) {
    super(message)
    this.name = "ApiRequestError"
  }
}

export type ApiRequestOptions = { timeoutMs?: number }

export class ApiTimeoutError extends ApiRequestError {
  constructor() {
    super("请求超时，请稍后重试", 0)
    this.name = "ApiTimeoutError"
  }
}

export function readItems<T>(payload: T[] | { items?: T[] } | null | undefined): T[] {
  if (Array.isArray(payload)) return payload
  if (payload && typeof payload === "object" && "items" in payload && Array.isArray(payload.items)) {
    return payload.items
  }
  throw new ApiRequestError(readMessage(undefined), 0)
}

function readMessage(body: ApiEnvelope<unknown> | null | undefined): string {
  return body?.detail || body?.message || "请求未完成，请稍后重试"
}

function isAbortError(reason: unknown): boolean {
  return typeof reason === "object" && reason !== null && "name" in reason && reason.name === "AbortError"
}

function notifySessionExpired(): void {
  if (typeof window !== "undefined") window.dispatchEvent(new Event(SESSION_EXPIRED_EVENT))
}

function createRequestSignal(callerSignal?: AbortSignal | null, timeoutMs = DEFAULT_REQUEST_TIMEOUT_MS): { signal: AbortSignal; didTimeout: () => boolean; cleanup: () => void } {
  const controller = new AbortController()
  let timedOut = false
  const timeoutId = setTimeout(() => {
    timedOut = true
    controller.abort()
  }, timeoutMs)
  const abortFromCaller = () => controller.abort(callerSignal?.reason)
  if (callerSignal) {
    if (callerSignal.aborted) abortFromCaller()
    else callerSignal.addEventListener("abort", abortFromCaller, { once: true })
  }
  return {
    signal: controller.signal,
    didTimeout: () => timedOut,
    cleanup: () => {
      clearTimeout(timeoutId)
      callerSignal?.removeEventListener("abort", abortFromCaller)
    },
  }
}

function rethrowRequestFailure(reason: unknown, request: ReturnType<typeof createRequestSignal>): never {
  if (request.didTimeout() && isAbortError(reason)) throw new ApiTimeoutError()
  if (isAbortError(reason)) throw reason
  throw new ApiRequestError(readMessage(undefined), 0)
}

export async function requestApi<T>(path: string, init: RequestInit = {}, options: ApiRequestOptions = {}): Promise<T> {
  const session = readSession()
  const headers = {
    "Content-Type": "application/json",
    ...(init.headers as Record<string, string> | undefined),
    ...(session ? { Authorization: `Bearer ${session.token}` } : {}),
  }
  const request = createRequestSignal(init.signal, options.timeoutMs)
  try {
    let response: Response
    try {
      response = await fetch(path, { ...init, headers, signal: request.signal })
    } catch (reason) {
      rethrowRequestFailure(reason, request)
    }

    if (response.status === 204) return undefined as T

    let body: ApiEnvelope<T>
    try {
      body = (await response.json()) as ApiEnvelope<T>
    } catch (reason) {
      if (request.didTimeout() && isAbortError(reason)) throw new ApiTimeoutError()
      if (isAbortError(reason)) throw reason
      throw new ApiRequestError(readMessage(undefined), response.status)
    }

    if (response.status === 401) {
      clearSession()
      notifySessionExpired()
    }
    if (!response.ok || body.code !== "ok") {
      throw new ApiRequestError(readMessage(body), response.status, body.code ?? "")
    }

    return body.data as T
  } finally {
    request.cleanup()
  }
}

export async function downloadApi(path: string, init: RequestInit = {}, options: ApiRequestOptions = {}): Promise<Blob> {
  const session = readSession()
  const headers = {
    ...(init.headers as Record<string, string> | undefined),
    ...(session ? { Authorization: `Bearer ${session.token}` } : {}),
  }
  const request = createRequestSignal(init.signal, options.timeoutMs)
  try {
    let response: Response
    try {
      response = await fetch(path, { ...init, headers, signal: request.signal })
    } catch (reason) {
      rethrowRequestFailure(reason, request)
    }

    if (response.status === 401) {
      clearSession()
      notifySessionExpired()
    }
    if (!response.ok) {
      let body: ApiEnvelope<unknown> | null = null
      try { body = (await response.json()) as ApiEnvelope<unknown> } catch (reason) {
        if (request.didTimeout() && isAbortError(reason)) throw new ApiTimeoutError()
        if (isAbortError(reason)) throw reason
      }
      throw new ApiRequestError(readMessage(body), response.status, body?.code ?? "")
    }

    try {
      return await response.blob()
    } catch (reason) {
      if (request.didTimeout() && isAbortError(reason)) throw new ApiTimeoutError()
      if (isAbortError(reason)) throw reason
      throw new ApiRequestError(readMessage(undefined), response.status)
    }
  } finally {
    request.cleanup()
  }
}
