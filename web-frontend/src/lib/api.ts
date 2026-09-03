import { clearSession, readSession } from "./session"

export const SESSION_EXPIRED_EVENT = "resume-web-session-expired"

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

export async function requestApi<T>(path: string, init: RequestInit = {}): Promise<T> {
  const session = readSession()
  const headers = {
    "Content-Type": "application/json",
    ...(init.headers as Record<string, string> | undefined),
    ...(session ? { Authorization: `Bearer ${session.token}` } : {}),
  }
  let response: Response
  try {
    response = await fetch(path, { ...init, headers })
  } catch (reason) {
    if (isAbortError(reason)) throw reason
    throw new ApiRequestError(readMessage(undefined), 0)
  }

  if (response.status === 204) return undefined as T

  let body: ApiEnvelope<T>
  try {
    body = (await response.json()) as ApiEnvelope<T>
  } catch {
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
}

export async function downloadApi(path: string, init: RequestInit = {}): Promise<Blob> {
  const session = readSession()
  const headers = {
    ...(init.headers as Record<string, string> | undefined),
    ...(session ? { Authorization: `Bearer ${session.token}` } : {}),
  }
  let response: Response
  try {
    response = await fetch(path, { ...init, headers })
  } catch (reason) {
    if (isAbortError(reason)) throw reason
    throw new ApiRequestError(readMessage(undefined), 0)
  }

  if (response.status === 401) {
    clearSession()
    notifySessionExpired()
  }
  if (!response.ok) {
    let body: ApiEnvelope<unknown> | null = null
    try { body = (await response.json()) as ApiEnvelope<unknown> } catch { /* binary endpoint may return no JSON */ }
    throw new ApiRequestError(readMessage(body), response.status)
  }

  return response.blob()
}
