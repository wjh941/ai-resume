import type { ApiEnvelope } from "../types/api"

const API_BASE_URL =
  process.env.UNI_PLATFORM === "h5" ? "" : "http://127.0.0.1:8000"

type UniRequest = (options: Record<string, unknown>) => Promise<{ data: ApiEnvelope<unknown> }>

export async function request<T>(path: string, method = "GET", data?: unknown): Promise<T> {
  const requestFn = (globalThis as typeof globalThis & { uni?: { request?: UniRequest } }).uni?.request
  if (!requestFn) throw new Error("当前运行环境不支持网络请求")
  const response = await requestFn({ url: `${API_BASE_URL}${path}`, method, data })
  if (response.data.code !== "ok") throw new Error(response.data.message || "请求失败")
  return response.data.data as T
}
