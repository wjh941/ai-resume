import type { ApiEnvelope } from "../types/api"

const API_BASE_URL =
  process.env.UNI_PLATFORM === "h5" ? "" : "http://127.0.0.1:8000"

type UniRequest = (options: Record<string, unknown>) => Promise<{ statusCode?: number; data: ApiEnvelope<unknown> | unknown }>

export function apiUrl(path: string): string {
  return `${API_BASE_URL}${path}`
}

export async function request<T>(path: string, method = "GET", data?: unknown): Promise<T> {
  const requestFn = (globalThis as typeof globalThis & { uni?: { request?: UniRequest } }).uni?.request
  if (!requestFn) throw new Error("当前运行环境不支持网络请求")
  const response = await requestFn({ url: apiUrl(path), method, data })
  const envelope = response.data as Partial<ApiEnvelope<T>>
  if (response.statusCode && response.statusCode >= 400) {
    throw new Error(envelope.message || `请求失败（${response.statusCode}）`)
  }
  if (envelope.code !== "ok") throw new Error(envelope.message || "请求失败")
  return envelope.data as T
}
