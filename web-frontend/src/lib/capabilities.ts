import { requestApi } from "./api"

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

export type CapabilityName = keyof Capabilities

const names: Array<[CapabilityName, string, string]> = [
  ["resumeImport", "resume_import", "简历导入暂不可用。"],
  ["smsLogin", "sms_login", "短信登录暂不可用。"],
  ["wechatOauth", "wechat_oauth", "微信登录暂不可用。"],
  ["payment", "payment", "支付服务暂不可用。"],
  ["pushNotifications", "push_notifications", "推送通知暂不可用。"],
  ["jobMatching", "job_matching", "岗位匹配暂不可用。"],
]

function disabled(notice: string): Capability {
  return { enabled: false, mode: "disabled", notice }
}

export function defaultCapabilities(): Capabilities {
  return Object.fromEntries(names.map(([name, , notice]) => [name, disabled(notice)])) as Capabilities
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value)
}

function mapCapability(value: unknown, fallback: Capability): Capability {
  if (!isRecord(value)) return fallback
  const { enabled, mode, notice } = value
  if (
    typeof enabled !== "boolean" ||
    (mode !== "real" && mode !== "demo" && mode !== "disabled") ||
    typeof notice !== "string" ||
    !notice.trim()
  ) return fallback
  return { enabled, mode, notice }
}

export function mapCapabilities(payload: unknown): Capabilities {
  const fallback = defaultCapabilities()
  if (!isRecord(payload) || !isRecord(payload.features)) return fallback

  const mapped = { ...fallback }
  for (const [name, backendName] of names) {
    mapped[name] = mapCapability(payload.features[backendName], fallback[name])
  }
  return mapped
}

export async function getCapabilities(): Promise<Capabilities> {
  try {
    return mapCapabilities(await requestApi<unknown>("/health"))
  } catch {
    return defaultCapabilities()
  }
}

export function isCapabilityEnabled(capabilities: Capabilities, name: CapabilityName): boolean {
  const capability = capabilities[name]
  return capability.enabled === true && capability.mode !== "disabled"
}
