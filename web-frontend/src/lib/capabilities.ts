import { requestApi } from "./api"
import { readonly, ref } from "vue"
import type { InjectionKey, Ref } from "vue"

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

export interface CapabilityContext {
  capabilities: Readonly<Ref<Capabilities>>
  refreshing: Readonly<Ref<boolean>>
  refresh: () => Promise<Capabilities>
}

export type CapabilityName = keyof Capabilities

export const CAPABILITIES_KEY: InjectionKey<Readonly<Ref<Capabilities>>> = Symbol("capabilities")

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

export async function getCapabilities(fallback = defaultCapabilities()): Promise<Capabilities> {
  try {
    return mapCapabilities(await requestApi<unknown>("/health"))
  } catch {
    return fallback
  }
}

export function createCapabilityContext(): CapabilityContext {
  const capabilities = ref(defaultCapabilities())
  const refreshing = ref(false)
  let inFlight: Promise<Capabilities> | null = null

  function refresh(): Promise<Capabilities> {
    if (inFlight) return inFlight

    refreshing.value = true
    inFlight = getCapabilities(capabilities.value)
      .then((value) => {
        capabilities.value = value
        return value
      })
      .finally(() => {
        refreshing.value = false
        inFlight = null
      })
    return inFlight
  }

  return {
    capabilities: readonly(capabilities),
    refreshing: readonly(refreshing),
    refresh,
  }
}

export function isCapabilityEnabled(capabilities: Capabilities, name: CapabilityName): boolean {
  const capability = capabilities[name]
  return capability.enabled === true && capability.mode !== "disabled"
}
