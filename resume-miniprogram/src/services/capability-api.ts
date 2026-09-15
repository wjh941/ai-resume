import { request } from "./http"

export type CapabilityMode = "real" | "demo" | "disabled"

export interface Capability {
  enabled: boolean
  mode: CapabilityMode
  notice: string
}

export interface Capabilities {
  resumeImport: Capability
  smsLogin: Capability
  wechatOauth: Capability
  payment: Capability
  pushNotifications: Capability
  jobMatching: Capability
}

type BackendCapability = { enabled?: unknown; mode?: unknown; notice?: unknown }
export type CapabilityName = keyof Capabilities

const names: Array<[CapabilityName, string]> = [
  ["resumeImport", "resume_import"],
  ["smsLogin", "sms_login"],
  ["wechatOauth", "wechat_oauth"],
  ["payment", "payment"],
  ["pushNotifications", "push_notifications"],
  ["jobMatching", "job_matching"],
]

const disabled = (notice = "当前功能暂不可用。"): Capability => ({
  enabled: false,
  mode: "disabled",
  notice,
})

export const defaultCapabilities = (): Capabilities => ({
  resumeImport: disabled("简历导入暂不可用。"),
  smsLogin: disabled("短信登录暂不可用。"),
  wechatOauth: disabled("微信登录暂不可用。"),
  payment: disabled("支付服务暂不可用。"),
  pushNotifications: disabled("推送通知暂不可用。"),
  jobMatching: disabled("岗位匹配暂不可用。"),
})

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value)
}

function mapCapability(value: unknown, fallback: Capability): Capability {
  if (
    !isRecord(value) ||
    typeof value.enabled !== "boolean" ||
    typeof value.notice !== "string" ||
    !value.notice.trim() ||
    typeof value.mode !== "string" ||
    !["real", "demo", "disabled"].includes(value.mode)
  ) return fallback
  return {
    enabled: value.enabled === true && value.mode !== "disabled",
    mode: value.mode as CapabilityMode,
    notice: value.notice,
  }
}

export function mapCapabilities(payload: unknown): Capabilities {
  const fallback = defaultCapabilities()
  if (!isRecord(payload) || !isRecord(payload.features)) return fallback
  const features = payload.features
  const mapped = { ...fallback }
  names.forEach(([key, backendKey]) => {
    mapped[key] = mapCapability(features[backendKey], fallback[key])
  })
  return mapped
}

export async function getCapabilities(): Promise<Capabilities> {
  try {
    return mapCapabilities(await request<unknown>("/health"))
  } catch {
    return defaultCapabilities()
  }
}

export function isCapabilityEnabled(capabilities: Capabilities, name: CapabilityName): boolean {
  return capabilities[name].enabled
}
