import { clearSession, readSession } from "./session"

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

function readMessage(body: ApiEnvelope<unknown>): string {
  return body.detail || body.message || "请求未完成，请稍后重试"
}

export async function requestApi<T>(path: string, init: RequestInit = {}): Promise<T> {
  const session = readSession()
  const headers = {
    "Content-Type": "application/json",
    ...(init.headers as Record<string, string> | undefined),
    ...(session ? { Authorization: `Bearer ${session.token}` } : {}),
  }
  const response = await fetch(path, { ...init, headers })
  const body = (await response.json()) as ApiEnvelope<T>

  if (response.status === 401) clearSession()
  if (!response.ok || body.code !== "ok") {
    throw new ApiRequestError(readMessage(body), response.status)
  }

  return body.data as T
}
