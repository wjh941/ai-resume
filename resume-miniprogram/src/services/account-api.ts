import { request } from "./http"

export type AccountDataScope = {
  categories: string[]
  retentionNote: string
}

export type AccountPrivacyDetails = AccountDataScope & {
  privacyPolicyHint: string
}

export type AccountLifecycleAcknowledgement = {
  status: string
  message: string
}

export type AccountDataExport = AccountLifecycleAcknowledgement & {
  downloadUrl: string
}

type BackendAccountScope = { categories: string[]; retention_note: string; privacy_policy_hint?: string }

async function fetchAccountScope(): Promise<BackendAccountScope> {
  return request<BackendAccountScope>("/api/account/data-scope")
}

export async function requestAccountScope(): Promise<AccountDataScope> {
  const data = await fetchAccountScope()
  return { categories: data.categories, retentionNote: data.retention_note }
}

export async function requestAccountPrivacyDetails(): Promise<AccountPrivacyDetails> {
  const data = await fetchAccountScope()
  return {
    categories: data.categories,
    retentionNote: data.retention_note,
    privacyPolicyHint: data.privacy_policy_hint || "Review the privacy policy before exporting or deleting your account.",
  }
}

export function requestAccountDeletion(): Promise<AccountLifecycleAcknowledgement> {
  return request<AccountLifecycleAcknowledgement>("/api/account/deletion-request", "POST")
}

export async function requestAccountDataExport(): Promise<AccountDataExport> {
  const data = await request<{ status: string; message: string; download_url: string }>("/api/account/data-export", "POST")
  return { status: data.status, message: data.message, downloadUrl: data.download_url }
}

export function recordPrivacyConsent(): Promise<{ privacyConsentAt: string }> {
  return request<{ privacy_consent_at: string }>("/api/account/privacy-consent", "POST").then((data) => ({
    privacyConsentAt: data.privacy_consent_at,
  }))
}
