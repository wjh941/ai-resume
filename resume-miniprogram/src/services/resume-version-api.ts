import { request } from "./http"

export type ResumeVersion = {
  id: string
  note: string
  isActive: boolean
  createdAt: string
}

type BackendResumeVersion = {
  id: string
  note: string
  is_active: boolean
  created_at: string
}

const fromBackend = (item: BackendResumeVersion): ResumeVersion => ({
  id: item.id,
  note: item.note,
  isActive: item.is_active,
  createdAt: item.created_at,
})

export async function listResumeVersions(draftId: string): Promise<ResumeVersion[]> {
  const data = await request<{ items: BackendResumeVersion[] }>(
    `/api/draft/${encodeURIComponent(draftId)}/versions`,
  )
  return data.items.map(fromBackend)
}

export async function createResumeVersion(draftId: string, note: string): Promise<ResumeVersion> {
  return fromBackend(await request<BackendResumeVersion>(
    `/api/draft/${encodeURIComponent(draftId)}/versions`, "POST", { note },
  ))
}

export async function restoreResumeVersion(draftId: string, versionId: string): Promise<void> {
  await request(
    `/api/draft/${encodeURIComponent(draftId)}/versions/${encodeURIComponent(versionId)}/restore`,
    "POST",
  )
}

export async function compareResumeVersions(
  draftId: string,
  leftId: string,
  rightId: string,
): Promise<string[]> {
  const params = new URLSearchParams({ left_id: leftId, right_id: rightId })
  const data = await request<{ changed_fields: string[] }>(
    `/api/draft/${encodeURIComponent(draftId)}/versions/compare?${params}`,
  )
  return data.changed_fields
}
