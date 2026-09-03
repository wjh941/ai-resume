import { clearSession, readSession } from "./session"

export const SESSION_EXPIRED_EVENT = "resume-web-session-expired"
export const DEFAULT_REQUEST_TIMEOUT_MS = 15_000

type ApiEnvelope<T> = {
  code?: string
  data?: T
  detail?: string
  message?: string
}

export class ApiRequestError extends Error {
  constructor(message: string, readonly status: number) {
    super(message)
    this.name = "ApiRequestError"
  }
}

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

function createRequestSignal(callerSignal?: AbortSignal | null): { signal: AbortSignal; didTimeout: () => boolean; cleanup: () => void } {
  const controller = new AbortController()
  let timedOut = false
  const timeoutId = setTimeout(() => {
    timedOut = true
    controller.abort()
  }, DEFAULT_REQUEST_TIMEOUT_MS)
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

export async function requestApi<T>(path: string, init: RequestInit = {}): Promise<T> {
  const session = readSession()
  const headers = {
    "Content-Type": "application/json",
    ...(init.headers as Record<string, string> | undefined),
    ...(session ? { Authorization: `Bearer ${session.token}` } : {}),
  }
  const request = createRequestSignal(init.signal)
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
      throw new ApiRequestError(readMessage(body), response.status)
    }

    return body.data as T
  } finally {
    request.cleanup()
  }
}

export async function downloadApi(path: string, init: RequestInit = {}): Promise<Blob> {
  const session = readSession()
  const headers = {
    ...(init.headers as Record<string, string> | undefined),
    ...(session ? { Authorization: `Bearer ${session.token}` } : {}),
  }
  const request = createRequestSignal(init.signal)
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
      throw new ApiRequestError(readMessage(body), response.status)
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
