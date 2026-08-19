import { request } from "./http"

export type AccountDataScope = {
  categories: string[]
  retentionNote: string
}

export type AccountLifecycleAcknowledgement = {
  status: string
  message: string
}

export async function requestAccountScope(): Promise<AccountDataScope> {
  const data = await request<{ categories: string[]; retention_note: string }>("/api/account/data-scope")
  return { categories: data.categories, retentionNote: data.retention_note }
}

export function requestAccountDeletion(): Promise<AccountLifecycleAcknowledgement> {
  return request<AccountLifecycleAcknowledgement>("/api/account/deletion-request", "POST")
}

export function requestAccountDataExport(): Promise<AccountLifecycleAcknowledgement> {
  return request<AccountLifecycleAcknowledgement>("/api/account/data-export", "POST")
}
